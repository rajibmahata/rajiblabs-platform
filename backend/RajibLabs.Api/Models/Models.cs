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
    public string CareerJson { get; set; } = "[]"; // JSON array of career entries
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    // Extended CMS fields
    public string? Headline { get; set; }
    public string? Location { get; set; }
    public string? Phone { get; set; }
    public string? WhatsApp { get; set; }
    public string? Email { get; set; }
    public string? LinkedIn { get; set; }
    public string? GitHub { get; set; }
    public string? Website { get; set; }
    public string? ProfileImageUrl { get; set; }

    // Frontend-friendly projections
    public List<string> Skills => System.Text.Json.JsonSerializer.Deserialize<List<string>>(SkillsJson) ?? new();
    public Dictionary<string, string> SocialLinks => System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, string>>(SocialLinksJson) ?? new();
    public List<CareerEntry> Career => System.Text.Json.JsonSerializer.Deserialize<List<CareerEntry>>(CareerJson) ?? new();
    public void SetSkills(List<string> skills) =>
        SkillsJson = System.Text.Json.JsonSerializer.Serialize(skills);
    public void SetSocialLinks(Dictionary<string, string> links) =>
        SocialLinksJson = System.Text.Json.JsonSerializer.Serialize(links);
    public void SetCareer(List<CareerEntry> entries) =>
        CareerJson = System.Text.Json.JsonSerializer.Serialize(entries);
}

public class CareerEntry
{
    public string Company { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public string Period { get; set; } = string.Empty;
    public string Client { get; set; } = string.Empty;
    public List<string> Achievements { get; set; } = new();
    public List<string> TechStack { get; set; } = new();
    public string Color { get; set; } = string.Empty;
}

// ── Contact ──

public class Contact
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Company { get; set; }
    public string Message { get; set; } = string.Empty;
    public DateTime SubmittedAt { get; set; } = DateTime.UtcNow;
}

public class ContactDto
{
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Company { get; set; }
    public string Message { get; set; } = string.Empty;
}

// ── LinkedIn Learning ──

public class LinkedInCourse
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Title { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public string? Instructor { get; set; }
    public string? Duration { get; set; }
    public string? Level { get; set; }
    public DateTime? CompletedAt { get; set; }
    public string Status { get; set; } = "in-progress"; // in-progress, completed
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}

public class LinkedInCourseDto
{
    public string Title { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public string? Instructor { get; set; }
    public string? Duration { get; set; }
    public string? Level { get; set; }
    public DateTime? CompletedAt { get; set; }
    public string? Status { get; set; }
}

// ── Subscriber ──

public class Subscriber
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Email { get; set; } = string.Empty;
    public bool IsActive { get; set; } = true;
    public DateTime SubscribedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UnsubscribedAt { get; set; }
}

public class SubscriberDto
{
    public string Email { get; set; } = string.Empty;
}
