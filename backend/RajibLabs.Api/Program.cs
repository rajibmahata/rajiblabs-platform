using System;
using System.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
// Rajib Labs API — Agent-Managed Portfolio Backend
// .NET 8 Minimal API + SQLite | Managed by RCore (OpenClaw)

using Microsoft.EntityFrameworkCore;
using RajibLabs.Api.Data;
using RajibLabs.Api.Models;

var builder = WebApplication.CreateBuilder(args);

// ── Database ──
builder.Services.AddDbContext<LabDbContext>(options =>
    options.UseSqlite("Data Source=rajiblabs.db"));

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:5173", "https://rajiblabs.com")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

// ── JSON Serialization (camelCase to match frontend) ──
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    options.SerializerOptions.PropertyNameCaseInsensitive = true;
});

var app = builder.Build();

// ── Ensure DB created & seeded ──
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<LabDbContext>();
    db.Database.EnsureCreated();

    if (!db.Projects.Any())
    {
        SeedData(db);
    }
}

app.UseCors();
app.UseDefaultFiles();
app.UseStaticFiles();

// ── Endpoints ──

app.MapGet("/api/projects", async (LabDbContext db) =>
{
    var projects = await db.Projects.OrderByDescending(p => p.UpdatedAt).ToListAsync();
    return Results.Ok(projects.Select(p => new {
        p.Id, p.Title, p.Slug, p.Description,
        techStack = p.TechStack,
        p.GitHubUrl, p.LiveUrl, p.Status,
        p.CreatedAt, p.UpdatedAt, p.LastCommitAt
    }));
});

app.MapGet("/api/projects/{id:guid}", async (Guid id, LabDbContext db) =>
{
    var p = await db.Projects.FindAsync(id);
    return p is not null ? Results.Ok(new {
        p.Id, p.Title, p.Slug, p.Description,
        techStack = p.TechStack,
        p.GitHubUrl, p.LiveUrl, p.Status,
        p.CreatedAt, p.UpdatedAt, p.LastCommitAt
    }) : Results.NotFound();
});

app.MapGet("/api/activity", async (int? limit, LabDbContext db) =>
{
    var query = db.Activities.OrderByDescending(a => a.Timestamp);
    var result = limit.HasValue ? query.Take(limit.Value) : query;
    return Results.Ok(await result.ToListAsync());
});

app.MapGet("/api/profile", async (LabDbContext db) =>
{
    var p = await db.Profiles.FirstOrDefaultAsync();
    return p is not null ? Results.Ok(new {
        p.Id, p.FullName, p.Title, p.Bio,
        skills = p.Skills,
        socialLinks = p.SocialLinks,
        career = p.Career,
        p.UpdatedAt
    }) : Results.NotFound();
});

// ── API Key Auth Filter ──
static async ValueTask<object?> RequireApiKey(EndpointFilterInvocationContext context, EndpointFilterDelegate next)
{
    var config = context.HttpContext.RequestServices.GetRequiredService<IConfiguration>();
    var expectedKey = config["ApiKey"];

    // In dev: if no key is configured, allow all requests
    if (string.IsNullOrWhiteSpace(expectedKey))
        return await next(context);

    if (!context.HttpContext.Request.Headers.TryGetValue("X-Api-Key", out var providedKey) ||
        !string.Equals(providedKey, expectedKey, StringComparison.Ordinal))
    {
        return Results.Json(new { Error = "Unauthorized" }, statusCode: 401);
    }

    return await next(context);
}

// ── Contact Endpoint ──

app.MapPost("/api/contact", async (ContactDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Name) || string.IsNullOrWhiteSpace(dto.Email) || string.IsNullOrWhiteSpace(dto.Message))
        return Results.BadRequest(new { Error = "Name, email, and message are required" });

    var contact = new Contact
    {
        Id = Guid.NewGuid(),
        Name = dto.Name.Trim(),
        Email = dto.Email.Trim(),
        Company = dto.Company?.Trim(),
        Message = dto.Message.Trim(),
        SubmittedAt = DateTime.UtcNow
    };
    db.Contacts.Add(contact);
    await db.SaveChangesAsync();

    return Results.Created($"/api/contact/{contact.Id}", new
    {
        contact.Id,
        Message = "Message received. Thank you!"
    });
});

// ── Write Endpoints ──

