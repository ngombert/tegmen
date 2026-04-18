import os
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from common.logger import setup_logger

logger = setup_logger("agent_registry")

class AgentConfig(BaseModel):
    """Configuration definition for a single agent."""
    name: str
    description: str
    url: str # Using str to allow environment variable overrides without HttpUrl strictness
    utterances: List[str] = Field(default_factory=list)

class RegistryConfig(BaseModel):
    """Schema for agents.yaml."""
    agents: List[AgentConfig]

class AgentRegistry:
    """
    Central registry for agents, loaded from config/agents.yaml.
    Support environment variable overrides for URLs.
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents = {}
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load agents from YAML and apply environment overrides."""
        config_path = os.path.join(os.getcwd(), "config", "agents.yaml")
        
        if not os.path.exists(config_path):
            error_msg = f"Agent registry configuration not found at {config_path}"
            logger.error(error_msg)
            # We don't raise Exception here to allow for minimal startup, 
            # but methods will fail if registry is empty.
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            validated_config = RegistryConfig(**data)
            
            for agent in validated_config.agents:
                # Environment override: AGENT_{NAME}_URL
                env_var = f"AGENT_{agent.name.upper()}_URL"
                if env_var in os.environ:
                    agent.url = os.environ[env_var]
                    logger.info(f"Overriding URL for {agent.name} via {env_var}")
                
                self._agents[agent.name] = agent
                
            logger.info(f"Loaded {len(self._agents)} agents from registry.")
            
        except Exception as e:
            logger.error(f"Failed to load agent registry: {str(e)}")
            raise RuntimeError(f"Critical configuration error: {str(e)}")

    def get_agent_url(self, name: str) -> Optional[str]:
        """Get the effective URL for a given agent."""
        agent = self._agents.get(name)
        return agent.url if agent else None

    def get_agent_description(self, name: str) -> Optional[str]:
        """Get the description for a given agent."""
        agent = self._agents.get(name)
        return agent.description if agent else None

    def list_agents(self) -> List[Dict]:
        """Return a list of all agents with their basic info."""
        return [
            {"name": a.name, "description": a.description, "url": a.url}
            for a in self._agents.values()
        ]

    def get_agents(self) -> Dict[str, AgentConfig]:
        """Return all agent configurations."""
        return self._agents

    def get_all_utterances(self) -> Dict[str, List[str]]:
        """Return mapping of agent names to their utterances for semantic routing."""
        return {a.name: a.utterances for a in self._agents.values()}

# Singleton instance
agent_registry = AgentRegistry()
