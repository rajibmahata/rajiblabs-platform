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
        p.UpdatedAt
    }) : Results.NotFound();
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
});

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
});

app.MapGet("/api/health", () => Results.Ok(new { Status = "healthy", Timestamp = DateTime.UtcNow }));

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
    profile.SetSkills(new() { ".NET 8/10", "C#", "ASP.NET Core", "Blazor", "React", "Python FastAPI", "Azure Cloud", "Microservices", "SQL Server", "Cosmos DB", "OpenAI/Gemini APIs", "RAG Systems", "Docker", "GitHub Copilot" });
    profile.SetSocialLinks(new() { { "github", "https://github.com/rajibmahata" }, { "linkedin", "https://linkedin.com/in/rajib-mahata" } });

    db.Profiles.Add(profile);
    db.SaveChanges();
}
