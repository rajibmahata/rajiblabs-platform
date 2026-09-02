using Microsoft.EntityFrameworkCore;
using RajibLabs.Api.Models;

namespace RajibLabs.Api.Data;

public class LabDbContext : DbContext
{
    public LabDbContext(DbContextOptions<LabDbContext> options) : base(options) { }

    public DbSet<Project> Projects => Set<Project>();
    public DbSet<Activity> Activities => Set<Activity>();
    public DbSet<Profile> Profiles => Set<Profile>();
    public DbSet<Contact> Contacts => Set<Contact>();
    public DbSet<LinkedInCourse> LinkedInCourses => Set<LinkedInCourse>();
    public DbSet<Subscriber> Subscribers => Set<Subscriber>();
    public DbSet<AdminUser> AdminUsers => Set<AdminUser>();
    public DbSet<Resume> Resumes => Set<Resume>();
    public DbSet<ResumeExtraction> ResumeExtractions => Set<ResumeExtraction>();
    public DbSet<PortfolioProject> PortfolioProjects => Set<PortfolioProject>();
    public DbSet<GitHubRepository> GitHubRepositories => Set<GitHubRepository>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<ProjectSyncLog> ProjectSyncLogs => Set<ProjectSyncLog>();
    public DbSet<WebsiteContent> WebsiteContents => Set<WebsiteContent>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // CareerEntry is stored as JSON in Profile — not a separate entity
        modelBuilder.Ignore<CareerEntry>();

        modelBuilder.Entity<Project>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Title).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Slug).HasMaxLength(200);
            entity.HasIndex(e => e.Slug).IsUnique();
        });

        modelBuilder.Entity<Activity>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Title).HasMaxLength(500);
        });

        modelBuilder.Entity<Profile>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.FullName).HasMaxLength(200);
            entity.Property(e => e.Title).HasMaxLength(200);
        });

        modelBuilder.Entity<Contact>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Email).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Company).HasMaxLength(200);
            entity.Property(e => e.Message).IsRequired().HasMaxLength(5000);
        });

        modelBuilder.Entity<LinkedInCourse>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Title).IsRequired().HasMaxLength(500);
            entity.Property(e => e.Url).HasMaxLength(1000);
            entity.Property(e => e.Instructor).HasMaxLength(200);
            entity.Property(e => e.Duration).HasMaxLength(50);
            entity.Property(e => e.Level).HasMaxLength(50);
            entity.Property(e => e.Status).HasMaxLength(50);
            entity.HasIndex(e => e.Url).IsUnique();
        });

        modelBuilder.Entity<Subscriber>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Email).IsRequired().HasMaxLength(200);
            entity.HasIndex(e => e.Email).IsUnique();
        });

        modelBuilder.Entity<AdminUser>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Username).IsRequired().HasMaxLength(100);
            entity.HasIndex(e => e.Username).IsUnique();
        });

        modelBuilder.Entity<Resume>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.FileName).HasMaxLength(300);
            entity.Property(e => e.StoredPath).HasMaxLength(500);
        });

        modelBuilder.Entity<PortfolioProject>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Title).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Slug).HasMaxLength(200);
            entity.HasIndex(e => e.Slug).IsUnique();
        });

        modelBuilder.Entity<GitHubRepository>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.GitHubId).IsUnique();
            entity.HasIndex(e => e.FullName).IsUnique();
        });

        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Slug).HasMaxLength(200);
            entity.HasIndex(e => e.Slug).IsUnique();
        });

        modelBuilder.Entity<WebsiteContent>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Key).IsRequired().HasMaxLength(100);
            entity.HasIndex(e => e.Key).IsUnique();
        });
    }
}
