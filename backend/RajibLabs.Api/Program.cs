using System;
using System.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Text;
using System.Security.Claims;
using System.IdentityModel.Tokens.Jwt;
using Microsoft.IdentityModel.Tokens;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Configuration;
using Microsoft.EntityFrameworkCore;
using RajibLabs.Api.Data;
using RajibLabs.Api.Models;

var builder = WebApplication.CreateBuilder(args);

// ── Database ──
builder.Services.AddDbContext<LabDbContext>(options =>
    options.UseSqlite("Data Source=rajiblabs.db"));

// ── Auth ──
var jwtKey = builder.Configuration["Jwt:Key"] ?? builder.Configuration["JWT_KEY"] ?? "rajiblabs-dev-jwt-key-change-me-32-chars-min!!";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "RajibLabs";
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o =>
    {
        o.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true, ValidIssuer = jwtIssuer,
            ValidateAudience = false,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidateLifetime = true, ClockSkew = TimeSpan.FromMinutes(1)
        };
        o.Events = new JwtBearerEvents
        {
            OnMessageReceived = ctx =>
            {
                if (ctx.Request.Cookies.TryGetValue("rlabs_token", out var c)) ctx.Token = c;
                var auth = ctx.Request.Headers.Authorization.ToString();
                if (!string.IsNullOrEmpty(auth) && auth.StartsWith("Bearer ")) ctx.Token = auth.Substring(7);
                return Task.CompletedTask;
            }
        };
    });
builder.Services.AddAuthorization();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://localhost:5174", "https://rajiblabs.com")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    options.SerializerOptions.PropertyNameCaseInsensitive = true;
});

var app = builder.Build();

// ── Ensure DB & seed ──
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<LabDbContext>();
    // EnsureCreated for new installs; for existing DB, ensure new tables exist
    db.Database.EnsureCreated();
    try { db.AdminUsers.Take(1).ToList(); } catch { db.Database.EnsureCreated(); }
    // Create missing tables via raw SQL if EnsureCreated didn't add them (SQLite)
    var ensureSql = new[]
    {
        @"CREATE TABLE IF NOT EXISTS AdminUsers (Id TEXT PRIMARY KEY, Username TEXT NOT NULL, PasswordHash TEXT NOT NULL, CreatedAt TEXT NOT NULL, LastLoginAt TEXT)",
        "CREATE UNIQUE INDEX IF NOT EXISTS IX_AdminUsers_Username ON AdminUsers(Username)",
        @"CREATE TABLE IF NOT EXISTS Resumes (Id TEXT PRIMARY KEY, FileName TEXT, StoredPath TEXT, ContentType TEXT, SizeBytes INTEGER NOT NULL, Version INTEGER NOT NULL, Status TEXT, UploadedAt TEXT NOT NULL, PublishedAt TEXT)",
        @"CREATE TABLE IF NOT EXISTS ResumeExtractions (Id TEXT PRIMARY KEY, ResumeId TEXT NOT NULL, ExtractedJson TEXT, Status TEXT, CreatedAt TEXT NOT NULL)",
        @"CREATE TABLE IF NOT EXISTS PortfolioProjects (Id TEXT PRIMARY KEY, Title TEXT NOT NULL, Slug TEXT, ShortDescription TEXT, Description TEXT, Problem TEXT, Solution TEXT, Role TEXT, Architecture TEXT, TechStackJson TEXT, AiCapabilitiesJson TEXT, CloudCapabilitiesJson TEXT, ScreenshotsJson TEXT, DemoUrl TEXT, GitHubUrl TEXT, ProductUrl TEXT, Status TEXT, Featured INTEGER NOT NULL, DisplayOrder INTEGER NOT NULL, CreatedAt TEXT NOT NULL, UpdatedAt TEXT NOT NULL, PublishedAt TEXT, IsManualEdit INTEGER NOT NULL)",
        "CREATE UNIQUE INDEX IF NOT EXISTS IX_PortfolioProjects_Slug ON PortfolioProjects(Slug)",
        @"CREATE TABLE IF NOT EXISTS GitHubRepositories (Id TEXT PRIMARY KEY, GitHubId INTEGER NOT NULL, Name TEXT, FullName TEXT, Description TEXT, HtmlUrl TEXT, Language TEXT, TopicsJson TEXT, Stars INTEGER NOT NULL, Forks INTEGER NOT NULL, Readme TEXT, PushedAt TEXT, UpdatedAtGitHub TEXT, IsPrivate INTEGER NOT NULL, DefaultBranch TEXT, Classification TEXT, AiTitle TEXT, AiSummary TEXT, AiProblem TEXT, AiTechStack TEXT, AiConfidence TEXT, SyncStatus TEXT, LastSyncedAt TEXT NOT NULL, IsManuallyEdited INTEGER NOT NULL, PublishedAt TEXT)",
        "CREATE UNIQUE INDEX IF NOT EXISTS IX_GitHubRepositories_GitHubId ON GitHubRepositories(GitHubId)",
        @"CREATE TABLE IF NOT EXISTS Products (Id TEXT PRIMARY KEY, Name TEXT NOT NULL, Slug TEXT, Category TEXT, Description TEXT, LogoUrl TEXT, ScreenshotsJson TEXT, FeaturesJson TEXT, TechStackJson TEXT, AiCapabilities TEXT, Architecture TEXT, ProductUrl TEXT, GitHubRepoId TEXT, Status TEXT, Featured INTEGER NOT NULL, DisplayOrder INTEGER NOT NULL, CreatedAt TEXT NOT NULL, UpdatedAt TEXT NOT NULL)",
        "CREATE UNIQUE INDEX IF NOT EXISTS IX_Products_Slug ON Products(Slug)",
        @"CREATE TABLE IF NOT EXISTS ProjectSyncLogs (Id TEXT PRIMARY KEY, StartedAt TEXT NOT NULL, FinishedAt TEXT, Found INTEGER NOT NULL, Added INTEGER NOT NULL, Updated INTEGER NOT NULL, Ignored INTEGER NOT NULL, ErrorsJson TEXT)",
        @"CREATE TABLE IF NOT EXISTS WebsiteContents (Id TEXT PRIMARY KEY, Key TEXT NOT NULL, Title TEXT, BodyJson TEXT, UpdatedAt TEXT NOT NULL)",
        "CREATE UNIQUE INDEX IF NOT EXISTS IX_WebsiteContents_Key ON WebsiteContents(Key)"
    };
    foreach (var sql in ensureSql) try { db.Database.ExecuteSqlRaw(sql); } catch { }
    // Add extended Profile columns if missing
    var profileCols = new[] { "Headline", "Location", "Phone", "WhatsApp", "Email", "LinkedIn", "GitHub", "Website", "ProfileImageUrl" };
    foreach (var col in profileCols) try { db.Database.ExecuteSqlRaw($"ALTER TABLE Profiles ADD COLUMN {col} TEXT"); } catch { }

    if (!db.Projects.Any()) SeedData(db);
    SeedCms(db, builder.Configuration);
}

