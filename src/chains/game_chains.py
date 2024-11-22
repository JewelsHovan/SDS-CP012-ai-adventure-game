from typing import Dict, Any, Optional
from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from pydantic import BaseModel
from .action_chains import create_action_chains

class GameState(BaseModel):
    """Represents the current state of the game"""
    messages: list[BaseMessage]
    context: Dict[str, Any] = {}
    player_state: Dict[str, Any] = {}
    world_state: Dict[str, Any] = {}
    current_location: str = "start"
    available_exits: list[str] = []
    inventory: list[str] = []
    current_enemy: Optional[Dict[str, Any]] = None

class ProcessedInput(BaseModel):
    """Represents processed user input with intent and entities"""
    raw_input: str
    intent: str
    entities: list[str]
    confidence: float

# Prompt templates
INTENT_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an intent classifier for a text adventure game. "
              "Classify the user's input into one of these categories: "
              "move, interact, combat, inventory, query, quit. "
              "Return only the category name in lowercase."),
    ("human", "{input}")
])

ENTITY_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Extract key entities (objects, characters, locations, items) from the input. "
              "Return them as a comma-separated list."),
    ("human", "{input}")
])

def create_game_chain(llm: BaseChatModel):
    """Creates the main game processing chain"""
    
    # Get action chains
    action_chains = create_action_chains(llm)
    
    # Input processing functions
    def classify_intent(input_text: str) -> str:
        """Classify the user's intent"""
        response = INTENT_CLASSIFICATION_PROMPT | llm
        return response.invoke({"input": input_text}).content.strip()

    def extract_entities(input_text: str) -> list[str]:
        """Extract entities from user input"""
        response = ENTITY_EXTRACTION_PROMPT | llm
        entities = response.invoke({"input": input_text}).content.strip()
        return [e.strip() for e in entities.split(",") if e.strip()]

    def process_input(input_data: Dict[str, Any]) -> ProcessedInput:
        """Process raw input into structured format"""
        raw_input = input_data["input"]
        intent = classify_intent(raw_input)
        entities = extract_entities(raw_input)
        
        return ProcessedInput(
            raw_input=raw_input,
            intent=intent,
            entities=entities,
            confidence=1.0  # We can add real confidence scoring later
        )

    def route_action(data: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate action chain based on intent"""
        processed_input = data["processed_input"]
        game_state = data.get("game_state", GameState(messages=[]))
        
        chain = action_chains.get(processed_input.intent)
        if not chain:
            return {"response": "I don't understand that action."}
            
        result = chain.invoke({
            "input": processed_input.raw_input,
            "intent": processed_input.intent,
            "entities": processed_input.entities,
            "game_state": game_state.dict()
        })
        
        # Update game state based on action result
        if "state_updates" in result:
            for key, value in result["state_updates"].items():
                setattr(game_state, key, value)
        
        return {
            "response": result["response"],
            "game_state": game_state
        }

    # Create the main processing chain
    input_processor = RunnableLambda(process_input)
    action_router = RunnableLambda(route_action)

    # Combine chains using the pipe operator
    game_chain = (
        {
            "processed_input": {"input": RunnablePassthrough()} | input_processor,
            "game_state": RunnablePassthrough()
        }
        | action_router
    )

    return game_chain