app.MapPost("/api/activity", async (ActivityDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title))
        return Results.BadRequest(new { Error = "Title is required" });

    var activity = new Activity
    {
        Id = Guid.NewGuid(),
        ProjectId = dto.ProjectId,
        Type = dto.Type ?? "commit",
        Title = dto.Title,
        Description = dto.Description ?? string.Empty,
        Timestamp = dto.Timestamp ?? DateTime.UtcNow
    };
    db.Activities.Add(activity);
    await db.SaveChangesAsync();

    // Also update the parent project's UpdatedAt and LastCommitAt
    var project = await db.Projects.FindAsync(dto.ProjectId);
    if (project is not null)
    {
        project.UpdatedAt = DateTime.UtcNow;
        if (dto.Type == "commit" && dto.CommittedAt.HasValue)
        {
            if (project.LastCommitAt is null || dto.CommittedAt.Value > project.LastCommitAt)
                project.LastCommitAt = dto.CommittedAt.Value;
        }
        else if (dto.Type == "commit")
            project.LastCommitAt = DateTime.UtcNow;
        await db.SaveChangesAsync();
    }

    return Results.Created($"/api/activity/{activity.Id}", new {
        activity.Id, activity.ProjectId, activity.Type,
        activity.Title, activity.Description, activity.Timestamp
    });
}).AddEndpointFilter(RequireApiKey);

app.MapMethods("/api/projects/{id:guid}", new[] { "PATCH" }, async (Guid id, ProjectPatchDto dto, LabDbContext db) =>
{
    var project = await db.Projects.FindAsync(id);
    if (project is null) return Results.NotFound();

    if (dto.LastCommitAt.HasValue)
        project.LastCommitAt = dto.LastCommitAt.Value;
    if (dto.Status is not null)
        project.Status = dto.Status;
    if (dto.Title is not null)
        project.Title = dto.Title;
    if (dto.Description is not null)
        project.Description = dto.Description;

    project.UpdatedAt = DateTime.UtcNow;
    await db.SaveChangesAsync();

    return Results.Ok(new {
        project.Id, project.Title, project.Slug, project.Description,
        techStack = project.TechStack,
        project.GitHubUrl, project.LiveUrl, project.Status,
        project.CreatedAt, project.UpdatedAt, project.LastCommitAt
    });
}).AddEndpointFilter(RequireApiKey);

app.MapGet("/api/health", () => Results.Ok(new { Status = "healthy", Timestamp = DateTime.UtcNow }));

// ── LinkedIn Learning Endpoints ──

app.MapGet("/api/learning", async (LabDbContext db) =>
{
    var courses = await db.LinkedInCourses
        .OrderByDescending(c => c.Status == "in-progress" ? 1 : 0)
        .ThenByDescending(c => c.UpdatedAt)
        .ToListAsync();
    return Results.Ok(courses.Select(c => new {
        c.Id, c.Title, c.Url, c.Instructor, c.Duration,
        c.Level, c.CompletedAt, c.Status, c.UpdatedAt
    }));
});

app.MapPost("/api/learning", async (LinkedInCourseDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title))
        return Results.BadRequest(new { Error = "Title is required" });

    // Upsert by URL (unique) — update if exists, insert if new
    var existing = await db.LinkedInCourses.FirstOrDefaultAsync(c => c.Url == dto.Url);
    if (existing != null)
    {
        existing.Title = dto.Title;
        existing.Instructor = dto.Instructor;
        existing.Duration = dto.Duration;
        existing.Level = dto.Level;
        existing.CompletedAt = dto.CompletedAt;
        existing.Status = dto.Status ?? existing.Status;
        existing.UpdatedAt = DateTime.UtcNow;
    }
    else
    {
        var course = new LinkedInCourse
        {
            Id = Guid.NewGuid(),
            Title = dto.Title.Trim(),
            Url = dto.Url.Trim(),
            Instructor = dto.Instructor?.Trim(),
            Duration = dto.Duration,
            Level = dto.Level,
            CompletedAt = dto.CompletedAt,
            Status = dto.Status ?? "in-progress",
            UpdatedAt = DateTime.UtcNow
        };
        db.LinkedInCourses.Add(course);
    }
    await db.SaveChangesAsync();
    return Results.Ok(new { Message = "Course synced" });
});

// ── Subscribe Endpoint ──

