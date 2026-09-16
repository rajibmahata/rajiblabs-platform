"""Tests for the RajibLabs Agent Orchestrator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import (
    AgentRun, AgentRole, RunStatus, RunStep, StepStatus,
    TaskType, QualityGrade, QualityDimension, QualityResult,
    EvidenceSource, ContentImprovement, ContentVersion, ProjectCaseStudy,
)
from app.engine.quality import (
    compute_quality, score_factual_accuracy, score_evidence_coverage,
    score_completeness, score_specificity, score_readability,
    score_technical_depth, score_business_relevance, score_uniqueness,
    QUALITY_DIMENSIONS,
)
from app.engine.content_intelligence import (
    detect_generic_content as detect_generic,
    detect_missing_fields, detect_weak_content,
)


class TestModels:
    def test_run_status_values(self):
        assert RunStatus.QUEUED.value == "queued"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"

    def test_task_type_values(self):
        assert TaskType.CONTENT_IMPROVEMENT.value == "content_improvement"
        assert TaskType.PROJECT_IMPROVEMENT.value == "project_improvement"
        assert TaskType.FULL_AUDIT.value == "full_audit"

    def test_quality_grade_values(self):
        assert QualityGrade.REJECT.value == "reject"
        assert QualityGrade.PUBLISH.value == "publish"

    def test_agent_role_values(self):
        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.PROJECT_INTELLIGENCE.value == "project_intelligence"

    def test_evidence_source(self):
        e = EvidenceSource(source_type="github", source_id="123", content="test", confidence=0.9)
        assert e.source_type == "github"
        assert e.confidence == 0.9

    def test_quality_result(self):
        r = QualityResult(total_score=85.0, grade=QualityGrade.ACCEPTABLE, passed=True)
        assert r.passed is True
        assert r.publishable is False

    def test_content_version(self):
        v = ContentVersion(version=1, content={"title": "Test"}, agent="test_agent")
        assert v.version == 1
        assert v.content["title"] == "Test"

    def test_agent_run(self):
        run = AgentRun(run_id="test_run", task_type=TaskType.CONTENT_AUDIT)
        assert run.run_id == "test_run"
        assert run.status == RunStatus.QUEUED
        assert len(run.steps) == 0


class TestQualityEngine:
    def test_quality_dimensions_defined(self):
        assert len(QUALITY_DIMENSIONS) == 10
        assert "factual_accuracy" in QUALITY_DIMENSIONS
        assert "specificity" in QUALITY_DIMENSIONS

    def test_compute_quality_basic(self):
        content = {"title": "Test Project", "description": "A test project for testing"}
        result = compute_quality(content)
        assert isinstance(result, QualityResult)
        assert result.total_score >= 0
        assert result.grade in QualityGrade

    def test_compute_quality_with_evidence(self):
        content = {"title": "Test", "description": "Test description"}
        evidence = [{"source_type": "github"}, {"source_type": "resume"}, {"source_type": "knowledge"}]
        result = compute_quality(content, evidence=evidence)
        assert result.total_score > 0

    def test_compute_quality_empty(self):
        result = compute_quality({})
        assert result.grade == QualityGrade.REJECT

    def test_score_factual_accuracy_with_evidence(self):
        content = {"title": "Test"}
        evidence = [{"source_type": "github"}]
        dim = score_factual_accuracy(content, evidence)
        assert dim.score > 0

    def test_score_factual_accuracy_no_evidence(self):
        dim = score_factual_accuracy({}, [])
        assert dim.score < 10.0
        assert len(dim.issues) > 0

    def test_score_completeness(self):
        content = {"title": "Test", "description": "Desc"}
        dim = score_completeness(content, ["title", "description", "missing"])
        assert dim.score < 10.0

    def test_score_readability(self):
        dim = score_readability("This is a well-written sentence about the project.")
        assert dim.score > 0

    def test_score_readability_empty(self):
        dim = score_readability("")
        assert dim.score == 0.0


class TestContentIntelligence:
    def test_detect_generic_content(self):
        text = "This is a powerful and innovative solution that provides seamless functionality."
        issues = detect_generic(text)
        assert len(issues) > 0

    def test_detect_generic_content_clean(self):
        text = "The application processes customer orders using a microservices architecture with Redis caching."
        issues = detect_generic(text)
        assert len(issues) == 0

    def test_detect_missing_fields_project(self):
        content = {"title": "Test"}
        missing = detect_missing_fields(content, "project")
        assert "description" in missing
        assert "problem" in missing
        assert "solution" in missing

    def test_detect_missing_fields_complete(self):
        content = {
            "title": "Test", "description": "Desc", "problem": "Problem",
            "solution": "Solution", "role": "Role", "skills": ["Python"],
            "architecture": "Arch", "business_value": "Value",
        }
        missing = detect_missing_fields(content, "project")
        assert len(missing) == 0

    def test_detect_weak_content(self):
        content = {"title": "Test", "description": "Short"}
        weaknesses = detect_weak_content(content, "project")
        assert len(weaknesses) > 0

    def test_detect_weak_content_good(self):
        content = {
            "title": "Test Project",
            "description": "This is a well-written project description that explains the architecture and implementation details clearly.",
            "problem": "The problem this solves is clearly defined and specific for our users.",
            "solution": "The solution uses a microservices architecture with event-driven communication patterns.",
            "role": "Lead developer responsible for backend architecture",
            "skills": ["Python", "FastAPI", "MongoDB"],
            "architecture": "Microservices with event-driven communication",
            "business_value": "Reduced processing time by 40%",
        }
        weaknesses = detect_weak_content(content, "project")
        assert len(weaknesses) == 0


class TestMCPClient:
    def test_client_init(self):
        from app.mcp_client import MCPClient
        client = MCPClient(base_url="http://localhost:8100")
        assert client.base_url == "http://localhost:8100"


class TestOrchestratorModels:
    def test_run_step(self):
        step = RunStep(
            step_id="test",
            agent=AgentRole.CONTENT_QUALITY,
            task="Test task",
            status=StepStatus.RUNNING,
        )
        assert step.status == StepStatus.RUNNING

    def test_content_improvement(self):
        improvement = ContentImprovement(
            entity_type="project",
            entity_id="123",
            before={"title": "Old"},
            after={"title": "New"},
            why_changed="Improved clarity",
        )
        assert improvement.before["title"] == "Old"
        assert improvement.after["title"] == "New"

    def test_project_case_study(self):
        cs = ProjectCaseStudy(
            project_id="123",
            title="Test Project",
            positioning="A test project",
            category="web",
            technologies=["Python", "FastAPI"],
        )
        assert cs.title == "Test Project"
        assert len(cs.technologies) == 2
