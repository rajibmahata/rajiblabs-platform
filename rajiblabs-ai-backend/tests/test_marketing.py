"""Marketing core unit tests — pure functions only, no DB required."""
from app.services import leads as rules
from app.services.marketing import (eligible_filter, html_to_text,
                                    lead_template_context, render_template,
                                    sanitize_html, segment_query,
                                    verify_send_token)


def test_score_explained_mirrors_score():
    lead = {"name": "Asha", "email": "asha@example.com", "phone": "+911234567890",
            "company_name": "Acme", "industry": "Retail"}
    idea = {"description": "Need a billing app for my shop",
            "problem_statement": "manual billing takes hours every day, error prone",
            "desired_outcome": "one-click GST invoices"}
    score, reasons = rules.score_lead_explained(lead, idea, "please send a proposal and call me")
    assert score == rules.score_lead(lead, idea, "please send a proposal and call me")
    assert score == 10 + 10 + 15 + 5 + 5 + 10 + 10 + 15 + 20
    assert any("proposal" in r.lower() for r in reasons)
    assert any("consultation" in r.lower() for r in reasons)


def test_score_explained_empty():
    score, reasons = rules.score_lead_explained({}, {}, "")
    assert score == 0 and reasons == []


def test_render_allowlist():
    out = render_template("Hi {{first_name}} at {{company_name}}! {{secret}} {{unsubscribe_url}}",
                          {"first_name": "Asha", "company_name": "Acme",
                           "secret": "X", "unsubscribe_url": "https://x/u"})
    assert out == "Hi Asha at Acme!  https://x/u"


def test_lead_context_no_chat_content():
    ctx = lead_template_context({"name": "Ravi Kumar", "company_name": "RK Foods"})
    assert ctx["first_name"] == "Ravi" and ctx["full_name"] == "Ravi Kumar"
    assert "inventory problem" not in str(ctx)


def test_sanitize_strips_danger():
    dirty = ('<p>Hello</p><script>alert(1)</script>'
             '<a href="javascript:evil()">x</a>'
             '<a href="https://rajiblabs.com/p">y</a>'
             '<img src="https://a/b.png" onerror="z()">')
    clean = sanitize_html(dirty)
    assert "<script" not in clean and "javascript:" not in clean and "onerror" not in clean
    assert "https://rajiblabs.com/p" in clean and "<p>Hello</p>" in clean


def test_html_to_text():
    assert "Hello" in html_to_text("<p>Hello</p><p>World</p>")
    assert "<" not in html_to_text("<b>x</b>")


def test_token_roundtrip_and_tamper():
    from app.services.marketing import make_send_token
    t = make_send_token("c1", "l2", "A@Example.com")
    assert verify_send_token(t, "a@example.com") == ("c1", "l2")
    assert verify_send_token(t + "x", "a@example.com") is None
    assert verify_send_token(t, "other@example.com") is None
    assert verify_send_token("bogus", "a@example.com") is None


def test_segments_shape():
    for seg in rules.SEGMENTS:
        q = segment_query(seg)
        assert isinstance(q, dict)
    assert segment_query("hot_leads").get("$or")
    assert segment_query("all_opted_in", {"tags": ["saas"]})["tags"] == {"$in": ["saas"]}


def test_eligible_filter_requires_consent():
    f = eligible_filter()
    assert f["marketing_consent"] is True
    assert f["unsubscribe"] == {"$ne": True}


def test_statuses_extended_backwards_compatible():
    for s in ("new", "contacted", "qualified", "proposal", "won", "lost",
              "archived", "spam", "closed"):
        assert s in rules.VALID_STATUSES
    for s in ("hot", "warm", "cold", "customer", "follow_up", "converted",
              "unsubscribed"):
        assert s in rules.VALID_STATUSES


def test_lead_sources():
    assert "website_chat" in rules.LEAD_SOURCES
    assert "live_agent" in rules.LEAD_SOURCES
