from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    PROPOSE = "propose"
    WRITE = "write"
    PUBLISH = "publish"
    DELETE = "delete"


ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "public_agent": [Permission.READ],
    "learning_agent": [Permission.READ, Permission.ANALYZE],
    "marketing_agent": [Permission.READ, Permission.ANALYZE, Permission.WRITE],
    "proposal_agent": [Permission.READ, Permission.ANALYZE, Permission.PROPOSE],
    "profile_manager": [
        Permission.READ,
        Permission.ANALYZE,
        Permission.WRITE,
        Permission.PUBLISH,
    ],
    "admin": [
        Permission.READ,
        Permission.ANALYZE,
        Permission.PROPOSE,
        Permission.WRITE,
        Permission.PUBLISH,
        Permission.DELETE,
    ],
}

TOOL_PERMISSIONS: dict[str, Permission] = {
    "get_profile": Permission.READ,
    "get_about": Permission.READ,
    "get_professional_positioning": Permission.READ,
    "get_profile_completeness": Permission.READ,
    "analyze_profile": Permission.ANALYZE,
    "validate_profile": Permission.ANALYZE,
    "optimize_profile": Permission.PROPOSE,
    "update_profile": Permission.WRITE,
    "list_resumes": Permission.READ,
    "get_resume": Permission.READ,
    "analyze_resume": Permission.ANALYZE,
    "extract_resume_experience": Permission.ANALYZE,
    "extract_resume_skills": Permission.ANALYZE,
    "extract_resume_projects": Permission.ANALYZE,
    "compare_resume_versions": Permission.ANALYZE,
    "sync_resume_to_knowledge": Permission.WRITE,
    "list_projects": Permission.READ,
    "get_project": Permission.READ,
    "analyze_project": Permission.ANALYZE,
    "improve_project": Permission.PROPOSE,
    "validate_project": Permission.ANALYZE,
    "detect_project_gaps": Permission.ANALYZE,
    "discover_project_relationships": Permission.ANALYZE,
    "update_project": Permission.WRITE,
    "get_portfolio": Permission.READ,
    "analyze_portfolio": Permission.ANALYZE,
    "rank_projects": Permission.ANALYZE,
    "select_featured_projects": Permission.ANALYZE,
    "improve_portfolio": Permission.PROPOSE,
    "validate_portfolio": Permission.ANALYZE,
    "update_portfolio": Permission.WRITE,
    "list_products": Permission.READ,
    "get_product": Permission.READ,
    "analyze_product": Permission.ANALYZE,
    "improve_product": Permission.PROPOSE,
    "validate_product": Permission.ANALYZE,
    "update_product": Permission.WRITE,
    "relate_product_to_projects": Permission.WRITE,
    "relate_product_to_skills": Permission.WRITE,
    "discover_skills": Permission.ANALYZE,
    "normalize_skill": Permission.ANALYZE,
    "validate_skill": Permission.ANALYZE,
    "get_skill_evidence": Permission.READ,
    "link_skill_to_project": Permission.WRITE,
    "link_skill_to_repository": Permission.WRITE,
    "link_skill_to_resume": Permission.WRITE,
    "get_skill_relationships": Permission.READ,
    "list_repositories": Permission.READ,
    "get_repository": Permission.READ,
    "analyze_repository": Permission.ANALYZE,
    "discover_projects_from_repository": Permission.ANALYZE,
    "discover_skills_from_repository": Permission.ANALYZE,
    "discover_technologies_from_repository": Permission.ANALYZE,
    "sync_repository": Permission.WRITE,
    "validate_repository": Permission.ANALYZE,
    "search_knowledge": Permission.READ,
    "get_knowledge": Permission.READ,
    "find_related_knowledge": Permission.READ,
    "validate_knowledge": Permission.ANALYZE,
    "index_knowledge": Permission.WRITE,
    "reindex_document": Permission.WRITE,
    "get_source_evidence": Permission.READ,
    "analyze_content": Permission.ANALYZE,
    "detect_missing_information": Permission.ANALYZE,
    "detect_duplicate_content": Permission.ANALYZE,
    "detect_conflicts": Permission.ANALYZE,
    "detect_outdated_content": Permission.ANALYZE,
    "improve_content": Permission.PROPOSE,
    "validate_content": Permission.ANALYZE,
    "compare_content_versions": Permission.ANALYZE,
    "generate_content_summary": Permission.ANALYZE,
    "analyze_seo": Permission.ANALYZE,
    "generate_metadata": Permission.PROPOSE,
    "validate_metadata": Permission.ANALYZE,
    "find_missing_metadata": Permission.ANALYZE,
    "find_internal_link_opportunities": Permission.ANALYZE,
    "check_internal_links": Permission.ANALYZE,
    "check_broken_links": Permission.ANALYZE,
    "analyze_headings": Permission.ANALYZE,
    "analyze_images": Permission.ANALYZE,
    "analyze_content_quality": Permission.ANALYZE,
    "validate_canonical": Permission.ANALYZE,
    "validate_sitemap": Permission.ANALYZE,
    "rollback_content": Permission.DELETE,
    "detect_missing_translations": Permission.ANALYZE,
    "generate_translation": Permission.WRITE,
    "validate_translation": Permission.ANALYZE,
    "sync_translations": Permission.WRITE,
    "preview_content": Permission.READ,
    "publish_content": Permission.PUBLISH,
    "unpublish_content": Permission.PUBLISH,
    "system_health": Permission.READ,
    "system_agent_status": Permission.READ,
    "system_rag_status": Permission.READ,
    "system_cache_status": Permission.READ,
    "system_mcp_status": Permission.READ,
}


def has_permission(role: str, tool_name: str) -> bool:
    required = TOOL_PERMISSIONS.get(tool_name, Permission.READ)
    perms = ROLE_PERMISSIONS.get(role, [])
    return required in perms


def get_role_permissions(role: str) -> list[Permission]:
    return ROLE_PERMISSIONS.get(role, [])
