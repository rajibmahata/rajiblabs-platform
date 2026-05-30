namespace RajibLabs.Api.Models;

public class Project
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public List<string> TechStack { get; set; } = new();
    public string GitHubUrl { get; set; } = string.Empty;
    public string? LiveUrl { get; set; }
    public string Status { get; set; } = "planning"; // planning, development, qa, deployed
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastCommitAt { get; set; }
}

public class Activity
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ProjectId { get; set; }
    public string Type { get; set; } = "commit"; // commit, deploy, milestone, blog
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

public class Profile
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string FullName { get; set; } = "Rajib Mahata";
    public string Title { get; set; } = "Senior Software Architect | AI & SaaS Platform Builder";
    public string Bio { get; set; } = string.Empty;
    public List<string> Skills { get; set; } = new();
    public Dictionary<string, string> SocialLinks { get; set; } = new();
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
