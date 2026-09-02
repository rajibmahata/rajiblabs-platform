using System.Text.Json;

namespace RajibLabs.Api.Models;

// ── Admin ──
public class AdminUser
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Username { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastLoginAt { get; set; }
}

// ── Resume ──
public class Resume
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string FileName { get; set; } = string.Empty;
    public string StoredPath { get; set; } = string.Empty;
    public string ContentType { get; set; } = string.Empty;
    public long SizeBytes { get; set; }
    public int Version { get; set; } = 1;
    public string Status { get; set; } = "published"; // published, draft, archived
    public DateTime UploadedAt { get; set; } = DateTime.UtcNow;
    public DateTime? PublishedAt { get; set; } = DateTime.UtcNow;
}

public class ResumeExtraction
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ResumeId { get; set; }
    public string ExtractedJson { get; set; } = "{}";
    public string Status { get; set; } = "review"; // review, approved, rejected
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public Resume? Resume { get; set; }
}

// ── Portfolio ──
public class PortfolioProject
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string ShortDescription { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Problem { get; set; } = string.Empty;
    public string Solution { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public string Architecture { get; set; } = string.Empty;
    public string TechStackJson { get; set; } = "[]";
    public string AiCapabilitiesJson { get; set; } = "[]";
    public string CloudCapabilitiesJson { get; set; } = "[]";
    public string ScreenshotsJson { get; set; } = "[]";
    public string? DemoUrl { get; set; }
    public string? GitHubUrl { get; set; }
    public string? ProductUrl { get; set; }
    public string Status { get; set; } = "draft"; // draft, review, published, hidden
    public bool Featured { get; set; }
    public int DisplayOrder { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? PublishedAt { get; set; }
    public bool IsManualEdit { get; set; }

    public List<string> TechStack => JsonSerializer.Deserialize<List<string>>(TechStackJson) ?? new();
    public void SetTechStack(List<string> v) => TechStackJson = JsonSerializer.Serialize(v);
    public List<string> AiCapabilities => JsonSerializer.Deserialize<List<string>>(AiCapabilitiesJson) ?? new();
    public void SetAiCapabilities(List<string> v) => AiCapabilitiesJson = JsonSerializer.Serialize(v);
    public List<string> CloudCapabilities => JsonSerializer.Deserialize<List<string>>(CloudCapabilitiesJson) ?? new();
    public void SetCloudCapabilities(List<string> v) => CloudCapabilitiesJson = JsonSerializer.Serialize(v);
    public List<string> Screenshots => JsonSerializer.Deserialize<List<string>>(ScreenshotsJson) ?? new();
    public void SetScreenshots(List<string> v) => ScreenshotsJson = JsonSerializer.Serialize(v);
}

public class PortfolioProjectDto
{
    public string Title { get; set; } = string.Empty;
    public string? Slug { get; set; }
    public string? ShortDescription { get; set; }
    public string? Description { get; set; }
    public string? Problem { get; set; }
    public string? Solution { get; set; }
    public string? Role { get; set; }
    public string? Architecture { get; set; }
    public List<string>? TechStack { get; set; }
    public List<string>? AiCapabilities { get; set; }
    public List<string>? CloudCapabilities { get; set; }
    public List<string>? Screenshots { get; set; }
    public string? DemoUrl { get; set; }
    public string? GitHubUrl { get; set; }
    public string? ProductUrl { get; set; }
    public string? Status { get; set; }
    public bool? Featured { get; set; }
    public int? DisplayOrder { get; set; }
}

// ── GitHub ──
public class GitHubRepository
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public long GitHubId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string HtmlUrl { get; set; } = string.Empty;
    public string Language { get; set; } = string.Empty;
    public string TopicsJson { get; set; } = "[]";
    public int Stars { get; set; }
    public int Forks { get; set; }
    public string? Readme { get; set; }
    public DateTime? PushedAt { get; set; }
    public DateTime? UpdatedAtGitHub { get; set; }
    public bool IsPrivate { get; set; }
    public string DefaultBranch { get; set; } = "main";
    public string Classification { get; set; } = "professional"; // professional, product, ai, saas, etc.
    public string? AiTitle { get; set; }
    public string? AiSummary { get; set; }
    public string? AiProblem { get; set; }
    public string? AiTechStack { get; set; }
    public string AiConfidence { get; set; } = "low"; // low, medium, high
    public string SyncStatus { get; set; } = "review"; // review, published, ignored, hidden
    public DateTime LastSyncedAt { get; set; } = DateTime.UtcNow;
    public bool IsManuallyEdited { get; set; }
    public DateTime? PublishedAt { get; set; }

    public List<string> Topics => JsonSerializer.Deserialize<List<string>>(TopicsJson) ?? new();
    public void SetTopics(List<string> v) => TopicsJson = JsonSerializer.Serialize(v);
}

// ── Product ──
public class Product
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string? LogoUrl { get; set; }
    public string ScreenshotsJson { get; set; } = "[]";
    public string FeaturesJson { get; set; } = "[]";
    public string TechStackJson { get; set; } = "[]";
    public string? AiCapabilities { get; set; }
    public string? Architecture { get; set; }
    public string? ProductUrl { get; set; }
    public string? GitHubRepoId { get; set; }
    public string Status { get; set; } = "draft"; // draft, published, featured
    public bool Featured { get; set; }
    public int DisplayOrder { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public List<string> Screenshots => JsonSerializer.Deserialize<List<string>>(ScreenshotsJson) ?? new();
    public void SetScreenshots(List<string> v) => ScreenshotsJson = JsonSerializer.Serialize(v);
    public List<string> Features => JsonSerializer.Deserialize<List<string>>(FeaturesJson) ?? new();
    public void SetFeatures(List<string> v) => FeaturesJson = JsonSerializer.Serialize(v);
    public List<string> TechStack => JsonSerializer.Deserialize<List<string>>(TechStackJson) ?? new();
    public void SetTechStack(List<string> v) => TechStackJson = JsonSerializer.Serialize(v);
}

public class ProductDto
{
    public string Name { get; set; } = string.Empty;
    public string? Slug { get; set; }
    public string? Category { get; set; }
    public string? Description { get; set; }
    public string? LogoUrl { get; set; }
    public List<string>? Screenshots { get; set; }
    public List<string>? Features { get; set; }
    public List<string>? TechStack { get; set; }
    public string? AiCapabilities { get; set; }
    public string? Architecture { get; set; }
    public string? ProductUrl { get; set; }
    public string? GitHubRepoId { get; set; }
    public string? Status { get; set; }
    public bool? Featured { get; set; }
    public int? DisplayOrder { get; set; }
}

// ── Sync Log ──
public class ProjectSyncLog
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;
    public DateTime? FinishedAt { get; set; }
    public int Found { get; set; }
    public int Added { get; set; }
    public int Updated { get; set; }
    public int Ignored { get; set; }
    public string ErrorsJson { get; set; } = "[]";
    public List<string> Errors => JsonSerializer.Deserialize<List<string>>(ErrorsJson) ?? new();
    public void SetErrors(List<string> v) => ErrorsJson = JsonSerializer.Serialize(v);
}

// ── Website Content ──
public class WebsiteContent
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Key { get; set; } = string.Empty; // e.g. "home_order", "seo_title"
    public string Title { get; set; } = string.Empty;
    public string BodyJson { get; set; } = "{}";
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}

// ── Extended Profile DTO ──
public class ProfileUpdateDto
{
    public string? FullName { get; set; }
    public string? Title { get; set; }
    public string? Bio { get; set; }
    public List<string>? Skills { get; set; }
    public Dictionary<string, string>? SocialLinks { get; set; }
    public List<CareerEntry>? Career { get; set; }
    public string? Headline { get; set; }
    public string? Location { get; set; }
    public string? Phone { get; set; }
    public string? WhatsApp { get; set; }
    public string? Email { get; set; }
    public string? LinkedIn { get; set; }
    public string? GitHub { get; set; }
    public string? Website { get; set; }
    public string? ProfileImageUrl { get; set; }
}

// ── Auth DTOs ──
public class AdminLoginDto
{
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}
