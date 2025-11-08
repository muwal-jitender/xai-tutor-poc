# core/templating.py
from jinja2 import Template
from core.loaders import load_templates, load_skill_graph

def render(template_key: str, ctx: dict) -> str:
    tpl = load_templates()[template_key]
    return Template(tpl).render(**ctx)

def titles_for(ids):
    skills = load_skill_graph()["skills"]
    return {i: skills[i]["title"] for i in ids if i in skills}