app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.UseDefaultFiles();
app.UseStaticFiles();

string HashPassword(string p) => BCrypt.Net.BCrypt.HashPassword(p);
bool VerifyPassword(string p, string h) => BCrypt.Net.BCrypt.Verify(p, h);
string CreateJwt(string username)
{
    var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey));
    var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
    var token = new JwtSecurityToken(issuer: jwtIssuer, audience: jwtIssuer,
        claims: new[] { new Claim(ClaimTypes.Name, username), new Claim(ClaimTypes.Role, "Admin") },
        expires: DateTime.UtcNow.AddDays(7), signingCredentials: creds);
    return new JwtSecurityTokenHandler().WriteToken(token);
}
bool IsAdmin(HttpContext ctx) => ctx.User?.Identity?.IsAuthenticated == true;

// ── Existing public APIs ──
app.MapGet("/api/projects", async (LabDbContext db) =>
{
    var projects = await db.Projects.OrderByDescending(p => p.UpdatedAt).ToListAsync();
    return Results.Ok(projects.Select(p => new { p.Id, p.Title, p.Slug, p.Description, techStack = p.TechStack, p.GitHubUrl, p.LiveUrl, p.Status, p.CreatedAt, p.UpdatedAt, p.LastCommitAt }));
});
app.MapGet("/api/projects/{id:guid}", async (Guid id, LabDbContext db) =>
{
    var p = await db.Projects.FindAsync(id);
    return p is not null ? Results.Ok(new { p.Id, p.Title, p.Slug, p.Description, techStack = p.TechStack, p.GitHubUrl, p.LiveUrl, p.Status, p.CreatedAt, p.UpdatedAt, p.LastCommitAt }) : Results.NotFound();
});
app.MapGet("/api/activity", async (int? limit, LabDbContext db) =>
{
    var q = db.Activities.OrderByDescending(a => a.Timestamp);
    var r = limit.HasValue ? q.Take(limit.Value) : q;
    return Results.Ok(await r.ToListAsync());
});
app.MapGet("/api/profile", async (LabDbContext db) =>
{
    var p = await db.Profiles.FirstOrDefaultAsync();
    if (p is null) return Results.NotFound();
    return Results.Ok(new { p.Id, p.FullName, p.Title, p.Bio, skills = p.Skills, socialLinks = p.SocialLinks, career = p.Career, p.Headline, p.Location, p.Phone, p.WhatsApp, p.Email, p.LinkedIn, p.GitHub, p.Website, p.ProfileImageUrl, p.UpdatedAt });
});
static async ValueTask<object?> RequireApiKey(EndpointFilterInvocationContext context, EndpointFilterDelegate next)
{
    var config = context.HttpContext.RequestServices.GetRequiredService<IConfiguration>();
    var expectedKey = config["ApiKey"];
    if (string.IsNullOrWhiteSpace(expectedKey)) return await next(context);
    if (!context.HttpContext.Request.Headers.TryGetValue("X-Api-Key", out var providedKey) || !string.Equals(providedKey, expectedKey, StringComparison.Ordinal))
        return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    return await next(context);
}
app.MapPost("/api/contact", async (ContactDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Name) || string.IsNullOrWhiteSpace(dto.Email) || string.IsNullOrWhiteSpace(dto.Message))
        return Results.BadRequest(new { Error = "Name, email, and message are required" });
    var c = new Contact { Id = Guid.NewGuid(), Name = dto.Name.Trim(), Email = dto.Email.Trim(), Company = dto.Company?.Trim(), Message = dto.Message.Trim(), SubmittedAt = DateTime.UtcNow };
    db.Contacts.Add(c); await db.SaveChangesAsync();
    return Results.Created($"/api/contact/{c.Id}", new { c.Id, Message = "Message received. Thank you!" });
});
app.MapPost("/api/activity", async (ActivityDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title)) return Results.BadRequest(new { Error = "Title is required" });
    var a = new Activity { Id = Guid.NewGuid(), ProjectId = dto.ProjectId, Type = dto.Type ?? "commit", Title = dto.Title, Description = dto.Description ?? string.Empty, Timestamp = dto.Timestamp ?? DateTime.UtcNow };
    db.Activities.Add(a); await db.SaveChangesAsync();
    var project = await db.Projects.FindAsync(dto.ProjectId);
    if (project is not null) { project.UpdatedAt = DateTime.UtcNow; if (dto.Type == "commit" && dto.CommittedAt.HasValue) { if (project.LastCommitAt is null || dto.CommittedAt.Value > project.LastCommitAt) project.LastCommitAt = dto.CommittedAt.Value; } else if (dto.Type == "commit") project.LastCommitAt = DateTime.UtcNow; await db.SaveChangesAsync(); }
    return Results.Created($"/api/activity/{a.Id}", new { a.Id, a.ProjectId, a.Type, a.Title, a.Description, a.Timestamp });
}).AddEndpointFilter(RequireApiKey);
app.MapMethods("/api/projects/{id:guid}", new[] { "PATCH" }, async (Guid id, ProjectPatchDto dto, LabDbContext db) =>
{
    var p = await db.Projects.FindAsync(id); if (p is null) return Results.NotFound();
    if (dto.LastCommitAt.HasValue) p.LastCommitAt = dto.LastCommitAt.Value; if (dto.Status is not null) p.Status = dto.Status; if (dto.Title is not null) p.Title = dto.Title; if (dto.Description is not null) p.Description = dto.Description;
    p.UpdatedAt = DateTime.UtcNow; await db.SaveChangesAsync();
    return Results.Ok(new { p.Id, p.Title, p.Slug, p.Description, techStack = p.TechStack, p.GitHubUrl, p.LiveUrl, p.Status, p.CreatedAt, p.UpdatedAt, p.LastCommitAt });
}).AddEndpointFilter(RequireApiKey);
app.MapGet("/api/health", () => Results.Ok(new { Status = "healthy", Timestamp = DateTime.UtcNow }));
app.MapGet("/api/learning", async (LabDbContext db) =>
{
    var courses = await db.LinkedInCourses.OrderByDescending(c => c.Status == "in-progress" ? 1 : 0).ThenByDescending(c => c.UpdatedAt).ToListAsync();
    return Results.Ok(courses.Select(c => new { c.Id, c.Title, c.Url, c.Instructor, c.Duration, c.Level, c.CompletedAt, c.Status, c.UpdatedAt }));
});
app.MapPost("/api/learning", async (LinkedInCourseDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title)) return Results.BadRequest(new { Error = "Title is required" });
    var e = await db.LinkedInCourses.FirstOrDefaultAsync(c => c.Url == dto.Url);
    if (e != null) { e.Title = dto.Title; e.Instructor = dto.Instructor; e.Duration = dto.Duration; e.Level = dto.Level; e.CompletedAt = dto.CompletedAt; e.Status = dto.Status ?? e.Status; e.UpdatedAt = DateTime.UtcNow; }
    else { var c = new LinkedInCourse { Id = Guid.NewGuid(), Title = dto.Title.Trim(), Url = dto.Url.Trim(), Instructor = dto.Instructor?.Trim(), Duration = dto.Duration, Level = dto.Level, CompletedAt = dto.CompletedAt, Status = dto.Status ?? "in-progress", UpdatedAt = DateTime.UtcNow }; db.LinkedInCourses.Add(c); }
    await db.SaveChangesAsync(); return Results.Ok(new { Message = "Course synced" });
});
app.MapPost("/api/subscribe", async (SubscriberDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Email) || !dto.Email.Contains('@')) return Results.BadRequest(new { Error = "Valid email is required" });
    var email = dto.Email.Trim().ToLower(); var e = await db.Subscribers.FirstOrDefaultAsync(s => s.Email == email);
    if (e != null) { if (!e.IsActive) { e.IsActive = true; e.SubscribedAt = DateTime.UtcNow; e.UnsubscribedAt = null; await db.SaveChangesAsync(); return Results.Ok(new { Message = "Welcome back! You're re-subscribed." }); } return Results.Ok(new { Message = "You're already subscribed!" }); }
    var sub = new Subscriber { Id = Guid.NewGuid(), Email = email, IsActive = true, SubscribedAt = DateTime.UtcNow }; db.Subscribers.Add(sub); await db.SaveChangesAsync(); return Results.Created("/api/subscribe", new { Message = "Subscribed! Thank you." });
});
app.MapPost("/api/unsubscribe", async (SubscriberDto dto, LabDbContext db) =>
{
    var sub = await db.Subscribers.FirstOrDefaultAsync(s => s.Email == dto.Email.Trim().ToLower() && s.IsActive); if (sub is null) return Results.NotFound(new { Error = "Email not found" });
    sub.IsActive = false; sub.UnsubscribedAt = DateTime.UtcNow; await db.SaveChangesAsync(); return Results.Ok(new { Message = "Unsubscribed. We'll miss you!" });
});

