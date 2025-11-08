# core/loaders.py
from functools import lru_cache
import yaml
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@lru_cache(maxsize=1)
def load_skill_graph():
    with open(DATA_DIR / "skill_graph.yaml", "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    skills = {s["id"]: s for s in y["skills"]}
    prerequisites = {sid: skills[sid].get("prerequisites", []) for sid in skills}
    return {"skills": skills, "prerequisites": prerequisites}

@lru_cache(maxsize=1)
def load_questions():
    with open(DATA_DIR / "questions.yaml", "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    by_skill = {}
    for q in y["questions"]:
        by_skill.setdefault(q["skill"], []).append(q)
    return {"all": y["questions"], "by_skill": by_skill}

@lru_cache(maxsize=1)
def load_templates():
    with open(DATA_DIR / "explanations.yaml", "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    return y["templates"]
