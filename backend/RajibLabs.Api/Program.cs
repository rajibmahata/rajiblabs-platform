// Rajib Labs API — Agent-Managed Portfolio Backend
// .NET 8 Minimal API | Managed by RCore (OpenClaw)

using RajibLabs.Api.Models;

var builder = WebApplication.CreateBuilder(args);

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
app.UseCors();

// ── In-Memory Data Store (replace with SQL Server before production) ──

var projects = new List<Project>
{
    new()
    {
        Id = Guid.NewGuid(),
        Title = "DocSignerHub",
        Slug = "docsignerhub",
        Description = "Digital signature SaaS platform with AI clause analysis, blockchain notarisation, visual workflow builder, and Stripe payment integration. 140+ REST API endpoints.",
        TechStack = new() { ".NET 8", "React", "SQL Server", "Azure", "Stripe", "OpenAI" },
        GitHubUrl = "https://github.com/rajibmahata/DocumentSigningPlatform",
        LiveUrl = "https://docsignerhub.com",
        Status = "development",
        CreatedAt = DateTime.UtcNow.AddMonths(-2),
        LastCommitAt = DateTime.UtcNow.AddHours(-3)
    },
    new()
    {
        Id = Guid.NewGuid(),
        Title = "AI Avatar RAG Platform",
        Slug = "ai-avatar-rag",
        Description = "Enterprise AI knowledge retrieval platform with avatar-based interaction, semantic search, and RAG pipelines.",
        TechStack = new() { "Python", "FastAPI", "OpenAI", "RAG", "Vector DB", "React" },
        GitHubUrl = "https://github.com/rajibmahata/AI-Avatar-RAG-Platform",
        Status = "development",
        CreatedAt = DateTime.UtcNow.AddMonths(-3),
        LastCommitAt = DateTime.UtcNow.AddDays(-2)
    },
    new()
    {
        Id = Guid.NewGuid(),
        Title = "Solicitor Case Management",
        Slug = "solicitor-cms",
        Description = "Legal enterprise workflow platform for case tracking, document management, and client communication.",
        TechStack = new() { ".NET 8", "Blazor", "SQL Server", "Azure", "Cosmos DB" },
        GitHubUrl = "https://github.com/rajibmahata/SolicitorCaseManagementSystem",
        Status = "planning",
        CreatedAt = DateTime.UtcNow.AddMonths(-5),
        LastCommitAt = DateTime.UtcNow.AddDays(-7)
    }
};

var activities = new List<Activity>
{
    new() { Id = Guid.NewGuid(), ProjectId = projects[0].Id, Type = "commit", Title = "DocSignerHub — 3 new commits", Description = "Auth middleware refactor, API rate limiting, blog publish endpoint", Timestamp = DateTime.UtcNow.AddHours(-2) },
    new() { Id = Guid.NewGuid(), ProjectId = projects[1].Id, Type = "milestone", Title = "AI Avatar RAG — Embedding pipeline complete", Description = "Vector search with hybrid retrieval now functional", Timestamp = DateTime.UtcNow.AddDays(-1) },
    new() { Id = Guid.NewGuid(), ProjectId = projects[0].Id, Type = "deploy", Title = "DocSignerHub — Blog system deployed", Description = "Tutorial blog generation pipeline live on docsignerhub.com/blog", Timestamp = DateTime.UtcNow.AddDays(-2) }
};

var profile = new Profile
{
    Id = Guid.NewGuid(),
    FullName = "Rajib Mahata",
    Title = "Senior Software Architect | AI & SaaS Platform Builder",
    Bio = "Independent software architect with 10+ years building production SaaS platforms, AI systems, and cloud-native applications. Specialising in .NET, Azure, and AI/LLM integrations.",
    Skills = new() { ".NET 8/10", "C#", "ASP.NET Core", "Blazor", "React", "Python FastAPI", "Azure Cloud", "Microservices", "SQL Server", "Cosmos DB", "OpenAI/Gemini APIs", "RAG Systems", "Docker", "GitHub Copilot" },
    SocialLinks = new()
    {
        { "github", "https://github.com/rajibmahata" },
        { "linkedin", "https://linkedin.com/in/rajib-mahata" }
    }
};

// ── Endpoints ──

app.MapGet("/api/projects", () => Results.Ok(projects.OrderByDescending(p => p.UpdatedAt)));

app.MapGet("/api/projects/{id:guid}", (Guid id) =>
{
    var project = projects.FirstOrDefault(p => p.Id == id);
    return project is not null ? Results.Ok(project) : Results.NotFound();
});

app.MapPost("/api/projects", (Project project) =>
{
    project.Id = Guid.NewGuid();
    project.CreatedAt = DateTime.UtcNow;
    project.UpdatedAt = DateTime.UtcNow;
    projects.Add(project);
    return Results.Created($"/api/projects/{project.Id}", project);
});

app.MapGet("/api/activity", (int? limit) =>
{
    var result = activities.OrderByDescending(a => a.Timestamp);
    return Results.Ok(limit.HasValue ? result.Take(limit.Value) : result);
});

app.MapGet("/api/profile", () => Results.Ok(profile));

app.MapGet("/api/health", () => Results.Ok(new { Status = "healthy", Timestamp = DateTime.UtcNow }));

// ── Run ──

app.Run("http://0.0.0.0:5000");
