# tests/test_templating.py
from core.templating import render

def test_render_review_template_has_placeholders():
    txt = render("review_prereq", {
        "skill_title": "Algorithmic Vocabulary",
        "next_title": "Time Complexity (Big O)",
        "score_correct": 1,
        "score_total": 3,
        "threshold": 2
    })
    assert "Algorithmic Vocabulary" in txt
    assert "Time Complexity" in txt
    assert "1/3" in txt