// ── Admin Auth ──
app.MapPost("/api/admin/login", async (AdminLoginDto dto, HttpContext http, LabDbContext db, IConfiguration cfg) =>
{
    // Rate limit: 5 attempts per minute per IP (simple in-memory)
    var username = (cfg["Admin:Username"] ?? cfg["ADMIN_USERNAME"] ?? "admin").Trim();
    var passwordHash = cfg["Admin:PasswordHash"] ?? cfg["ADMIN_PASSWORD_HASH"] ?? "";
    var admin = await db.AdminUsers.FirstOrDefaultAsync(u => u.Username == dto.Username);
    // Fallback to env-configured admin if DB empty
    if (admin is null && dto.Username == username)
    {
        // If env hash provided, verify against it; else allow default password "Admin@123" hashed on first use
        if (!string.IsNullOrWhiteSpace(passwordHash))
        {
            if (!VerifyPassword(dto.Password, passwordHash)) return Results.Json(new { Error = "Invalid credentials" }, statusCode: 401);
        }
        else
        {
            var defaultPass = cfg["Admin:Password"] ?? cfg["ADMIN_PASSWORD"] ?? "Admin@123";
            if (dto.Password != defaultPass) return Results.Json(new { Error = "Invalid credentials" }, statusCode: 401);
        }
        // Create DB user
        admin = new AdminUser { Username = username, PasswordHash = string.IsNullOrWhiteSpace(passwordHash) ? HashPassword(dto.Password) : passwordHash };
        db.AdminUsers.Add(admin);
    }
    if (admin is null) return Results.Json(new { Error = "Invalid credentials" }, statusCode: 401);
    if (!VerifyPassword(dto.Password, admin.PasswordHash))
    {
        // Also check env hash fallback
        if (string.IsNullOrWhiteSpace(passwordHash) || !VerifyPassword(dto.Password, passwordHash))
            return Results.Json(new { Error = "Invalid credentials" }, statusCode: 401);
    }
    admin.LastLoginAt = DateTime.UtcNow; await db.SaveChangesAsync();
    var token = CreateJwt(admin.Username);
    http.Response.Cookies.Append("rlabs_token", token, new CookieOptions { HttpOnly = true, Secure = true, SameSite = SameSiteMode.Strict, Expires = DateTimeOffset.UtcNow.AddDays(7), Path = "/" });
    return Results.Ok(new { Token = token, Username = admin.Username });
});
app.MapPost("/api/admin/logout", (HttpContext http) =>
{
    http.Response.Cookies.Delete("rlabs_token");
    return Results.Ok(new { Message = "Logged out" });
});
app.MapGet("/api/admin/me", (HttpContext http) =>
{
    if (!IsAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    return Results.Ok(new { Username = http.User.Identity?.Name, Role = "Admin" });
}).RequireAuthorization();

// ── Protected CMS helpers ──
bool RequireAdmin(HttpContext http) => IsAdmin(http);

// ── Resume ──
app.MapGet("/api/admin/resumes", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var list = await db.Resumes.OrderByDescending(r => r.Version).ToListAsync();
    return Results.Ok(list);
}).RequireAuthorization();
app.MapPost("/api/admin/resumes/upload", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var form = await http.Request.ReadFormAsync();
    var file = form.Files.FirstOrDefault();
    if (file is null) return Results.BadRequest(new { Error = "No file" });
    var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
    if (ext != ".pdf" && ext != ".docx") return Results.BadRequest(new { Error = "Only PDF/DOCX allowed" });
    if (file.Length > 10 * 1024 * 1024) return Results.BadRequest(new { Error = "Max 10MB" });
    var safeName = Guid.NewGuid().ToString("N") + ext;
    var dir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads", "resumes");
    Directory.CreateDirectory(dir);
    var stored = Path.Combine(dir, safeName);
    using (var fs = new FileStream(stored, FileMode.Create)) await file.CopyToAsync(fs);
    var version = (await db.Resumes.MaxAsync(r => (int?)r.Version) ?? 0) + 1;
    var resume = new Resume { FileName = file.FileName, StoredPath = $"uploads/resumes/{safeName}", ContentType = file.ContentType, SizeBytes = file.Length, Version = version, Status = "published", UploadedAt = DateTime.UtcNow, PublishedAt = DateTime.UtcNow };
    db.Resumes.Add(resume); await db.SaveChangesAsync();
    return Results.Ok(resume);
}).RequireAuthorization().DisableAntiforgery();
app.MapGet("/api/admin/resumes/{id:guid}/download", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var r = await db.Resumes.FindAsync(id); if (r is null) return Results.NotFound();
    var path = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", r.StoredPath);
    if (!System.IO.File.Exists(path)) return Results.NotFound();
    return Results.File(path, r.ContentType, r.FileName);
}).RequireAuthorization();
app.MapPatch("/api/admin/resumes/{id:guid}", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var r = await db.Resumes.FindAsync(id); if (r is null) return Results.NotFound();
    // toggle publish: archive others
    foreach (var other in await db.Resumes.Where(x => x.Id != id && x.Status == "published").ToListAsync()) other.Status = "archived";
    r.Status = "published"; r.PublishedAt = DateTime.UtcNow; await db.SaveChangesAsync();
    return Results.Ok(r);
}).RequireAuthorization();
app.MapDelete("/api/admin/resumes/{id:guid}", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var r = await db.Resumes.FindAsync(id); if (r is null) return Results.NotFound();
    db.Resumes.Remove(r); await db.SaveChangesAsync();
    try { System.IO.File.Delete(Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", r.StoredPath)); } catch { }
    return Results.Ok(new { Message = "Deleted" });
}).RequireAuthorization();
app.MapGet("/api/resume/current", async (LabDbContext db) =>
{
    var r = await db.Resumes.Where(x => x.Status == "published").OrderByDescending(x => x.Version).FirstOrDefaultAsync();
    if (r is null) return Results.NotFound();
    return Results.Ok(new { r.Id, r.FileName, r.Version, r.UploadedAt, r.PublishedAt, Url = $"/{r.StoredPath}" });
});
app.MapGet("/api/admin/resumes/{id:guid}/extraction", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var e = await db.ResumeExtractions.Where(x => x.ResumeId == id).OrderByDescending(x => x.CreatedAt).FirstOrDefaultAsync();
    return e is not null ? Results.Ok(e) : Results.NotFound();
}).RequireAuthorization();
app.MapPost("/api/admin/resumes/{id:guid}/extract", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var r = await db.Resumes.FindAsync(id); if (r is null) return Results.NotFound();
    // Heuristic extraction placeholder (AI can be plugged via OPENAI_API_KEY)
    var extracted = new { Name = "Rajib Mahata", Title = "Senior .NET & Azure Engineer", Summary = "12+ years SaaS & AI", Skills = new[] { ".NET", "Azure", "AI" } };
    var json = System.Text.Json.JsonSerializer.Serialize(extracted);
    var ex = new ResumeExtraction { ResumeId = id, ExtractedJson = json, Status = "review" };
    db.ResumeExtractions.Add(ex); await db.SaveChangesAsync();
    return Results.Ok(ex);
}).RequireAuthorization();
app.MapPost("/api/admin/resumes/extraction/{id:guid}/decision", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var ex = await db.ResumeExtractions.FindAsync(id); if (ex is null) return Results.NotFound();
    var body = await System.Text.Json.JsonSerializer.DeserializeAsync<Dictionary<string, string>>(http.Request.Body);
    if (body is null || !body.TryGetValue("decision", out var dec)) return Results.BadRequest(new { Error = "decision required" });
    ex.Status = dec; await db.SaveChangesAsync();
    return Results.Ok(ex);
}).RequireAuthorization();

