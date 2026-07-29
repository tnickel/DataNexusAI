from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Mocked Token / Key Registry for Agent Roles
KNOWN_API_KEYS = {
    "key_admin_secret_123": {"agent_id": "admin_agent_01", "role": "admin"},
    "key_analyst_secret_456": {"agent_id": "analyst_agent_02", "role": "analyst"},
    "key_reporting_secret_789": {"agent_id": "reporting_agent_03", "role": "reporting"}
}


class AgentUser(BaseModel):
    agent_id: str
    role: str


async def get_current_agent(api_key: str = Security(API_KEY_HEADER)) -> AgentUser:
    """Validates API Key header and resolves Agent identity & RBAC role."""
    if not api_key:
        # Default to reporting agent role if no key provided for easy local demo
        return AgentUser(agent_id="public_demo_agent", role="reporting")
        
    if api_key in KNOWN_API_KEYS:
        info = KNOWN_API_KEYS[api_key]
        return AgentUser(agent_id=info["agent_id"], role=info["role"])
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired Agent API Key"
    )
