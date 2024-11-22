from typing import Dict, Any, List
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda
from .models import GameState

# Action-specific prompt templates
MOVEMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are processing movement in a text adventure game. 
    Given the current location and movement intent, determine if the movement is possible 
    and describe the result. Consider:
    - Available paths/exits
    - Obstacles or barriers
    - Required items for passage
    Return a JSON with format:
    {
        "possible": true/false,
        "description": "Description of movement or why it's not possible",
        "new_location": "Name of new location if moved"
    }"""),
    ("human", "Current location: {current_location}\nDesired movement: {movement}\nAvailable exits: {exits}")
])

COMBAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are processing combat in a text adventure game.
    Given the player's action and the current combat situation, determine the outcome.
    Consider:
    - Player's abilities and equipment
    - Enemy status and abilities
    - Combat mechanics (hit chance, damage)
    Return a JSON with format:
    {
        "success": true/false,
        "damage_dealt": number,
        "damage_received": number,
        "description": "Description of the combat action and its results"
    }"""),
    ("human", "Player action: {action}\nPlayer status: {player_status}\nEnemy: {enemy_status}")
])

INTERACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are processing interaction with objects or NPCs in a text adventure game.
    Given the interaction target and action, determine the outcome.
    Consider:
    - Object/NPC properties
    - Required items or conditions
    - Possible interaction outcomes
    Return a JSON with format:
    {
        "success": true/false,
        "result": "Description of interaction result",
        "state_changes": {"item_gained": [], "item_used": [], "quest_updated": []}
    }"""),
    ("human", "Interaction target: {target}\nAction: {action}\nInventory: {inventory}")
])

INVENTORY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are processing inventory actions in a text adventure game.
    Handle inventory management including checking, using, combining items.
    Return a JSON with format:
    {
        "success": true/false,
        "result": "Description of inventory action result",
        "inventory_changes": {"added": [], "removed": [], "modified": []}
    }"""),
    ("human", "Action: {action}\nCurrent inventory: {inventory}")
])

def create_action_chains(llm: BaseChatModel):
    """Creates all action-specific chains"""
    
    def movement_chain(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process movement actions"""
        game_state = data.get("game_state", {})
        current_location = game_state.get("current_location", "unknown")
        exits = game_state.get("available_exits", [])
        movement = data.get("input", "")
        
        response = (MOVEMENT_PROMPT | llm).invoke({
            "current_location": current_location,
            "movement": movement,
            "exits": ", ".join(exits) if exits else "unknown"
        })
        
        # Process the response and update game state
        result = response.content
        return {
            "response": result,
            "state_updates": {"location_changed": True} if "new_location" in result else {}
        }

    def combat_chain(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process combat actions"""
        game_state = data.get("game_state", {})
        player_status = game_state.get("player_status", {})
        enemy_status = game_state.get("current_enemy", {})
        action = data.get("input", "")
        
        response = (COMBAT_PROMPT | llm).invoke({
            "action": action,
            "player_status": player_status,
            "enemy_status": enemy_status
        })
        
        return {
            "response": response.content,
            "state_updates": {"combat_occurred": True}
        }

    def interaction_chain(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process interaction with objects/NPCs"""
        game_state = data.get("game_state", {})
        inventory = game_state.get("inventory", [])
        entities = data.get("entities", [])
        action = data.get("input", "")
        
        response = (INTERACTION_PROMPT | llm).invoke({
            "target": ", ".join(entities),
            "action": action,
            "inventory": inventory
        })
        
        return {
            "response": response.content,
            "state_updates": {"interaction_occurred": True}
        }

    def inventory_chain(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process inventory actions"""
        game_state = data.get("game_state", {})
        inventory = game_state.get("inventory", [])
        action = data.get("input", "")
        
        response = (INVENTORY_PROMPT | llm).invoke({
            "action": action,
            "inventory": inventory
        })
        
        return {
            "response": response.content,
            "state_updates": {"inventory_changed": True}
        }

    return {
        "movement": RunnableLambda(movement_chain),
        "combat": RunnableLambda(combat_chain),
        "interact": RunnableLambda(interaction_chain),
        "inventory": RunnableLambda(inventory_chain)
    }