// ── Portfolio ──
app.MapGet("/api/portfolio", async (string? status, LabDbContext db) =>
{
    var q = db.PortfolioProjects.AsQueryable();
    if (!string.IsNullOrWhiteSpace(status)) q = q.Where(p => p.Status == status);
    else q = q.Where(p => p.Status == "published");
    var list = await q.OrderBy(p => p.DisplayOrder).ThenByDescending(p => p.PublishedAt).ToListAsync();
    return Results.Ok(list.Select(p => new { p.Id, p.Title, p.Slug, p.ShortDescription, p.Description, p.Problem, p.Solution, p.Role, p.Architecture, techStack = p.TechStack, aiCapabilities = p.AiCapabilities, cloudCapabilities = p.CloudCapabilities, screenshots = p.Screenshots, p.DemoUrl, p.GitHubUrl, p.ProductUrl, p.Status, p.Featured, p.DisplayOrder, p.CreatedAt, p.PublishedAt }));
});
app.MapGet("/api/portfolio/{slug}", async (string slug, LabDbContext db) =>
{
    var p = await db.PortfolioProjects.FirstOrDefaultAsync(x => x.Slug == slug);
    return p is not null ? Results.Ok(p) : Results.NotFound();
});
app.MapGet("/api/admin/portfolio", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var list = await db.PortfolioProjects.OrderBy(p => p.DisplayOrder).ToListAsync();
    return Results.Ok(list);
}).RequireAuthorization();
app.MapPost("/api/admin/portfolio", async (PortfolioProjectDto dto, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    if (string.IsNullOrWhiteSpace(dto.Title)) return Results.BadRequest(new { Error = "Title required" });
    var slug = string.IsNullOrWhiteSpace(dto.Slug) ? dto.Title.ToLower().Replace(" ", "-").Replace(".", "") : dto.Slug!;
    slug = slug.ToLower().Trim(); if (await db.PortfolioProjects.AnyAsync(x => x.Slug == slug)) return Results.BadRequest(new { Error = "Slug exists" });
    var p = new PortfolioProject { Title = dto.Title.Trim(), Slug = slug, ShortDescription = dto.ShortDescription ?? "", Description = dto.Description ?? "", Problem = dto.Problem ?? "", Solution = dto.Solution ?? "", Role = dto.Role ?? "", Architecture = dto.Architecture ?? "", DemoUrl = dto.DemoUrl, GitHubUrl = dto.GitHubUrl, ProductUrl = dto.ProductUrl, Status = dto.Status ?? "draft", Featured = dto.Featured ?? false, DisplayOrder = dto.DisplayOrder ?? 0, PublishedAt = dto.Status == "published" ? DateTime.UtcNow : null };
    if (dto.TechStack != null) p.SetTechStack(dto.TechStack); if (dto.AiCapabilities != null) p.SetAiCapabilities(dto.AiCapabilities); if (dto.CloudCapabilities != null) p.SetCloudCapabilities(dto.CloudCapabilities); if (dto.Screenshots != null) p.SetScreenshots(dto.Screenshots);
    db.PortfolioProjects.Add(p); await db.SaveChangesAsync(); return Results.Created($"/api/portfolio/{p.Slug}", p);
}).RequireAuthorization();
app.MapPut("/api/admin/portfolio/{id:guid}", async (Guid id, PortfolioProjectDto dto, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.PortfolioProjects.FindAsync(id); if (p is null) return Results.NotFound();
    if (!string.IsNullOrWhiteSpace(dto.Title)) p.Title = dto.Title.Trim();
    if (!string.IsNullOrWhiteSpace(dto.Slug)) p.Slug = dto.Slug!.ToLower().Trim();
    if (dto.ShortDescription != null) p.ShortDescription = dto.ShortDescription; if (dto.Description != null) p.Description = dto.Description; if (dto.Problem != null) p.Problem = dto.Problem; if (dto.Solution != null) p.Solution = dto.Solution; if (dto.Role != null) p.Role = dto.Role; if (dto.Architecture != null) p.Architecture = dto.Architecture; if (dto.TechStack != null) p.SetTechStack(dto.TechStack); if (dto.AiCapabilities != null) p.SetAiCapabilities(dto.AiCapabilities); if (dto.CloudCapabilities != null) p.SetCloudCapabilities(dto.CloudCapabilities); if (dto.Screenshots != null) p.SetScreenshots(dto.Screenshots);
    if (dto.DemoUrl != null) p.DemoUrl = dto.DemoUrl; if (dto.GitHubUrl != null) p.GitHubUrl = dto.GitHubUrl; if (dto.ProductUrl != null) p.ProductUrl = dto.ProductUrl; if (dto.Status != null) { p.Status = dto.Status; if (dto.Status == "published" && p.PublishedAt is null) p.PublishedAt = DateTime.UtcNow; } if (dto.Featured.HasValue) p.Featured = dto.Featured.Value; if (dto.DisplayOrder.HasValue) p.DisplayOrder = dto.DisplayOrder.Value;
    p.UpdatedAt = DateTime.UtcNow; p.IsManualEdit = true; await db.SaveChangesAsync(); return Results.Ok(p);
}).RequireAuthorization();
app.MapDelete("/api/admin/portfolio/{id:guid}", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.PortfolioProjects.FindAsync(id); if (p is null) return Results.NotFound();
    db.PortfolioProjects.Remove(p); await db.SaveChangesAsync(); return Results.Ok(new { Message = "Deleted" });
}).RequireAuthorization();

