namespace RajibLabs.Api.Models;

public class Project
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string TechStackJson { get; set; } = "[]"; // JSON array
    public string GitHubUrl { get; set; } = string.Empty;
    public string? LiveUrl { get; set; }
    public string Status { get; set; } = "planning";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastCommitAt { get; set; }

    // Frontend-friendly projection (not mapped)
    public List<string> TechStack => System.Text.Json.JsonSerializer.Deserialize<List<string>>(TechStackJson) ?? new();
    public void SetTechStack(List<string> techs) =>
        TechStackJson = System.Text.Json.JsonSerializer.Serialize(techs);
}

public class Activity
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ProjectId { get; set; }
    public string Type { get; set; } = "commit";
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

// ── Request DTOs ──

public class ActivityDto
{
    public Guid ProjectId { get; set; }
    public string? Type { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public DateTime? Timestamp { get; set; }
    public DateTime? CommittedAt { get; set; }
}

public class ProjectPatchDto
{
    public DateTime? LastCommitAt { get; set; }
    public string? Status { get; set; }
    public string? Title { get; set; }
    public string? Description { get; set; }
}

public class Profile
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string FullName { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Bio { get; set; } = string.Empty;
    public string SkillsJson { get; set; } = "[]";
    public string SocialLinksJson { get; set; } = "{}";
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Frontend-friendly projections
    public List<string> Skills => System.Text.Json.JsonSerializer.Deserialize<List<string>>(SkillsJson) ?? new();
    public Dictionary<string, string> SocialLinks => System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, string>>(SocialLinksJson) ?? new();
    public void SetSkills(List<string> skills) =>
        SkillsJson = System.Text.Json.JsonSerializer.Serialize(skills);
    public void SetSocialLinks(Dictionary<string, string> links) =>
        SocialLinksJson = System.Text.Json.JsonSerializer.Serialize(links);
}
