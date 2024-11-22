from enum import Enum, auto
from typing import Dict, Any, Optional, Callable, List
from pydantic import BaseModel, Field
from .models import GameState, ProcessedInput

class GameStateType(Enum):
    """Represents different states the game can be in"""
    INITIALIZING = auto()
    CHARACTER_CREATION = auto()
    EXPLORING = auto()
    IN_COMBAT = auto()
    IN_DIALOGUE = auto()
    IN_INVENTORY = auto()
    GAME_OVER = auto()

class StateTransition(BaseModel):
    """Represents a transition between states"""
    from_state: GameStateType
    to_state: GameStateType
    action: str
    conditions: List[str]

class StateMachine:
    """
    Manages game state transitions and ensures state consistency
    """
    def __init__(self):
        self.current_state: GameStateType = GameStateType.INITIALIZING
        self.game_state: Optional[GameState] = None
        self.transitions: Dict[str, StateTransition] = {}
        self._setup_transitions()
        self.state_validators: Dict[GameStateType, List[Callable]] = {}
        self._setup_validators()

    def _setup_transitions(self):
        """Define valid state transitions"""
        self.transitions = {
            # From INITIALIZING
            "start_character_creation": StateTransition(
                from_state=GameStateType.INITIALIZING,
                to_state=GameStateType.CHARACTER_CREATION,
                action="start_character_creation",
                conditions=["config_loaded"]
            ),
            
            # From CHARACTER_CREATION
            "start_game": StateTransition(
                from_state=GameStateType.CHARACTER_CREATION,
                to_state=GameStateType.EXPLORING,
                action="start_game",
                conditions=["character_created"]
            ),
            
            # From EXPLORING
            "enter_combat": StateTransition(
                from_state=GameStateType.EXPLORING,
                to_state=GameStateType.IN_COMBAT,
                action="enter_combat",
                conditions=["enemy_present"]
            ),
            "start_dialogue": StateTransition(
                from_state=GameStateType.EXPLORING,
                to_state=GameStateType.IN_DIALOGUE,
                action="start_dialogue",
                conditions=["npc_present"]
            ),
            "open_inventory": StateTransition(
                from_state=GameStateType.EXPLORING,
                to_state=GameStateType.IN_INVENTORY,
                action="open_inventory",
                conditions=[]
            ),
            
            # From IN_COMBAT
            "end_combat": StateTransition(
                from_state=GameStateType.IN_COMBAT,
                to_state=GameStateType.EXPLORING,
                action="end_combat",
                conditions=["combat_resolved"]
            ),
            "game_over_combat": StateTransition(
                from_state=GameStateType.IN_COMBAT,
                to_state=GameStateType.GAME_OVER,
                action="player_defeated",
                conditions=["player_health_zero"]
            ),
            
            # From IN_DIALOGUE
            "end_dialogue": StateTransition(
                from_state=GameStateType.IN_DIALOGUE,
                to_state=GameStateType.EXPLORING,
                action="end_dialogue",
                conditions=["dialogue_completed"]
            ),
            
            # From IN_INVENTORY
            "close_inventory": StateTransition(
                from_state=GameStateType.IN_INVENTORY,
                to_state=GameStateType.EXPLORING,
                action="close_inventory",
                conditions=[]
            ),
        }

    def _setup_validators(self):
        """Setup validation functions for each state"""
        self.state_validators = {
            GameStateType.EXPLORING: [
                self._validate_location,
                self._validate_player_state
            ],
            GameStateType.IN_COMBAT: [
                self._validate_combat_state,
                self._validate_player_state
            ],
            GameStateType.IN_DIALOGUE: [
                self._validate_dialogue_state,
                self._validate_player_state
            ],
            GameStateType.IN_INVENTORY: [
                self._validate_inventory_state
            ]
        }

    def _validate_location(self, game_state: GameState) -> bool:
        """Validate location-related state"""
        return (
            game_state.current_location is not None and
            isinstance(game_state.available_exits, list)
        )

    def _validate_combat_state(self, game_state: GameState) -> bool:
        """Validate combat-related state"""
        return game_state.current_enemy is not None

    def _validate_dialogue_state(self, game_state: GameState) -> bool:
        """Validate dialogue-related state"""
        return "current_npc" in game_state.context

    def _validate_inventory_state(self, game_state: GameState) -> bool:
        """Validate inventory-related state"""
        return isinstance(game_state.inventory, list)

    def _validate_player_state(self, game_state: GameState) -> bool:
        """Validate player-related state"""
        return (
            "health" in game_state.player_state and
            "level" in game_state.player_state
        )

    def check_transition_conditions(self, transition: StateTransition, game_state: GameState) -> bool:
        """Check if all conditions for a transition are met"""
        condition_checks = {
            "config_loaded": lambda: True,  # Always true as config is required
            "character_created": lambda: bool(game_state.player_state),
            "enemy_present": lambda: game_state.current_enemy is not None,
            "npc_present": lambda: "current_npc" in game_state.context,
            "combat_resolved": lambda: (
                game_state.current_enemy is None or 
                game_state.current_enemy.get("health", 0) <= 0
            ),
            "player_health_zero": lambda: game_state.player_state.get("health", 1) <= 0,
            "dialogue_completed": lambda: game_state.context.get("dialogue_completed", False)
        }
        
        return all(condition_checks[condition]() for condition in transition.conditions)

    def validate_state(self, game_state: GameState) -> bool:
        """Run all validators for the current state"""
        if self.current_state not in self.state_validators:
            return True
        
        return all(
            validator(game_state) 
            for validator in self.state_validators[self.current_state]
        )

    def can_transition(self, action: str, game_state: GameState) -> bool:
        """Check if a transition is possible"""
        if action not in self.transitions:
            return False
            
        transition = self.transitions[action]
        if transition.from_state != self.current_state:
            return False
            
        return self.check_transition_conditions(transition, game_state)

    def transition(self, action: str, game_state: GameState) -> bool:
        """
        Attempt to transition to a new state
        Returns True if transition was successful
        """
        if not self.can_transition(action, game_state):
            return False
            
        transition = self.transitions[action]
        self.current_state = transition.to_state
        self.game_state = game_state
        
        return self.validate_state(game_state)

    def get_current_state(self) -> GameStateType:
        """Get the current game state"""
        return self.current_state

    def get_valid_actions(self, game_state: GameState) -> List[str]:
        """Get list of valid actions from current state"""
        return [
            action for action, transition in self.transitions.items()
            if transition.from_state == self.current_state
            and self.check_transition_conditions(transition, game_state)
        ]