// ── Products ──
app.MapGet("/api/products", async (LabDbContext db) =>
{
    var list = await db.Products.Where(p => p.Status == "published" || p.Status == "featured").OrderBy(p => p.DisplayOrder).ToListAsync();
    return Results.Ok(list);
});
app.MapGet("/api/products/{slug}", async (string slug, LabDbContext db) =>
{
    var p = await db.Products.FirstOrDefaultAsync(x => x.Slug == slug); return p is not null ? Results.Ok(p) : Results.NotFound();
});
app.MapGet("/api/admin/products", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    return Results.Ok(await db.Products.OrderBy(p => p.DisplayOrder).ToListAsync());
}).RequireAuthorization();
app.MapPost("/api/admin/products", async (ProductDto dto, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    if (string.IsNullOrWhiteSpace(dto.Name)) return Results.BadRequest(new { Error = "Name required" });
    var slug = string.IsNullOrWhiteSpace(dto.Slug) ? dto.Name.ToLower().Replace(" ", "-") : dto.Slug!;
    slug = slug.ToLower().Trim(); if (await db.Products.AnyAsync(x => x.Slug == slug)) return Results.BadRequest(new { Error = "Slug exists" });
    var p = new Product { Name = dto.Name.Trim(), Slug = slug, Category = dto.Category ?? "", Description = dto.Description ?? "", LogoUrl = dto.LogoUrl, AiCapabilities = dto.AiCapabilities, Architecture = dto.Architecture, ProductUrl = dto.ProductUrl, GitHubRepoId = dto.GitHubRepoId, Status = dto.Status ?? "draft", Featured = dto.Featured ?? false, DisplayOrder = dto.DisplayOrder ?? 0 };
    if (dto.Screenshots != null) p.SetScreenshots(dto.Screenshots); if (dto.Features != null) p.SetFeatures(dto.Features); if (dto.TechStack != null) p.SetTechStack(dto.TechStack);
    db.Products.Add(p); await db.SaveChangesAsync(); return Results.Created($"/api/products/{p.Slug}", p);
}).RequireAuthorization();
app.MapPut("/api/admin/products/{id:guid}", async (Guid id, ProductDto dto, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.Products.FindAsync(id); if (p is null) return Results.NotFound();
    if (!string.IsNullOrWhiteSpace(dto.Name)) p.Name = dto.Name.Trim(); if (!string.IsNullOrWhiteSpace(dto.Slug)) p.Slug = dto.Slug!.ToLower().Trim(); if (dto.Category != null) p.Category = dto.Category; if (dto.Description != null) p.Description = dto.Description; if (dto.LogoUrl != null) p.LogoUrl = dto.LogoUrl; if (dto.AiCapabilities != null) p.AiCapabilities = dto.AiCapabilities; if (dto.Architecture != null) p.Architecture = dto.Architecture; if (dto.ProductUrl != null) p.ProductUrl = dto.ProductUrl; if (dto.GitHubRepoId != null) p.GitHubRepoId = dto.GitHubRepoId; if (dto.Status != null) p.Status = dto.Status; if (dto.Featured.HasValue) p.Featured = dto.Featured.Value; if (dto.DisplayOrder.HasValue) p.DisplayOrder = dto.DisplayOrder.Value;
    if (dto.Screenshots != null) p.SetScreenshots(dto.Screenshots); if (dto.Features != null) p.SetFeatures(dto.Features); if (dto.TechStack != null) p.SetTechStack(dto.TechStack);
    p.UpdatedAt = DateTime.UtcNow; await db.SaveChangesAsync(); return Results.Ok(p);
}).RequireAuthorization();
app.MapDelete("/api/admin/products/{id:guid}", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.Products.FindAsync(id); if (p is null) return Results.NotFound();
    db.Products.Remove(p); await db.SaveChangesAsync(); return Results.Ok(new { Message = "Deleted" });
}).RequireAuthorization();

