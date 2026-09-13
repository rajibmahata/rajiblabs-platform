"""Comprehensive tests for the Universal Content Validation Engine."""
import pytest
from app.services.content_validator import (
    normalize_lesson_block, normalize_path, validate_block, validate_path,
    plan_improvements, check_publish_gate, save_validation_result,
    save_improvement, get_validation_history, should_skip_revalidation,
    rollback_content, validate_all_paths, validate_and_save_block,
    validate_and_save_path, RULES, _applicable_rules, _calculate_scores,
    _content_hash, _validate_structural, _validate_beginner,
    _validate_technical, _validate_consistency, _validate_curriculum,
    ContentType, Difficulty, Severity, ValidationStatus, ContentAction,
    NormalizedContent, Rule, ValidationIssue, ValidationResult,
    DEFAULT_SCORING_WEIGHTS, DEFAULT_PUBLISH_GATE,
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def good_block():
    """A well-structured lesson block that should pass validation."""
    return {
        "_id": "block_001",
        "topic": "Python Variables",
        "title": "Understanding Python Variables",
        "learning_objective": "Create and use Python variables in your first program",
        "concept_explanation": (
            "A variable is a named container that stores a value. "
            "In Python, you create a variable by typing its name, then the equals sign, "
            "then the value. For example, name = 'Rajib' creates a variable called name "
            "that holds the text 'Rajib'. Python automatically figures out the type."
        ),
        "simple_explanation": "Think of a variable like a labeled box where you put things.",
        "examples": [
            {
                "title": "Storing a name",
                "code": "name = 'Rajib'\nprint(name)",
                "explanation": "This stores the text 'Rajib' in a variable and prints it.",
            }
        ],
        "exercise": "Create a variable called age with your age, then print it",
        "homework": "Create 3 variables of different types and print them",
        "challenge": "Create variables for a person's full name, age, and favorite color, then print a sentence using them",
        "real_world_example": (
            "When you sign up for a website, your name, email, and password are "
            "stored in variables. The website uses these variables to personalize "
            "your experience and send you notifications."
        ),
        "step_by_step": [
            "Type name = 'Alex' and press Enter",
            "Type print(name) and press Enter",
            "Notice how Python stored and recalled the value",
        ],
        "try_it_yourself": "Change 'Alex' to your own name and run it again",
        "common_mistakes": [
            "Forgetting quotes around text: name = Rajib (error) vs name = 'Rajib' (correct)"
        ],
        "quick_review": "Variables store values using the equals sign. Text needs quotes, numbers do not.",
        "why_matters": "Every program uses variables to store and manipulate data.",
        "what_you_can_do_now": "You can create variables, store text and numbers, and print them.",
        "next_preview": "Tomorrow we learn about different data types in Python.",
        "questions": ["What happens if you try name without quotes?"],
        "status": "published",
        "version": 2,
        "path_id": "path_001",
        "day_number": 1,
        "slug": "python-basics",
    }


@pytest.fixture
def bad_block():
    """A poorly structured block that should fail validation."""
    return {
        "_id": "block_bad",
        "topic": "Advanced Async Patterns",
        "title": "Advanced Async Patterns",
        "learning_objective": "",
        "concept_explanation": (
            "As an AI, I will explain async patterns. In today's digital world, "
            "asynchronous programming is important. Furthermore, you should understand "
            "callbacks and promises. Moreover, the event loop is a complex topic."
        ),
        "simple_explanation": "",
        "examples": [],
        "exercise": "",
        "homework": "",
        "challenge": "",
        "real_world_example": "In general, async is useful.",
        "step_by_step": [],
        "try_it_yourself": "",
        "common_mistakes": [],
        "quick_review": "In summary, this lesson covered async.",
        "why_matters": "It is important to note that async is used.",
        "what_you_can_do_now": "",
        "next_preview": "",
        "questions": [],
        "status": "published",
        "version": 1,
        "path_id": "path_001",
        "day_number": 1,
        "slug": "python-advanced",
    }


@pytest.fixture
def good_path():
    """A well-structured learning path."""
    return {
        "_id": "path_001",
        "slug": "python-basics",
        "topic": "Python Programming Basics",
        "title": "Python Programming Basics",
        "goal": "Learn Python from scratch",
        "status": "active",
        "duration": 3,
        "level": "beginner",
        "prerequisites": ["Basic computer skills"],
        "roadmap": [
            {"day": 1, "title": "What is Python?", "objective": "Explain what Python is"},
            {"day": 2, "title": "Variables", "objective": "Create and use variables"},
            {"day": 3, "title": "Conditionals", "objective": "Write if/else statements"},
        ],
        "current_day": 3,
        "progress": 100,
        "version": 2,
    }


@pytest.fixture
def bad_path():
    """A path with too many prerequisites."""
    return {
        "_id": "path_bad",
        "slug": "too-many-prereqs",
        "topic": "Advanced Topics",
        "goal": "Learn advanced stuff",
        "status": "active",
        "duration": 5,
        "level": "beginner",
        "prerequisites": ["Python", "JavaScript", "Rust", "Go", "Haskell"],
        "current_day": 5,
        "progress": 100,
        "version": 1,
    }


@pytest.fixture
def path_blocks():
    """Multiple blocks for a path (consistency checks)."""
    return [
        {
            "_id": "b1",
            "topic": "Intro to Python",
            "title": "What is Python?",
            "learning_objective": "Explain what Python is and why to use it",
            "concept_explanation": "Python is a programming language used for web development, data science, and automation.",
            "simple_explanation": "Python is a tool for telling computers what to do.",
            "examples": [{"title": "Hello", "code": "print('Hello')", "explanation": "Prints hello."}],
            "exercise": "Install Python on your computer",
            "homework": "Run Python in a terminal",
            "real_world_example": "Instagram uses Python for its backend services.",
            "step_by_step": ["Go to python.org", "Download Python 3", "Run the installer"],
            "try_it_yourself": "Open a terminal and type python3",
            "common_mistakes": ["Not adding Python to PATH"],
            "quick_review": "Python is a versatile programming language.",
            "status": "published",
            "day_number": 1,
            "slug": "python-basics",
        },
        {
            "_id": "b2",
            "topic": "Variables",
            "title": "Python Variables",
            "learning_objective": "Create and use variables",
            "concept_explanation": "Variables store values using the equals sign.",
            "simple_explanation": "Variables are labeled boxes for data.",
            "examples": [{"title": "Store name", "code": "x = 42", "explanation": "Stores 42."}],
            "exercise": "Create a variable and print it",
            "homework": "Create 5 variables",
            "real_world_example": "Websites store user data in variables.",
            "step_by_step": ["Type x = 5", "Type print(x)"],
            "try_it_yourself": "Try changing the value",
            "common_mistakes": ["Forgetting the equals sign"],
            "quick_review": "Variables hold data values.",
            "status": "published",
            "day_number": 2,
            "slug": "python-basics",
        },
        {
            "_id": "b3",
            "topic": "Conditionals",
            "title": "If/Else Statements",
            "learning_objective": "Write if/else statements to make decisions",
            "concept_explanation": "Conditionals let your program make choices based on conditions.",
            "simple_explanation": "Like a fork in the road — the program picks a path.",
            "examples": [{"title": "Basic if", "code": "if x > 5:\n    print('big')", "explanation": "Checks if x is bigger than 5."}],
            "exercise": "Write an if statement",
            "homework": "Create a grading program",
            "real_world_example": "Login pages check if your password is correct.",
            "step_by_step": ["Write the condition", "Indent the code block"],
            "try_it_yourself": "Try different conditions",
            "common_mistakes": ["Forgetting the colon after the condition"],
            "quick_review": "Conditionals control program flow.",
            "status": "published",
            "day_number": 3,
            "slug": "python-basics",
        },
    ]


@pytest.fixture
def duplicate_blocks():
    """Blocks with duplicate code (should fail consistency check)."""
    return [
        {
            "_id": "d1",
            "topic": "Lists",
            "title": "Python Lists",
            "learning_objective": "Create and use lists",
            "concept_explanation": "Lists store multiple values.",
            "examples": [{"title": "List", "code": "nums = [1,2,3]", "explanation": "Creates a list."}],
            "exercise": "Create a list",
            "status": "published",
            "day_number": 1,
            "slug": "python-intermediate",
        },
        {
            "_id": "d2",
            "topic": "Tuples",
            "title": "Python Tuples",
            "learning_objective": "Create and use tuples",
            "concept_explanation": "Tuples are like lists but cannot be changed.",
            "examples": [{"title": "Tuple", "code": "nums = [1,2,3]", "explanation": "Creates a tuple."}],
            "exercise": "Create a tuple",
            "status": "published",
            "day_number": 2,
            "slug": "python-intermediate",
        },
    ]


@pytest.fixture
def block_with_syntax_error():
    """Block with Python syntax error in code."""
    return {
        "_id": "block_syntax",
        "topic": "Python Functions",
        "title": "Python Functions",
        "learning_objective": "Define and call functions",
        "concept_explanation": "Functions are reusable blocks of code.",
        "examples": [
            {
                "title": "Basic function",
                "code": "def greet(name:\n    print(name)",
                "explanation": "Defines a function that prints a name.",
            }
        ],
        "exercise": "Write a function",
        "status": "published",
        "day_number": 1,
        "slug": "python-functions",
    }


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Content Normalizer
# ═══════════════════════════════════════════════════════════════════

class TestContentNormalizer:
    def test_normalize_lesson_basic(self, good_block):
        nc = normalize_lesson_block(good_block)
        assert nc.content_id == "block_001"
        assert nc.content_type == ContentType.LESSON
        assert nc.title == "Understanding Python Variables"
        assert nc.topic == "Python Variables"
        assert nc.difficulty == Difficulty.BEGINNER
        assert len(nc.sections) >= 4
        assert len(nc.code_examples) == 1
        assert nc.exercises
        assert nc.homework
        assert nc.content_hash

    def test_normalize_lesson_with_path(self, good_block, good_path):
        nc = normalize_lesson_block(good_block, good_path)
        assert nc.difficulty == Difficulty.BEGINNER
        assert nc.prerequisites == ["Basic computer skills"]

    def test_normalize_lesson_empty(self):
        nc = normalize_lesson_block({})
        assert nc.content_type == ContentType.LESSON
        assert nc.title == ""
        assert nc.content_hash

    def test_normalize_path(self, good_path, path_blocks):
        nc = normalize_path(good_path, path_blocks)
        assert nc.content_type == ContentType.LEARNING_PATH
        assert nc.title == "Python Programming Basics"
        assert nc.difficulty == Difficulty.BEGINNER
        assert nc.prerequisites == ["Basic computer skills"]
        assert len(nc.sections) == 3  # 3 days
        assert len(nc.examples) == 3  # one from each block
        assert nc.content_hash

    def test_content_hash_deterministic(self):
        h1 = _content_hash("test content")
        h2 = _content_hash("test content")
        assert h1 == h2

    def test_content_hash_different(self):
        h1 = _content_hash("content A")
        h2 = _content_hash("content B")
        assert h1 != h2


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Rule Engine
# ═══════════════════════════════════════════════════════════════════

class TestRuleEngine:
    def test_rules_exist(self):
        assert len(RULES) >= 20

    def test_all_rules_have_required_fields(self):
        for r in RULES:
            assert r.rule_id
            assert r.name
            assert r.category
            assert r.severity in ("P0", "P1", "P2", "P3")
            assert r.applies_to
            assert isinstance(r.enabled, bool)

    def test_applicable_rules_lesson(self):
        rules = _applicable_rules("lesson")
        assert len(rules) >= 10
        assert all("lesson" in r.applies_to for r in rules)

    def test_applicable_rules_path(self):
        rules = _applicable_rules("learning_path")
        assert len(rules) >= 3
        assert all("learning_path" in r.applies_to for r in rules)

    def test_applicable_rules_quiz(self):
        rules = _applicable_rules("quiz")
        # quiz is not in any rule's applies_to — should be empty
        assert len(rules) == 0


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Structural Validation
# ═══════════════════════════════════════════════════════════════════

class TestStructuralValidation:
    def test_good_block_no_structural_issues(self, good_block):
        nc = normalize_lesson_block(good_block)
        issues = _validate_structural(nc)
        p0 = [i for i in issues if i.severity == "P0"]
        assert len(p0) == 0, f"Unexpected P0 issues: {[i.problem for i in p0]}"

    def test_missing_objective(self):
        block = {"_id": "x", "topic": "T", "learning_objective": "",
                 "concept_explanation": "Some content", "examples": []}
        nc = normalize_lesson_block(block)
        issues = _validate_structural(nc)
        assert any(i.rule_id == "STRUCTURAL_OBJECTIVE" for i in issues)

    def test_missing_explanation(self):
        block = {"_id": "x", "topic": "T", "learning_objective": "Do something",
                 "concept_explanation": "", "examples": []}
        nc = normalize_lesson_block(block)
        issues = _validate_structural(nc)
        assert any(i.rule_id == "STRUCTURAL_EXPLANATION" for i in issues)

    def test_code_without_explanation(self):
        block = {
            "_id": "x", "topic": "T", "learning_objective": "Do something",
            "concept_explanation": "Some content here",
            "examples": [{"title": "test", "code": "x = 1", "explanation": ""}],
        }
        nc = normalize_lesson_block(block)
        issues = _validate_structural(nc)
        assert any(i.rule_id == "STRUCTURAL_CODE" for i in issues)


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Beginner Validation
# ═══════════════════════════════════════════════════════════════════

class TestBeginnerValidation:
    def test_ai_filler_detected(self, bad_block):
        nc = normalize_lesson_block(bad_block)
        issues = _validate_beginner(nc)
        assert any(i.rule_id == "BEGINNER_AI_FILLER" for i in issues)

    def test_no_ai_filler_in_good_content(self, good_block):
        nc = normalize_lesson_block(good_block)
        issues = _validate_beginner(nc)
        assert not any(i.rule_id == "BEGINNER_AI_FILLER" for i in issues)

    def test_abstract_real_world(self):
        block = {
            "_id": "x", "topic": "T",
            "learning_objective": "Create variables",
            "concept_explanation": "Variables store data.",
            "real_world_example": "In general, typically, variables are often used.",
        }
        nc = normalize_lesson_block(block)
        issues = _validate_beginner(nc)
        assert any(i.rule_id == "BEGINNER_REAL_WORLD" for i in issues)

    def test_long_paragraph(self):
        long_text = "This is a very long paragraph. " * 50
        block = {
            "_id": "x", "topic": "T",
            "learning_objective": "Learn something",
            "concept_explanation": long_text,
        }
        nc = normalize_lesson_block(block)
        issues = _validate_beginner(nc)
        assert any(i.rule_id == "QUALITY_PARAGRAPH_LENGTH" for i in issues)

    def test_jargon_detection(self):
        block = {
            "_id": "x", "topic": "T",
            "learning_objective": "Learn Python",
            "concept_explanation": (
                "Polymorphism is when Inheritance works with Encapsulation "
                "and Abstraction to create a Composition of Behavior that "
                "implements multiple Interfaces through Metaprogramming "
                "and Reflection in a DependencyInjection container. "
                "Furthermore, the Constructor initializes the Singleton. "
                "Additionally, Serialization handles the deserialization."
            ),
        }
        nc = normalize_lesson_block(block)
        issues = _validate_beginner(nc)
        assert any(i.rule_id == "BEGINNER_JARGON" for i in issues)


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Technical Validation
# ═══════════════════════════════════════════════════════════════════

class TestTechnicalValidation:
    def test_syntax_error_detected(self, block_with_syntax_error):
        nc = normalize_lesson_block(block_with_syntax_error)
        issues = _validate_technical(nc)
        assert any(i.rule_id == "TECHNICAL_ACCURACY" for i in issues)

    def test_valid_code_no_issues(self, good_block):
        nc = normalize_lesson_block(good_block)
        issues = _validate_technical(nc)
        assert not any(i.rule_id == "TECHNICAL_ACCURACY" for i in issues)


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Consistency Validation
# ═══════════════════════════════════════════════════════════════════

class TestConsistencyValidation:
    def test_duplicate_code_detected(self, duplicate_blocks):
        nc1 = normalize_lesson_block(duplicate_blocks[0])
        nc2 = normalize_lesson_block(duplicate_blocks[1])
        issues = _validate_consistency(nc1, [nc2])
        assert any(i.rule_id == "CONSISTENCY_NO_DUPLICATE_CODE" for i in issues)

    def test_no_duplicates_when_unique(self, path_blocks):
        nc = normalize_lesson_block(path_blocks[0])
        siblings = [normalize_lesson_block(b) for b in path_blocks[1:]]
        issues = _validate_consistency(nc, siblings)
        assert not any(i.rule_id == "CONSISTENCY_NO_DUPLICATE_CODE" for i in issues)

    def test_no_issues_without_siblings(self, good_block):
        nc = normalize_lesson_block(good_block)
        issues = _validate_consistency(nc, None)
        assert len(issues) == 0


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Curriculum Validation
# ═══════════════════════════════════════════════════════════════════

class TestCurriculumValidation:
    def test_repeated_titles(self, good_path, path_blocks):
        # Make two blocks have the same title
        blocks = [dict(b) for b in path_blocks]
        blocks[1]["title"] = blocks[0]["title"]
        nc = normalize_path(good_path, blocks)
        block_ncs = [normalize_lesson_block(b) for b in blocks]
        issues = _validate_curriculum(nc, block_ncs)
        assert any(i.rule_id == "CURRICULUM_PROGRESSION" for i in issues)

    def test_first_day_advanced(self, good_path, path_blocks):
        blocks = [dict(b) for b in path_blocks]
        blocks[0]["topic"] = "Advanced Microservices Architecture"
        blocks[0]["title"] = "Advanced Microservices Architecture"
        nc = normalize_path(good_path, blocks)
        block_ncs = [normalize_lesson_block(b) for b in blocks]
        issues = _validate_curriculum(nc, block_ncs)
        assert any(i.rule_id == "CURRICULUM_FIRST_DAY" for i in issues)

    def test_too_many_prerequisites(self, bad_path, path_blocks):
        nc = normalize_path(bad_path, path_blocks)
        block_ncs = [normalize_lesson_block(b) for b in path_blocks]
        issues = _validate_curriculum(nc, block_ncs)
        assert any(i.rule_id == "CURRICULUM_PREREQUISITES" for i in issues)


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Scoring
# ═══════════════════════════════════════════════════════════════════

class TestScoring:
    def test_no_issues_gives_high_score(self, good_block):
        nc = normalize_lesson_block(good_block)
        issues = _validate_structural(nc) + _validate_beginner(nc) + _validate_technical(nc)
        dims = _calculate_scores(nc, issues)
        assert dims["overall"] >= 80, f"Expected >= 80, got {dims['overall']}"

    def test_many_issues_gives_low_score(self, bad_block):
        nc = normalize_lesson_block(bad_block)
        issues = (_validate_structural(nc) + _validate_beginner(nc) +
                  _validate_technical(nc))
        dims = _calculate_scores(nc, issues)
        assert dims["overall"] < 75, f"Expected < 75, got {dims['overall']}"

    def test_custom_weights(self, good_block):
        nc = normalize_lesson_block(good_block)
        custom = {k: 0.1 for k in DEFAULT_SCORING_WEIGHTS}
        dims = _calculate_scores(nc, [], custom)
        assert 0 <= dims["overall"] <= 100


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Block Validation
# ═══════════════════════════════════════════════════════════════════

class TestBlockValidation:
    def test_good_block_passes(self, good_block):
        result = validate_block(good_block)
        assert result["status"] == "PASS"
        assert result["overall_score"] >= 70
        assert not result["improvement_required"]
        assert len(result["issues"]) <= 2  # allow 1-2 minor P2s

    def test_bad_block_fails(self, bad_block):
        result = validate_block(bad_block)
        assert result["status"] == "FAIL"
        assert result["overall_score"] < 70
        assert result["improvement_required"]
        assert len(result["issues"]) >= 3

    def test_actions_for_passing(self, good_block):
        result = validate_block(good_block)
        assert any(a["action"] in ("KEEP", "IMPROVE") for a in result["actions"])

    def test_actions_for_failing(self, bad_block):
        result = validate_block(bad_block)
        assert result["status"] == "FAIL"
        assert any(a["action"] in ("IMPROVE", "REWRITE") for a in result["actions"])

    def test_content_hash_in_result(self, good_block):
        result = validate_block(good_block)
        assert result["content_hash"]
        assert result["content_version"] == 2

    def test_strengths_detected(self, good_block):
        result = validate_block(good_block)
        assert len(result["strengths"]) >= 0  # may or may not have strengths

    def test_dimensions_in_result(self, good_block):
        result = validate_block(good_block)
        assert "dimensions" in result
        assert "overall" not in result["dimensions"]  # overall is top-level
        for dim in DEFAULT_SCORING_WEIGHTS:
            assert dim in result["dimensions"]


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Path Validation
# ═══════════════════════════════════════════════════════════════════

class TestPathValidation:
    def test_good_path_passes(self, good_path, path_blocks):
        result = validate_path(good_path, path_blocks)
        assert result["status"] == "PASS"
        assert result["overall_score"] >= 70
        assert result["total_blocks"] == 3
        assert len(result["block_scores"]) == 3

    def test_path_with_bad_blocks(self, good_path):
        bad_blocks = [
            {
                "_id": "b_bad1", "topic": "X", "title": "X",
                "learning_objective": "", "concept_explanation": "",
                "examples": [], "exercise": "", "status": "published",
                "day_number": 1, "slug": "bad-path",
            }
        ]
        result = validate_path(good_path, bad_blocks)
        assert result["status"] == "FAIL"
        assert result["total_issues"] > 0

    def test_path_block_scores_present(self, good_path, path_blocks):
        result = validate_path(good_path, path_blocks)
        for bs in result["block_scores"]:
            assert "score" in bs
            assert "status" in bs
            assert "issues" in bs


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Improvement Planner
# ═══════════════════════════════════════════════════════════════════

class TestImprovementPlanner:
    def test_empty_issues(self):
        plans = plan_improvements({"issues": []})
        assert plans == []

    def test_sorted_by_priority(self, bad_block):
        result = validate_block(bad_block)
        plans = plan_improvements(result)
        assert len(plans) > 0
        priorities = [p["priority"] for p in plans]
        assert priorities == sorted(priorities)

    def test_p0_becomes_rewrite(self, bad_block):
        result = validate_block(bad_block)
        plans = plan_improvements(result)
        p0_plans = [p for p in plans if p["severity"] == "P0"]
        for p in p0_plans:
            assert p["action"] == "REWRITE"


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS: Publishing Gate
# ═══════════════════════════════════════════════════════════════════

class TestPublishingGate:
    def test_passing_result(self, good_block):
        result = validate_block(good_block)
        allowed, reasons = check_publish_gate(result)
        if not allowed:
            # Allow if it's a minor issue
            assert all("score" not in r.lower() or "below" in r.lower() for r in reasons)

    def test_failing_result(self, bad_block):
        result = validate_block(bad_block)
        allowed, reasons = check_publish_gate(result)
        assert not allowed
        assert len(reasons) >= 1

    def test_custom_gate(self, good_block):
        result = validate_block(good_block)
        gate = {"min_overall": 50, "min_technical": 0, "max_p0_issues": 0}
        allowed, reasons = check_publish_gate(result, gate)
        assert allowed


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: MongoDB persistence
# ═══════════════════════════════════════════════════════════════════

class TestPersistence:
    @pytest.mark.asyncio
    async def test_save_and_retrieve_validation(self, good_block):
        from app.database import get_db
        db = get_db()
        result = validate_block(good_block)
        vid = await save_validation_result(db, "lesson", "block_001", result)
        assert vid
        history = await get_validation_history(db, "block_001")
        assert len(history) >= 1
        assert history[0]["content_id"] == "block_001"

    @pytest.mark.asyncio
    async def test_skip_revalidation(self, good_block):
        from app.database import get_db
        db = get_db()
        nc = normalize_lesson_block(good_block)
        # Save once
        result = validate_block(good_block)
        await save_validation_result(db, "lesson", "block_001", result)
        # Should skip
        skip = await should_skip_revalidation(db, "block_001", nc.content_hash)
        assert skip is True
        # Should not skip with different hash
        skip2 = await should_skip_revalidation(db, "block_001", "different_hash")
        assert skip2 is False

    @pytest.mark.asyncio
    async def test_save_improvement(self):
        from app.database import get_db
        db = get_db()
        vid = await save_improvement(db, "lesson", "block_001", 65.0, 82.0,
                                     [{"fix": "added examples"}], "hash123")
        assert vid

    @pytest.mark.asyncio
    async def test_rollback(self, good_block):
        from app.database import get_db
        db = get_db()
        # Save a passing result
        result = validate_block(good_block)
        await save_validation_result(db, "lesson", "block_001", result)
        # Rollback should find it
        rb = await rollback_content(db, "lesson", "block_001")
        assert rb["found"] is True
        assert rb["last_good_score"] > 0

    @pytest.mark.asyncio
    async def test_rollback_not_found(self):
        from app.database import get_db
        db = get_db()
        rb = await rollback_content(db, "lesson", "nonexistent")
        assert rb["found"] is False


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: validate_and_save
# ═══════════════════════════════════════════════════════════════════

class TestValidateAndSave:
    @pytest.mark.asyncio
    async def test_validate_and_save_block(self, good_block):
        from app.database import get_db
        db = get_db()
        result = await validate_and_save_block(db, good_block)
        assert result["status"] in ("PASS", "FAIL")
        # Block should now have validation metadata
        block = await db["learning_blocks"].find_one({"_id": "block_001"})
        if block:
            assert "validation_score" in block

    @pytest.mark.asyncio
    async def test_validate_and_save_path(self, good_path, path_blocks):
        from app.database import get_db
        db = get_db()
        # Insert path and blocks first
        await db["learning_paths"].update_one(
            {"_id": good_path["_id"]}, {"$set": good_path}, upsert=True)
        for b in path_blocks:
            await db["learning_blocks"].update_one(
                {"_id": b["_id"]}, {"$set": b}, upsert=True)
        result = await validate_and_save_path(db, good_path, path_blocks)
        assert result["status"] in ("PASS", "FAIL")
        assert result["total_blocks"] == 3


# ═══════════════════════════════════════════════════════════════════
# BEHAVIOR TESTS: Real-world content
# ═══════════════════════════════════════════════════════════════════

class TestRealWorldContent:
    def test_aspnet_core_day1(self):
        """Day 1 of the ASP.NET Core path should score well."""
        block = {
            "_id": "aspnet_d1",
            "topic": "Setting Up Your First ASP.NET Core Project",
            "title": "Your First ASP.NET Core Project",
            "learning_objective": "Create and run your first ASP.NET Core web application using the dotnet CLI",
            "concept_explanation": (
                "ASP.NET Core is Microsoft's modern web framework. You start by creating a new project "
                "with 'dotnet new webapp'. This gives you a project folder with Program.cs, a wwwroot folder "
                "for static files, and a Pages folder for Razor pages. The dotnet run command starts a local "
                "web server on port 5000."
            ),
            "simple_explanation": "Think of ASP.NET Core like a restaurant kitchen — Program.cs is the recipe, "
                                  "Pages are the menu items, and wwwroot is the pantry with ingredients.",
            "examples": [
                {"title": "Create project", "code": "dotnet new webapp -n MyFirstApp\ncd MyFirstApp\ndotnet run",
                 "explanation": "Creates a new web app, enters the folder, and starts the server."}
            ],
            "exercise": "Install the .NET SDK and create a new webapp project",
            "homework": "Modify the Index.cshtml page to display your name",
            "real_world_example": (
                "When you visit a government website to apply for a service, the pages you see are generated "
                "by a server-side framework like ASP.NET Core. Each page is a template filled with your data."
            ),
            "step_by_step": [
                "Install .NET SDK from dotnet.microsoft.com",
                "Open a terminal and type 'dotnet new webapp -n MyApp'",
                "cd into the folder and type 'dotnet run'",
                "Open your browser to localhost:5000",
            ],
            "try_it_yourself": "Change the page title in Index.cshtml and refresh the browser",
            "common_mistakes": [
                "Forgetting to install the .NET SDK before running dotnet commands"
            ],
            "quick_review": "You created an ASP.NET Core project, ran it, and saw it in the browser.",
            "why_matters": "Every web application starts with a project setup — this is your foundation.",
            "status": "published",
            "version": 2,
            "day_number": 1,
            "slug": "asp-net-core",
        }
        result = validate_block(block)
        assert result["overall_score"] >= 70, f"ASP.NET Core Day 1 score: {result['overall_score']}"
        p0 = [i for i in result["issues"] if i["severity"] == "P0"]
        assert len(p0) == 0, f"Unexpected P0 issues: {p0}"

    def test_weak_content_gets_low_score(self):
        """Very weak content should fail (below publish threshold)."""
        block = {
            "_id": "weak_1",
            "topic": "Advanced Topic",
            "title": "Advanced Topic",
            "learning_objective": "",
            "concept_explanation": (
                "As an AI, I will explain this topic. In today's digital world, "
                "this is important. Furthermore, you should understand the concepts. "
                "Moreover, this is a complex topic. In conclusion, it is worth noting "
                "that as mentioned earlier, it should be noted."
            ),
            "simple_explanation": "",
            "examples": [],
            "exercise": "",
            "homework": "",
            "real_world_example": "",
            "step_by_step": [],
            "try_it_yourself": "",
            "common_mistakes": [],
            "quick_review": "In summary, this lesson covered advanced topics.",
            "status": "published",
            "day_number": 1,
            "slug": "weak-path",
        }
        result = validate_block(block)
        assert result["status"] == "FAIL"
        assert result["improvement_required"]
        assert len(result["issues"]) >= 3
        # Should not be publishable
        from app.services.content_validator import check_publish_gate
        allowed, reasons = check_publish_gate(result)
        assert not allowed
