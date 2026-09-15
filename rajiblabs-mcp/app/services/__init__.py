"""MCP service layer — business logic for MCP tools."""

# Services are thin wrappers that can be imported by both MCP tools
# and the existing backend agents. This creates the controlled interface:
#   Agent → MCP Tool → Service → MongoDB

# Service modules are imported by the tool modules directly.
# This package exists to allow future service-level abstractions.