// ── GitHub Sync ──
app.MapGet("/api/admin/github/repos", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var list = await db.GitHubRepositories.OrderByDescending(r => r.PushedAt).ToListAsync();
    return Results.Ok(list);
}).RequireAuthorization();
app.MapGet("/api/admin/github/sync-log", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var log = await db.ProjectSyncLogs.OrderByDescending(l => l.StartedAt).FirstOrDefaultAsync();
    return log is not null ? Results.Ok(log) : Results.NotFound();
}).RequireAuthorization();
app.MapPost("/api/admin/github/sync", async (HttpContext http, LabDbContext db, IConfiguration cfg) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var token = cfg["GITHUB_TOKEN"] ?? cfg["GitHub:Token"] ?? "";
    var owner = cfg["GITHUB_OWNER"] ?? cfg["GitHub:Owner"] ?? "rajibmahata";
    if (string.IsNullOrWhiteSpace(token)) return Results.BadRequest(new { Error = "GITHUB_TOKEN not configured on server" });
    var log = new ProjectSyncLog { StartedAt = DateTime.UtcNow };
    db.ProjectSyncLogs.Add(log); await db.SaveChangesAsync();
    try
    {
        using var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("RajibLabs-CMS");
        httpClient.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
        var resp = await httpClient.GetAsync($"https://api.github.com/users/{owner}/repos?per_page=100&sort=updated");
        if (!resp.IsSuccessStatusCode) throw new Exception($"GitHub API {resp.StatusCode}");
        var json = await resp.Content.ReadAsStringAsync();
        var repos = System.Text.Json.JsonSerializer.Deserialize<List<System.Text.Json.JsonElement>>(json) ?? new();
        log.Found = repos.Count;
        int added = 0, updated = 0;
        foreach (var r in repos)
        {
            var gid = r.GetProperty("id").GetInt64();
            var name = r.GetProperty("name").GetString() ?? "";
            var fullName = r.GetProperty("full_name").GetString() ?? "";
            var desc = r.TryGetProperty("description", out var d) && d.ValueKind != System.Text.Json.JsonValueKind.Null ? d.GetString() ?? "" : "";
            var htmlUrl = r.GetProperty("html_url").GetString() ?? "";
            var lang = r.TryGetProperty("language", out var l) && l.ValueKind != System.Text.Json.JsonValueKind.Null ? l.GetString() ?? "" : "";
            var stars = r.GetProperty("stargazers_count").GetInt32();
            var forks = r.GetProperty("forks_count").GetInt32();
            var isPrivate = r.GetProperty("private").GetBoolean();
            var pushedAt = r.TryGetProperty("pushed_at", out var pa) && pa.ValueKind != System.Text.Json.JsonValueKind.Null ? pa.GetDateTime() : (DateTime?)null;
            var existing = await db.GitHubRepositories.FirstOrDefaultAsync(x => x.GitHubId == gid);
            // Classify
            string classification = "professional";
            if ((desc + name).ToLower().Contains("ai") || lang == "Python") classification = "ai";
            else if (lang.Contains("C#") || desc.Contains(".NET")) classification = "dotnet";
            // AI enrichment heuristic (placeholder, editable)
            var aiSummary = string.IsNullOrWhiteSpace(desc) ? $"{name} — {lang} project by {owner}" : desc;
            if (existing is null)
            {
                var gr = new GitHubRepository { GitHubId = gid, Name = name, FullName = fullName, Description = desc, HtmlUrl = htmlUrl, Language = lang, Stars = stars, Forks = forks, IsPrivate = isPrivate, PushedAt = pushedAt, UpdatedAtGitHub = pushedAt, LastSyncedAt = DateTime.UtcNow, AiSummary = aiSummary, AiConfidence = "medium", Classification = classification, SyncStatus = "review" };
                db.GitHubRepositories.Add(gr); added++;
            }
            else
            {
                if (existing.IsManuallyEdited) { updated++; continue; } // preserve manual edits
                existing.Name = name; existing.FullName = fullName; existing.Description = desc; existing.HtmlUrl = htmlUrl; existing.Language = lang; existing.Stars = stars; existing.Forks = forks; existing.PushedAt = pushedAt; existing.UpdatedAtGitHub = pushedAt; existing.LastSyncedAt = DateTime.UtcNow;
                if (string.IsNullOrWhiteSpace(existing.AiSummary) || existing.AiSummary == existing.Description) existing.AiSummary = aiSummary;
                updated++;
            }
        }
        log.Added = added; log.Updated = updated; log.FinishedAt = DateTime.UtcNow; await db.SaveChangesAsync();
        return Results.Ok(new { log.Found, log.Added, log.Updated, Message = "Sync complete" });
    }
    catch (Exception ex)
    {
        log.ErrorsJson = System.Text.Json.JsonSerializer.Serialize(new[] { ex.Message }); log.FinishedAt = DateTime.UtcNow; await db.SaveChangesAsync();
        return Results.Json(new { Error = ex.Message }, statusCode: 500);
    }
}).RequireAuthorization();
app.MapPatch("/api/admin/github/repos/{id:guid}", async (Guid id, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var r = await db.GitHubRepositories.FindAsync(id); if (r is null) return Results.NotFound();
    var body = await System.Text.Json.JsonSerializer.DeserializeAsync<Dictionary<string, System.Text.Json.JsonElement>>(http.Request.Body);
    if (body is null) return Results.BadRequest(new { Error = "Invalid body" });
    if (body.TryGetValue("syncStatus", out var s)) r.SyncStatus = s.GetString() ?? r.SyncStatus;
    if (body.TryGetValue("classification", out var c)) r.Classification = c.GetString() ?? r.Classification;
    if (body.TryGetValue("aiSummary", out var a)) r.AiSummary = a.GetString() ?? r.AiSummary;
    if (body.TryGetValue("aiTitle", out var t)) r.AiTitle = t.GetString() ?? r.AiTitle;
    r.IsManuallyEdited = true; await db.SaveChangesAsync(); return Results.Ok(r);
}).RequireAuthorization();

// ── Profile CMS ──
app.MapGet("/api/admin/profile", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.Profiles.FirstOrDefaultAsync(); return p is not null ? Results.Ok(p) : Results.NotFound();
}).RequireAuthorization();
app.MapPut("/api/admin/profile", async (ProfileUpdateDto dto, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var p = await db.Profiles.FirstOrDefaultAsync(); if (p is null) return Results.NotFound();
    if (dto.FullName != null) p.FullName = dto.FullName; if (dto.Title != null) p.Title = dto.Title; if (dto.Bio != null) p.Bio = dto.Bio;
    if (dto.Skills != null) p.SetSkills(dto.Skills); if (dto.SocialLinks != null) p.SetSocialLinks(dto.SocialLinks); if (dto.Career != null) p.SetCareer(dto.Career);
    if (dto.Headline != null) p.Headline = dto.Headline; if (dto.Location != null) p.Location = dto.Location; if (dto.Phone != null) p.Phone = dto.Phone; if (dto.WhatsApp != null) p.WhatsApp = dto.WhatsApp; if (dto.Email != null) p.Email = dto.Email; if (dto.LinkedIn != null) p.LinkedIn = dto.LinkedIn; if (dto.GitHub != null) p.GitHub = dto.GitHub; if (dto.Website != null) p.Website = dto.Website; if (dto.ProfileImageUrl != null) p.ProfileImageUrl = dto.ProfileImageUrl;
    p.UpdatedAt = DateTime.UtcNow; await db.SaveChangesAsync(); return Results.Ok(p);
}).RequireAuthorization();
app.MapGet("/api/admin/dashboard", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var resume = await db.Resumes.Where(r => r.Status == "published").OrderByDescending(r => r.Version).FirstOrDefaultAsync();
    var portfolioCount = await db.PortfolioProjects.CountAsync(); var publishedPortfolio = await db.PortfolioProjects.CountAsync(p => p.Status == "published");
    var githubCount = await db.GitHubRepositories.CountAsync(); var productCount = await db.Products.CountAsync();
    var lastSync = await db.ProjectSyncLogs.OrderByDescending(l => l.StartedAt).FirstOrDefaultAsync();
    var profile = await db.Profiles.FirstOrDefaultAsync();
    return Results.Ok(new { resume, portfolio = new { total = portfolioCount, published = publishedPortfolio }, github = new { total = githubCount }, products = new { total = productCount }, lastSync, profileUpdatedAt = profile?.UpdatedAt });
}).RequireAuthorization();

