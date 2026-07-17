"""
AgentRegistry — central lookup table for all registered agents.

Engineering pattern: agents register themselves by decorating with @registry.register.
Callers retrieve agents by name without importing the concrete classes directly.
This makes it easy to:
  - Swap one agent implementation for another without touching callers
  - Log which agents ran during a pipeline
  - Write tests that mock a specific agent by name

Usage:
    from services.agents.registry import registry

    # Retrieve
    agent = registry.get("LexicalTrackerAgent")

    # Register (done at module level in each agent file)
    @registry.register
    class MyAgent(BaseAgent):
        name = "MyAgent"
        ...
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Simple dict-backed registry mapping agent name → agent class."""

    def __init__(self):
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(self, agent_cls: type) -> type:
        """
        Class decorator that registers an agent.

            @registry.register
            class FooAgent(BaseAgent):
                name = "FooAgent"
        """
        name = getattr(agent_cls, "name", None)
        if not name:
            raise ValueError(f"Agent class {agent_cls.__name__} must define a 'name' attribute.")
        if name in self._agents:
            logger.warning("AgentRegistry: overwriting existing agent '%s'", name)
        self._agents[name] = agent_cls
        logger.debug("AgentRegistry: registered '%s'", name)
        return agent_cls

    def get(self, name: str) -> "BaseAgent":
        """Return a new instance of the agent with the given name."""
        cls = self._agents.get(name)
        if cls is None:
            raise KeyError(
                f"Agent '{name}' not found. Registered agents: {list(self._agents.keys())}"
            )
        return cls()

    def all_names(self) -> list[str]:
        """Return a sorted list of all registered agent names."""
        return sorted(self._agents.keys())

    def __repr__(self) -> str:
        return f"AgentRegistry({self.all_names()})"


# Single global registry instance
registry = AgentRegistry()
