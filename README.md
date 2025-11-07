# How to “plug / unplug” modules
**Explainable AI Tutor (Proof of Concept)**  
This project explores how an AI-based tutoring system can guide learners in a transparent and human-understandable way. Instead of simply answering questions, the tutor identifies prerequisite knowledge gaps, recommends the next learning step, and clearly explains _why_ those recommendations are made.

The goal of this proof of concept is to demonstrate:

-   A small **skill graph** for a chosen learning domain (e.g., basics before DSA),
    
-   A **diagnostic check** to gauge learner readiness,
    
-   A **rule-based decision policy** that determines the next instructional step,
    
-   And an **explainability layer** that communicates the reasoning behind the system’s decisions.
    

This project uses:

-   **Python** for backend logic (FastAPI)
    
-   **Rule-based tutoring policies** for transparent decision-making
    
-   **Config files** (YAML) for defining skills and questions
    
-   (Optional) **LLM APIs** only for generating _educational explanations_, not for decision logic
    

The system behaves like a real teacher:  
It asks questions, evaluates understanding, flags misconceptions, and _explains why_ it recommends reviewing a concept or moving ahead.

> The long-term direction is to generalize this into multi-domain tutor “agents” (e.g., programming, math, spoken language), each built on the same explainability-first interaction model.

# Commands and Init Repo
- py -m venv .venv
- .venv\Scripts\Activate.ps1
- python -m pip install --upgrade pip
- pip install -r requirements.txt
- uvicorn app:app --reload