app.MapPost("/api/subscribe", async (SubscriberDto dto, LabDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(dto.Email) || !dto.Email.Contains('@'))
        return Results.BadRequest(new { Error = "Valid email is required" });

    var email = dto.Email.Trim().ToLower();
    var existing = await db.Subscribers.FirstOrDefaultAsync(s => s.Email == email);
    if (existing != null)
    {
        if (!existing.IsActive)
        {
            existing.IsActive = true;
            existing.SubscribedAt = DateTime.UtcNow;
            existing.UnsubscribedAt = null;
            await db.SaveChangesAsync();
            return Results.Ok(new { Message = "Welcome back! You're re-subscribed." });
        }
        return Results.Ok(new { Message = "You're already subscribed!" });
    }

    var sub = new Subscriber
    {
        Id = Guid.NewGuid(),
        Email = email,
        IsActive = true,
        SubscribedAt = DateTime.UtcNow
    };
    db.Subscribers.Add(sub);
    await db.SaveChangesAsync();
    return Results.Created("/api/subscribe", new { Message = "Subscribed! Thank you." });
});

app.MapPost("/api/unsubscribe", async (SubscriberDto dto, LabDbContext db) =>
{
    var sub = await db.Subscribers.FirstOrDefaultAsync(s => s.Email == dto.Email.Trim().ToLower() && s.IsActive);
    if (sub is null) return Results.NotFound(new { Error = "Email not found" });
    sub.IsActive = false;
    sub.UnsubscribedAt = DateTime.UtcNow;
    await db.SaveChangesAsync();
    return Results.Ok(new { Message = "Unsubscribed. We'll miss you!" });
});

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

    var profile = new Profile
    {
        Id = Guid.NewGuid(),
        FullName = "Rajib Mahata",
        Title = "Senior Software Architect | AI & SaaS Platform Builder",
        Bio = "Independent software architect with 10+ years building production SaaS platforms, AI systems, and cloud-native applications. Specialising in .NET, Azure, and AI/LLM integrations."
    };
    profile.SetSkills(new() { ".NET 8/10", "C#", "ASP.NET Core", "Blazor", "React", "Python FastAPI", "Azure Cloud", "Azure DevOps", "Microservices", "CQRS & Design Patterns", "SQL Server", "Cosmos DB", "OpenAI/Gemini APIs", "RAG Systems", "Docker", "GitHub Copilot" });
    profile.SetSocialLinks(new() { { "github", "https://github.com/rajibmahata" }, { "linkedin", "https://linkedin.com/in/rajib-mahata" } });
    profile.SetCareer(new()
    {
        new() { Company = "Fortune 500 Healthcare", Role = "Solutions Architect", Period = "Aug 2019 – Present", Client = "Healthcare & Pharmacy (USA)", Color = "var(--c-accent-blue)", Achievements = new() { "Led development of open APIs, reducing pharmacy vendor dependency by 100%", "Architected data lake on Azure for raw prescription/patient data ingestion and processing", "Automated Prescription Refill System — 30% faster processing, 40% fewer medication errors", "Vaccine Appointment System — streamlined COVID-19 immunization scheduling nationally", "Built Rule Engine (CQRS) on Azure PaaS processing 500K+ daily prescription events", "Deployed PWAs on Azure Cloud for secure, scalable pharmacy interfaces", "Integrated secure payment (MParks), barcode scanning, voice/SMS notifications" }, TechStack = new() { ".NET 8", "Blazor", "Azure Functions", "Logic Apps", "Service Bus", "Event Grid", "Cosmos DB", "Azure Data Factory", "AngularJS", "Open API" } },
        new() { Company = "Telecom Enterprise", Role = "Platform Engineer", Period = "Jul 2016 – Feb 2019", Client = "Telecommunications (USA)", Color = "var(--c-accent-teal)", Achievements = new() { "Designed and built CMT application automating network equipment provisioning", "Reduced manual intervention by 30%, processing time by 40%", "Achieved 95% issue resolution within 24 hours via automated ticket system", "Built intuitive UI improving user satisfaction scores by 25%" }, TechStack = new() { "ASP.NET MVC", "WCF", "Entity Framework", "SQL Server", "JavaScript" } },
        new() { Company = "Product Studio", Role = "Full-Stack Developer", Period = "Mar 2013 – Apr 2016", Color = "var(--c-accent-gold)", Achievements = new() { "Built Corporate Hour — B2B media advertisement & trade platform", "Developed Cinematic Lens — product visual storytelling platform", "Created TRANSZOOM — car rental & TruckIt365 freight matching solution", "Full-stack ownership: database design to frontend deployment" }, TechStack = new() { "ASP.NET MVC", "SQL Server", "JavaScript", "HTML/CSS", "AJAX" } }
    });

    db.Profiles.Add(profile);
    db.SaveChanges();
}
