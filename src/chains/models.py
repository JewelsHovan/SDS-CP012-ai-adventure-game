from typing import Dict, Any, Optional, List
from langchain.schema import BaseMessage
from pydantic import BaseModel

class GameState(BaseModel):
    """Represents the current state of the game"""
    messages: list[BaseMessage]
    context: Dict[str, Any] = {}
    player_state: Dict[str, Any] = {}
    world_state: Dict[str, Any] = {}
    current_location: str = "start"
    available_exits: list[str] = []
    available_actions: list[str] = []  # Add available_actions field
    inventory: list[str] = []
    current_enemy: Optional[Dict[str, Any]] = None

class ProcessedInput(BaseModel):
    """Represents processed user input with intent and entities"""
    raw_input: str
    intent: str
    entities: List[str] = []
    action: Optional[str] = None  # Corresponding state machine action
    valid_action: bool = False  # Whether the action matches an available action
    confidence: float = 1.0
