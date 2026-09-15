"""RajibLabs MCP Content Intelligence Platform.

A reusable, Dockerized MCP (Model Context Protocol) layer that allows
RajibLabs agents to intelligently manage, validate, organize, refine,
and continuously improve profile, portfolio, projects, products, skills,
GitHub knowledge, SEO content, and RAG knowledge.

Architecture:
  MongoDB = Source of Truth
  Qdrant = Retrieval Layer
  MCP = Controlled Tool Interface
  Agents = Reasoning + Orchestration
"""
