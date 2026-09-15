from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys
from app.cache import cache_get, cache_set
from app.versioning import create_version, record_change
from app.relationships import add_relationship

logger = logging.getLogger(__name__)


@mcp_tool(
    name="list_products",
    description="List all RajibLabs products.",
    category="product",
    permission="read",
)
async def list_products(agent_id: str = "anonymous") -> dict:
    cached = await cache_get("products", "list")
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    products = []
    async for prod in db.products.find():
        prod["_id"] = _oid_str(prod["_id"])
        prod = _clean_secret_keys(prod)
        products.append(prod)

    result = {"products": products, "count": len(products)}
    await cache_set("products", "list", result)
    return {"success": True, "data": result, "sources": ["products"], "confidence": 1.0}


@mcp_tool(
    name="get_product",
    description="Get a specific product by ID.",
    category="product",
    permission="read",
)
async def get_product(product_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Product not found"}}

    product["_id"] = _oid_str(product["_id"])
    product = _clean_secret_keys(product)
    return {"success": True, "data": product, "sources": ["products"], "confidence": 1.0}


@mcp_tool(
    name="analyze_product",
    description="Analyze product completeness and quality.",
    category="product",
    permission="analyze",
)
async def analyze_product(product_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Product not found"}}

    fields = ["title", "description", "short_description", "tech_stack", "features", "image", "github_url", "live_url", "category"]
    filled = sum(1 for f in fields if product.get(f))
    score = (filled / len(fields)) * 100 if fields else 0

    return {
        "success": True,
        "data": {"product_id": product_id, "score": round(score, 1), "filled": filled, "total": len(fields)},
        "sources": ["products"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="improve_product",
    description="Suggest improvements for a product.",
    category="product",
    permission="propose",
)
async def improve_product(product_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Product not found"}}

    suggestions = []
    if not product.get("description") or len(product.get("description", "")) < 100:
        suggestions.append({"field": "description", "priority": "high", "suggestion": "Expand product description"})
    if not product.get("features"):
        suggestions.append({"field": "features", "priority": "high", "suggestion": "Add feature list"})
    if not product.get("tech_stack"):
        suggestions.append({"field": "tech_stack", "priority": "medium", "suggestion": "Add technology stack"})
    if not product.get("image"):
        suggestions.append({"field": "image", "priority": "medium", "suggestion": "Add product image"})

    return {"success": True, "data": {"product_id": product_id, "suggestions": suggestions}, "sources": ["products"], "confidence": 0.85}


@mcp_tool(
    name="validate_product",
    description="Validate product for completeness and consistency.",
    category="product",
    permission="analyze",
)
async def validate_product(product_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Product not found"}}

    issues = []
    warnings = []
    if not product.get("title"):
        issues.append("Missing title")
    if not product.get("description"):
        issues.append("Missing description")

    return {
        "success": True,
        "data": {"product_id": product_id, "valid": len(issues) == 0, "issues": issues, "warnings": warnings},
        "sources": ["products"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="update_product",
    description="Update a product with new content. Creates version snapshot.",
    category="product",
    permission="write",
)
async def update_product(
    product_id: str, updates: dict, reason: str = "", agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Product not found"}}

    before = {k: v for k, v in product.items() if k != "_id"}
    await create_version("product", product_id, before, agent_id, reason or "Product update")

    allowed = {"title", "description", "short_description", "tech_stack", "features", "image", "github_url", "live_url", "category", "status"}
    safe = {k: v for k, v in updates.items() if k in allowed}
    await db.products.update_one({"_id": ObjectId(product_id)}, {"$set": safe})

    await record_change("product", product_id, "update", before, safe, agent_id, reason)

    return {"success": True, "data": {"product_id": product_id, "updated_fields": list(safe.keys())}, "sources": ["products"], "changed": True, "confidence": 1.0}


@mcp_tool(
    name="relate_product_to_projects",
    description="Link a product to related projects.",
    category="product",
    permission="write",
)
async def relate_product_to_projects(
    product_id: str, project_ids: list[str], agent_id: str = "anonymous"
) -> dict:
    added = 0
    for pid in project_ids:
        result = await add_relationship("product", product_id, "project", pid, "related_to")
        if result:
            added += 1

    return {"success": True, "data": {"product_id": product_id, "linked_projects": added}, "sources": ["content_relationships"], "confidence": 0.9}


@mcp_tool(
    name="relate_product_to_skills",
    description="Link a product to relevant skills.",
    category="product",
    permission="write",
)
async def relate_product_to_skills(
    product_id: str, skill_ids: list[str], agent_id: str = "anonymous"
) -> dict:
    added = 0
    for sid in skill_ids:
        result = await add_relationship("product", product_id, "skill", sid, "uses_skill")
        if result:
            added += 1

    return {"success": True, "data": {"product_id": product_id, "linked_skills": added}, "sources": ["content_relationships"], "confidence": 0.9}