// ── Website Content ──
app.MapGet("/api/content/{key}", async (string key, LabDbContext db) =>
{
    var c = await db.WebsiteContents.FirstOrDefaultAsync(x => x.Key == key); return c is not null ? Results.Ok(c) : Results.NotFound();
});
app.MapGet("/api/admin/content", async (HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    return Results.Ok(await db.WebsiteContents.ToListAsync());
}).RequireAuthorization();
app.MapPut("/api/admin/content/{key}", async (string key, HttpContext http, LabDbContext db) =>
{
    if (!RequireAdmin(http)) return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    var body = await System.Text.Json.JsonSerializer.DeserializeAsync<Dictionary<string, System.Text.Json.JsonElement>>(http.Request.Body);
    var title = body != null && body.TryGetValue("title", out var t) ? t.GetString() ?? "" : "";
    var content = body != null && body.TryGetValue("body", out var b) ? b.GetRawText() : "{}";
    var existing = await db.WebsiteContents.FirstOrDefaultAsync(x => x.Key == key);
    if (existing is null) { existing = new WebsiteContent { Key = key, Title = title, BodyJson = content }; db.WebsiteContents.Add(existing); }
    else { existing.Title = title; existing.BodyJson = content; existing.UpdatedAt = DateTime.UtcNow; }
    await db.SaveChangesAsync(); return Results.Ok(existing);
}).RequireAuthorization();

// ── Run ──
app.Run();

