"""
services/agents — All IELTS AI agent implementations.

Structure:
    base.py           — BaseAgent: shared async wrappers around GemmaClient
    registry.py       — AgentRegistry: @registry.register decorator + get(name)

    council/          — Council of Judges (parallel multi-agent writing evaluator)
        lexical_tracker.py    — LexicalTrackerAgent
        syntax_auditor.py     — SyntaxAuditorAgent
        rhetoric_cohesion.py  — RhetoricCohesionAgent
        chief_examiner.py     — ChiefExaminerAgent
        runner.py             — run_council() orchestrator

    socratic/         — Socratic Debugging Agent (multi-turn hint engine)
        hint_engine.py        — SocraticHintAgent

    syllabus/         — Autonomous Syllabus Curating Agent
        curator.py            — SyllabusCuratorAgent

    adversarial/      — Adversarial Distractor Agent (cognitive trap generator)
        distractor.py         — AdversarialDistractorAgent

Import pattern (prefer sub-package imports for clarity):
    from services.agents.council import run_council, CouncilReport
    from services.agents.socratic import SocraticHintAgent
    from services.agents.syllabus import SyllabusCuratorAgent
    from services.agents.adversarial import AdversarialDistractorAgent

Or use the registry for dynamic lookup:
    from services.agents.registry import registry
    agent = registry.get("LexicalTrackerAgent")

All modules register their agents automatically when imported.
Import this package to trigger all registrations:
"""

# Trigger all @registry.register decorators
from services.agents.council import (        # noqa: F401
    LexicalTrackerAgent, SyntaxAuditorAgent,
    RhetoricCohesionAgent, ChiefExaminerAgent,
    run_council, CouncilReport,
)
from services.agents.socratic import SocraticHintAgent          # noqa: F401
from services.agents.syllabus import SyllabusCuratorAgent       # noqa: F401
from services.agents.adversarial import AdversarialDistractorAgent  # noqa: F401
