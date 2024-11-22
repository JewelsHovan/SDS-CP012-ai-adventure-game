from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain.schema import BaseMessage
import json
from datetime import datetime

class PlayerStats(BaseModel):
    """Player character statistics"""
    health: int = 100
    max_health: int = 100
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    equipped_items: Dict[str, str] = Field(default_factory=lambda: {
        "weapon": None,
        "armor": None,
        "accessory": None
    })

class InventoryItem(BaseModel):
    """Individual inventory item"""
    name: str
    type: str  # weapon, armor, consumable, key_item, etc.
    description: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    quantity: int = 1

class Location(BaseModel):
    """Game location information"""
    name: str
    description: str
    available_exits: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)
    npcs: List[str] = Field(default_factory=list)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    visited: bool = False

class QuestStatus(BaseModel):
    """Quest tracking"""
    name: str
    description: str
    status: str = "not_started"  # not_started, in_progress, completed, failed
    objectives: Dict[str, bool] = Field(default_factory=dict)
    rewards: Dict[str, Any] = Field(default_factory=dict)

class GameState(BaseModel):
    """Complete game state"""
    # Basic info
    player_name: str = ""
    current_location: str = "start"
    
    # Complex state tracking
    player_stats: PlayerStats = Field(default_factory=PlayerStats)
    inventory: Dict[str, InventoryItem] = Field(default_factory=dict)
    locations: Dict[str, Location] = Field(default_factory=dict)
    quests: Dict[str, QuestStatus] = Field(default_factory=dict)
    
    # Game progression
    visited_locations: List[str] = Field(default_factory=list)
    completed_quests: List[str] = Field(default_factory=list)
    current_enemies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Conversation history
    messages: List[BaseMessage] = Field(default_factory=list)
    
    # Game metadata
    game_start_time: datetime = Field(default_factory=datetime.now)
    last_save_time: Optional[datetime] = None
    
    def update_location(self, new_location: str) -> None:
        """Update player location and track visited locations"""
        if new_location not in self.visited_locations:
            self.visited_locations.append(new_location)
        self.current_location = new_location
        if new_location in self.locations:
            self.locations[new_location].visited = True

    def add_to_inventory(self, item: InventoryItem) -> None:
        """Add or update item in inventory"""
        if item.name in self.inventory:
            self.inventory[item.name].quantity += item.quantity
        else:
            self.inventory[item.name] = item

    def remove_from_inventory(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory, returns False if not enough items"""
        if item_name not in self.inventory:
            return False
        if self.inventory[item_name].quantity < quantity:
            return False
        
        self.inventory[item_name].quantity -= quantity
        if self.inventory[item_name].quantity <= 0:
            del self.inventory[item_name]
        return True

    def update_quest_status(self, quest_name: str, objective: str = None) -> None:
        """Update quest status and track completion"""
        if quest_name not in self.quests:
            return
            
        quest = self.quests[quest_name]
        if objective:
            quest.objectives[objective] = True
            
        # Check if all objectives are completed
        if all(quest.objectives.values()):
            quest.status = "completed"
            if quest_name not in self.completed_quests:
                self.completed_quests.append(quest_name)

    def apply_state_updates(self, updates: Dict[str, Any]) -> None:
        """Apply a batch of state updates"""
        for key, value in updates.items():
            if key == "location_changed":
                self.update_location(value)
            elif key == "inventory_changed":
                for item_data in value.get("added", []):
                    self.add_to_inventory(InventoryItem(**item_data))
                for item_name in value.get("removed", []):
                    self.remove_from_inventory(item_name)
            elif key == "quest_updated":
                self.update_quest_status(value["quest"], value.get("objective"))
            elif key == "combat_occurred":
                if value.get("damage_taken"):
                    self.player_stats.health -= value["damage_taken"]
                if value.get("enemy_defeated"):
                    enemy_name = value["enemy_defeated"]
                    if enemy_name in self.current_enemies:
                        del self.current_enemies[enemy_name]

    def save_game(self, save_path: str) -> None:
        """Save game state to file"""
        self.last_save_time = datetime.now()
        # Convert to dict and handle datetime serialization
        state_dict = self.dict(exclude={'messages'})
        state_dict['game_start_time'] = self.game_start_time.isoformat()
        state_dict['last_save_time'] = self.last_save_time.isoformat()
        
        with open(save_path, 'w') as f:
            json.dump(state_dict, f, indent=2)

    @classmethod
    def load_game(cls, save_path: str) -> 'GameState':
        """Load game state from file"""
        with open(save_path, 'r') as f:
            state_dict = json.load(f)
        
        # Convert datetime strings back to datetime objects
        state_dict['game_start_time'] = datetime.fromisoformat(state_dict['game_start_time'])
        if state_dict['last_save_time']:
            state_dict['last_save_time'] = datetime.fromisoformat(state_dict['last_save_time'])
            
        return cls(**state_dict)