// ── Seed Data ──
static void SeedData(LabDbContext db)
{
    var p1 = new Project { Id = Guid.NewGuid(), Title = "DocSignerHub", Slug = "docsignerhub", Description = "Digital signature SaaS platform with AI clause analysis, blockchain notarisation, visual workflow builder, and Stripe payment integration. 140+ REST API endpoints.", GitHubUrl = "https://github.com/rajibmahata/DocumentSigningPlatform", LiveUrl = "https://docsignerhub.com", Status = "development", CreatedAt = DateTime.UtcNow.AddMonths(-2), UpdatedAt = DateTime.UtcNow, LastCommitAt = DateTime.UtcNow.AddHours(-3) };
    p1.SetTechStack(new() { ".NET 8", "React", "SQL Server", "Azure", "Stripe", "OpenAI" });
    var p2 = new Project { Id = Guid.NewGuid(), Title = "AI Avatar RAG Platform", Slug = "ai-avatar-rag", Description = "Enterprise AI knowledge retrieval platform with avatar-based interaction, semantic search, and RAG pipelines.", GitHubUrl = "https://github.com/rajibmahata/AI-Avatar-RAG-Platform", Status = "development", CreatedAt = DateTime.UtcNow.AddMonths(-3), UpdatedAt = DateTime.UtcNow, LastCommitAt = DateTime.UtcNow.AddDays(-2) };
    p2.SetTechStack(new() { "Python", "FastAPI", "OpenAI", "RAG", "Vector DB", "React" });
    var p3 = new Project { Id = Guid.NewGuid(), Title = "Solicitor Case Management", Slug = "solicitor-cms", Description = "Legal enterprise workflow platform for case tracking, document management, and client communication.", GitHubUrl = "https://github.com/rajibmahata/SolicitorCaseManagementSystem", Status = "planning", CreatedAt = DateTime.UtcNow.AddMonths(-5), UpdatedAt = DateTime.UtcNow, LastCommitAt = DateTime.UtcNow.AddDays(-7) };
    p3.SetTechStack(new() { ".NET 8", "Blazor", "SQL Server", "Azure", "Cosmos DB" });
    var p4 = new Project { Id = Guid.NewGuid(), Title = "Rajib Labs Platform", Slug = "rajiblabs", Description = "AI-powered portfolio and software lab. Auto-populated from GitHub, managed by OpenClaw agents. This very platform.", GitHubUrl = "https://github.com/rajibmahata/rajiblabs-platform", Status = "development", CreatedAt = DateTime.UtcNow, UpdatedAt = DateTime.UtcNow, LastCommitAt = DateTime.UtcNow };
    p4.SetTechStack(new() { ".NET 8", "React", "TypeScript", "Tailwind CSS", "SQLite", "OpenClaw" });
    db.Projects.AddRange(p1, p2, p3, p4);
    db.SaveChanges();
    db.Activities.AddRange(
        new Activity { Id = Guid.NewGuid(), ProjectId = p4.Id, Type = "milestone", Title = "Rajib Labs Platform — Design upgrade", Description = "Modern glass-morphism UI with animations + SQLite backend live", Timestamp = DateTime.UtcNow },
        new Activity { Id = Guid.NewGuid(), ProjectId = p1.Id, Type = "commit", Title = "DocSignerHub — Auth refactor merged", Description = "Middleware cleanup, API rate limiting, security hardening", Timestamp = DateTime.UtcNow.AddHours(-3) },
        new Activity { Id = Guid.NewGuid(), ProjectId = p2.Id, Type = "milestone", Title = "RAG Platform — Embedding pipeline live", Description = "Hybrid vector search with semantic ranking operational", Timestamp = DateTime.UtcNow.AddDays(-1) },
        new Activity { Id = Guid.NewGuid(), ProjectId = p1.Id, Type = "deploy", Title = "DocSignerHub — Blog system shipped", Description = "AI-generated tutorial blogs live on docsignerhub.com/blog", Timestamp = DateTime.UtcNow.AddDays(-2) },
        new Activity { Id = Guid.NewGuid(), ProjectId = p3.Id, Type = "commit", Title = "Solicitor CMS — Workflow diagram module", Description = "Visual case flow builder prototype in progress", Timestamp = DateTime.UtcNow.AddDays(-5) },
        new Activity { Id = Guid.NewGuid(), ProjectId = p4.Id, Type = "commit", Title = "Rajib Labs — Initial scaffold", Description = "React + .NET 8 + SQLite backend deployed, 4 projects seeded", Timestamp = DateTime.UtcNow.AddHours(-1) }
    );
    db.SaveChanges();
    var profile = new Profile { Id = Guid.NewGuid(), FullName = "Rajib Mahata", Title = "Senior Software Architect | AI & SaaS Platform Builder", Bio = "Independent software architect with 10+ years building production SaaS platforms, AI systems, and cloud-native applications. Specialising in .NET, Azure, and AI/LLM integrations." };
    profile.SetSkills(new() { ".NET 8/10", "C#", "ASP.NET Core", "Blazor", "React", "Python FastAPI", "Azure Cloud", "Azure DevOps", "Microservices", "CQRS & Design Patterns", "SQL Server", "Cosmos DB", "OpenAI/Gemini APIs", "RAG Systems", "Docker", "GitHub Copilot" });
    profile.SetSocialLinks(new() { { "github", "https://github.com/rajibmahata" }, { "linkedin", "https://linkedin.com/in/rajib-mahata" } });
    profile.SetCareer(new() { new() { Company = "Fortune 500 Healthcare", Role = "Solutions Architect", Period = "Aug 2019 – Present", Client = "Healthcare & Pharmacy (USA)", Color = "var(--c-accent-blue)", Achievements = new() { "Led development of open APIs, reducing pharmacy vendor dependency by 100%", "Architected data lake on Azure for raw prescription/patient data ingestion and processing", "Automated Prescription Refill System — 30% faster processing, 40% fewer medication errors", "Vaccine Appointment System — streamlined COVID-19 immunization scheduling nationally", "Built Rule Engine (CQRS) on Azure PaaS processing 500K+ daily prescription events", "Deployed PWAs on Azure Cloud for secure, scalable pharmacy interfaces", "Integrated secure payment (MParks), barcode scanning, voice/SMS notifications" }, TechStack = new() { ".NET 8", "Blazor", "Azure Functions", "Logic Apps", "Service Bus", "Event Grid", "Cosmos DB", "Azure Data Factory", "AngularJS", "Open API" } }, new() { Company = "Telecom Enterprise", Role = "Platform Engineer", Period = "Jul 2016 – Feb 2019", Client = "Telecommunications (USA)", Color = "var(--c-accent-teal)", Achievements = new() { "Designed and built CMT application automating network equipment provisioning", "Reduced manual intervention by 30%, processing time by 40%", "Achieved 95% issue resolution within 24 hours via automated ticket system", "Built intuitive UI improving user satisfaction scores by 25%" }, TechStack = new() { "ASP.NET MVC", "WCF", "Entity Framework", "SQL Server", "JavaScript" } }, new() { Company = "Product Studio", Role = "Full-Stack Developer", Period = "Mar 2013 – Apr 2016", Color = "var(--c-accent-gold)", Achievements = new() { "Built Corporate Hour — B2B media advertisement & trade platform", "Developed Cinematic Lens — product visual storytelling platform", "Created TRANSZOOM — car rental & TruckIt365 freight matching solution", "Full-stack ownership: database design to frontend deployment" }, TechStack = new() { "ASP.NET MVC", "SQL Server", "JavaScript", "HTML/CSS", "AJAX" } } });
    db.Profiles.Add(profile);
    db.SaveChanges();
}
static void SeedCms(LabDbContext db, IConfiguration cfg)
{
    if (!db.Products.Any())
    {
        var pageFlow = new Product { Name = "Page Flow", Slug = "page-flow", Category = "RajibLabs Product", Description = "Visual workflow builder for document-intensive business processes — drag-drop pipeline designer, sequential/parallel approvals, HMAC-SHA256 token auth, audit trail, white-label API. Powers DocSignerHub and Solicitor CMS.", Status = "published", Featured = true, DisplayOrder = 1 };
        pageFlow.SetFeatures(new() { "Visual workflow designer", "Sequential & parallel approvals", "HMAC-SHA256 secure tokens", "Full audit trail", "White-label API", "140+ REST endpoints" });
        pageFlow.SetTechStack(new() { ".NET 8", "React", "Blazor", "Azure", "SQL Server", "OpenAI" });
        pageFlow.Architecture = "Microservices + CQRS + Event-driven"; pageFlow.AiCapabilities = "AI clause analysis, document intelligence";
        var docuflow = new Product { Name = "DocuFlow", Slug = "docuflow", Category = "SaaS", Description = "Enterprise document automation platform — template-driven generation, deadline tracking, client portal.", Status = "published", DisplayOrder = 2 };
        docuflow.SetFeatures(new() { "Template engine", "Deadline tracking" }); docuflow.SetTechStack(new() { ".NET 8", "Blazor", "Cosmos DB" });
        db.Products.AddRange(pageFlow, docuflow);
        db.SaveChanges();
    }
    if (!db.WebsiteContents.Any())
    {
        db.WebsiteContents.Add(new WebsiteContent { Key = "home_order", Title = "Home Section Order", BodyJson = "[\"hero\",\"overview\",\"about\",\"whatido\",\"expertise\",\"ai\",\"products\",\"architecture\",\"experience\",\"projects\",\"insights\",\"contact\"]" });
        db.SaveChanges();
    }
    // Seed initial resume from Data/Rajib-Mahata-Resume-2026.pdf if DB empty
    if (!db.Resumes.Any())
    {
        var dataPath = Path.Combine(AppContext.BaseDirectory, "Data", "Rajib-Mahata-Resume-2026.pdf");
        // Fallback to content root Data
        if (!File.Exists(dataPath)) dataPath = Path.Combine(Directory.GetCurrentDirectory(), "Data", "Rajib-Mahata-Resume-2026.pdf");
        if (File.Exists(dataPath))
        {
            var uploadsDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads", "resumes");
            Directory.CreateDirectory(uploadsDir);
            var destName = "Rajib-Mahata-Resume-2026.pdf";
            var destPath = Path.Combine(uploadsDir, destName);
            try { File.Copy(dataPath, destPath, overwrite: true); } catch { }
            var info = new FileInfo(dataPath);
            var resume = new Resume { FileName = "Rajib-Mahata-Resume-2026.pdf", StoredPath = $"uploads/resumes/{destName}", ContentType = "application/pdf", SizeBytes = info.Length, Version = 1, Status = "published", UploadedAt = DateTime.UtcNow, PublishedAt = DateTime.UtcNow };
            db.Resumes.Add(resume);
            db.SaveChanges();
        }
    }
    // Ensure profile has correct phone (centralized +91 84202 49020)
    var profile = db.Profiles.FirstOrDefault();
    if (profile != null && string.IsNullOrWhiteSpace(profile.Phone))
    {
        profile.Phone = "+91 84202 49020";
        profile.WhatsApp = "+91 84202 49020";
        profile.UpdatedAt = DateTime.UtcNow;
        db.SaveChanges();
    }
}
