from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.agents.skills import (
    BaseAgentSkill,
    Text2SQLQuerySkill,
    DocumentRAGSkill,
    DataHealthCheckSkill,
    SkillExecutionResult
)


class AgentRouter:
    """
    Static Route Dispatcher for Agent Skills.
    Routes agent execution requests deterministically based on defined static routes,
    eliminating fragile LLM looping behavior.
    """

    def __init__(self):
        self._skills: Dict[str, BaseAgentSkill] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        self.register_skill(Text2SQLQuerySkill())
        self.register_skill(DocumentRAGSkill())
        self.register_skill(DataHealthCheckSkill())

    def register_skill(self, skill: BaseAgentSkill):
        self._skills[skill.name] = skill

    def list_skills(self, user_role: str = "analyst") -> List[Dict[str, Any]]:
        """Lists all registered skills available to the user's RBAC role."""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "allowed_roles": skill.allowed_roles
            }
            for skill in self._skills.values()
            if user_role in skill.allowed_roles
        ]

    def route_and_execute(
        self,
        skill_name: str,
        params: Dict[str, Any],
        db: Session,
        user_role: str = "analyst"
    ) -> SkillExecutionResult:
        """Deterministisch gelenkte Skill-Ausführung via Statische Route."""
        if skill_name not in self._skills:
            return SkillExecutionResult(
                skill_name=skill_name,
                status="FAILED",
                output={},
                error=f"Unbekannte Skill-Route: '{skill_name}'. Verfügbare Skills: {list(self._skills.keys())}"
            )

        skill = self._skills[skill_name]
        
        # Check RBAC permission for skill execution
        if user_role not in skill.allowed_roles:
            return SkillExecutionResult(
                skill_name=skill_name,
                status="FORBIDDEN",
                output={},
                error=f"Rolle '{user_role}' besitzt keine Berechtigung für Skill '{skill_name}'."
            )

        return skill.execute(params=params, db=db, user_role=user_role)
