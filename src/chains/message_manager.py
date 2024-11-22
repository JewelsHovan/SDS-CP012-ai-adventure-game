from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto
from langchain.schema import BaseMessage, SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel

class MessageType(Enum):
    """Types of messages in the game"""
    SYSTEM = auto()
    NARRATIVE = auto()
    DIALOGUE = auto()
    COMBAT = auto()
    INVENTORY = auto()
    ENVIRONMENT = auto()
    PLAYER_ACTION = auto()

@dataclass
class MessageContext:
    """Context for a message"""
    type: MessageType
    location: Optional[str] = None
    timestamp: Optional[float] = None
    related_entities: List[str] = None
    importance: int = 1  # 1-5, with 5 being most important

class MessageManager:
    """Manages game message history with intelligent pruning and context management"""
    
    def __init__(self, max_history: int = 50, context_window: int = 10):
        self.messages: List[BaseMessage] = []
        self.message_contexts: Dict[int, MessageContext] = {}
        self.max_history = max_history
        self.context_window = context_window
        self.system_prompt: Optional[SystemMessage] = None
        
    def add_system_prompt(self, content: str):
        """Add or update system prompt"""
        self.system_prompt = SystemMessage(content=content)
        if not self.messages or not isinstance(self.messages[0], SystemMessage):
            self.messages.insert(0, self.system_prompt)
        else:
            self.messages[0] = self.system_prompt
            
    def add_message(self, content: str, message_type: MessageType, 
                   is_ai: bool = False, context: Dict[str, Any] = None) -> BaseMessage:
        """Add a new message with context"""
        # Create message
        message = AIMessage(content=content) if is_ai else HumanMessage(content=content)
        
        # Create context
        msg_context = MessageContext(
            type=message_type,
            location=context.get('location') if context else None,
            timestamp=context.get('timestamp') if context else None,
            related_entities=context.get('entities', []) if context else [],
            importance=context.get('importance', 1) if context else 1
        )
        
        # Add message and context
        self.messages.append(message)
        self.message_contexts[id(message)] = msg_context
        
        # Prune if necessary
        if len(self.messages) > self.max_history:
            self._prune_messages()
            
        return message
    
    def get_relevant_history(self, current_context: Dict[str, Any], 
                           max_messages: Optional[int] = None) -> List[BaseMessage]:
        """Get relevant message history based on current context"""
        if not max_messages:
            max_messages = self.context_window
            
        # Always include system prompt
        if self.system_prompt:
            relevant_messages = [self.system_prompt]
        else:
            relevant_messages = []
            
        # Score and sort messages by relevance
        scored_messages = []
        current_location = current_context.get('location')
        current_entities = current_context.get('entities', [])
        
        for msg in reversed(self.messages[1:]):  # Skip system prompt
            context = self.message_contexts.get(id(msg))
            if not context:
                continue
                
            score = self._calculate_relevance_score(
                context, current_location, current_entities
            )
            scored_messages.append((score, msg))
            
        # Sort by relevance score and take top N
        relevant_messages.extend([msg for _, msg in sorted(scored_messages, key=lambda x: x[0], reverse=True)[:max_messages]])
        
        return relevant_messages
    
    def _calculate_relevance_score(self, context: MessageContext, 
                                 current_location: Optional[str], 
                                 current_entities: List[str]) -> float:
        """Calculate relevance score for a message context based on multiple factors:
        1. Base importance of the message
        2. Location relevance (exact match, connected location, or unrelated)
        3. Entity relevance (shared entities and their importance)
        4. Message type relevance (different weights for different types)
        5. Temporal relevance (more recent messages score higher)
        """
        # Base score from importance (1-5 scale, weighted heavily)
        score = context.importance * 2.0

        # Location relevance
        if context.location and current_location:
            if context.location == current_location:
                score += 3.0  # Exact location match
            elif self._are_locations_connected(context.location, current_location):
                score += 1.5  # Connected location
                
        # Entity relevance with importance weighting
        if context.related_entities and current_entities:
            common_entities = set(context.related_entities) & set(current_entities)
            entity_score = len(common_entities) * 1.0
            
            # Bonus for important entities (e.g., quest items, key characters)
            important_entities = self._get_important_entities()
            important_matches = common_entities & important_entities
            entity_score += len(important_matches) * 0.5
            
            score += entity_score
            
        # Message type weighting
        type_weights = {
            MessageType.SYSTEM: 5.0,      # System messages are critical
            MessageType.NARRATIVE: 2.0,    # Narrative provides important context
            MessageType.DIALOGUE: 1.8,     # Dialogue helps with character interaction
            MessageType.COMBAT: 1.5,       # Combat relevant for immediate threats
            MessageType.INVENTORY: 1.2,    # Inventory changes somewhat important
            MessageType.ENVIRONMENT: 1.0,  # Environmental details less critical
            MessageType.PLAYER_ACTION: 1.3 # Player actions provide context
        }
        score *= type_weights.get(context.type, 1.0)
        
        # Temporal relevance - more recent messages score higher
        if context.timestamp:
            import time
            time_diff = time.time() - context.timestamp
            temporal_factor = max(0.5, 1.0 - (time_diff / (60 * 60)))  # Decay over an hour
            score *= temporal_factor
            
        return score

    def _calculate_retention_score(self, context: MessageContext) -> float:
        """Calculate retention score for message pruning based on:
        1. Message importance
        2. Message type
        3. Entity significance
        4. Narrative continuity
        5. Player interaction relevance
        """
        # Base retention score from importance
        score = context.importance * 2.0
        
        # Message type retention weights
        type_retention_weights = {
            MessageType.SYSTEM: 10.0,     # Always retain system messages
            MessageType.NARRATIVE: 3.0,    # Keep key narrative elements
            MessageType.DIALOGUE: 2.5,     # Important conversations
            MessageType.COMBAT: 2.0,       # Combat outcomes
            MessageType.INVENTORY: 1.5,    # Inventory changes
            MessageType.ENVIRONMENT: 1.0,  # Environmental context
            MessageType.PLAYER_ACTION: 2.0 # Player decisions
        }
        score *= type_retention_weights.get(context.type, 1.0)
        
        # Entity significance
        if context.related_entities:
            important_entities = self._get_important_entities()
            significant_matches = set(context.related_entities) & important_entities
            score += len(significant_matches) * 2.0
            
        # Narrative continuity - keep messages that link to current quest/storyline
        if self._is_part_of_active_quest(context):
            score *= 1.5
            
        # Player interaction relevance
        if self._involves_player_decision(context):
            score *= 1.3
            
        return score

    def _are_locations_connected(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are directly connected in the game world"""
        # Define location connections (could be loaded from game data)
        location_connections = {
            'forest_edge': ['deep_woods', 'river_crossing'],
            'deep_woods': ['forest_edge', 'ancient_ruins'],
            'river_crossing': ['forest_edge', 'mountain_path'],
            'ancient_ruins': ['deep_woods', 'temple_interior'],
            'mountain_path': ['river_crossing', 'peak'],
            'temple_interior': ['ancient_ruins'],
            'peak': ['mountain_path']
        }
        return loc2 in location_connections.get(loc1, [])

    def _get_important_entities(self) -> set:
        """Get set of important entities in the game"""
        return {
            # Quest items
            'ancient_scroll', 'magic_gem', 'sacred_amulet',
            # Key characters
            'elder_sage', 'forest_guardian', 'dark_sorcerer',
            # Important locations
            'ancient_temple', 'sacred_grove', 'dragon_lair',
            # Key quest objectives
            'portal_key', 'healing_crystal', 'dragon_egg'
        }

    def _is_part_of_active_quest(self, context: MessageContext) -> bool:
        """Check if message is related to any active quests"""
        # This could be expanded to check against actual quest state
        if not context.related_entities:
            return False
            
        quest_related_terms = {
            'ancient_scroll', 'magic_gem', 'sacred_amulet',
            'elder_sage', 'forest_guardian', 'dark_sorcerer',
            'quest', 'mission', 'task'
        }
        return bool(set(context.related_entities) & quest_related_terms)

    def _involves_player_decision(self, context: MessageContext) -> bool:
        """Check if message involves a significant player decision"""
        return (context.type == MessageType.PLAYER_ACTION or 
                (context.type == MessageType.DIALOGUE and 
                 any(term in context.content.lower() 
                     for term in ['choose', 'decide', 'option', 'path'])))

    def _prune_messages(self):
        """Intelligently prune message history"""
        if len(self.messages) <= self.max_history:
            return
            
        # Always keep system prompt
        if self.system_prompt:
            protected_messages = [self.system_prompt]
        else:
            protected_messages = []
            
        # Score messages for retention
        scored_messages = []
        for msg in self.messages[1:]:  # Skip system prompt
            context = self.message_contexts.get(id(msg))
            if not context:
                continue
                
            retention_score = self._calculate_retention_score(context)
            scored_messages.append((retention_score, msg))
            
        # Sort by retention score and keep top messages
        keep_messages = [msg for _, msg in sorted(scored_messages, key=lambda x: x[0], reverse=True)[:self.max_history - 1]]
        
        # Update message list
        self.messages = protected_messages + keep_messages
        
        # Clean up contexts for removed messages
        current_msg_ids = {id(msg) for msg in self.messages}
        self.message_contexts = {
            msg_id: context 
            for msg_id, context in self.message_contexts.items()
            if msg_id in current_msg_ids
        }
    
    def clear_history(self, keep_system_prompt: bool = True):
        """Clear message history"""
        if keep_system_prompt and self.system_prompt:
            self.messages = [self.system_prompt]
        else:
            self.messages = []
        self.message_contexts.clear()
        
    def get_message_count(self) -> int:
        """Get current message count"""
        return len(self.messages)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current message contexts"""
        type_counts = {}
        total_importance = 0
        locations = set()
        entities = set()
        
        for context in self.message_contexts.values():
            type_counts[context.type] = type_counts.get(context.type, 0) + 1
            total_importance += context.importance
            if context.location:
                locations.add(context.location)
            if context.related_entities:
                entities.update(context.related_entities)
                
        return {
            "message_count": len(self.messages),
            "type_distribution": type_counts,
            "average_importance": total_importance / len(self.message_contexts) if self.message_contexts else 0,
            "unique_locations": list(locations),
            "unique_entities": list(entities)
        }
