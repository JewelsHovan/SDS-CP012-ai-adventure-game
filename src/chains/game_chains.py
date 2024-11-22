from typing import Dict, Any
from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from .action_chains import create_action_chains
from .models import GameState, ProcessedInput
from difflib import get_close_matches

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

def classify_intent(llm: BaseChatModel, input_text: str) -> str:
    """Classify the user's intent"""
    response = INTENT_CLASSIFICATION_PROMPT | llm
    return response.invoke({"input": input_text}).content.strip()

def extract_entities(llm: BaseChatModel, input_text: str) -> list[str]:
    """Extract entities from user input"""
    response = ENTITY_EXTRACTION_PROMPT | llm
    entities = response.invoke({"input": input_text}).content.strip()
    return [e.strip() for e in entities.split(",") if e.strip()]

def match_action(user_input: str, available_actions: list[str], threshold: float = 0.6) -> str | None:
    """Match user input against available actions using fuzzy matching"""
    # Normalize input and actions to lowercase for better matching
    user_input = user_input.lower().strip()
    normalized_actions = [action.lower().strip() for action in available_actions]
    
    # Try exact match first
    if user_input in normalized_actions:
        return available_actions[normalized_actions.index(user_input)]
    
    # Try fuzzy matching
    matches = get_close_matches(user_input, normalized_actions, n=1, cutoff=threshold)
    if matches:
        return available_actions[normalized_actions.index(matches[0])]
    
    return None

def process_input(llm: BaseChatModel, input_data: str | Dict[str, Any], game_state: GameState | None = None) -> ProcessedInput:
    """Process raw input into structured format"""
    # Extract the raw input string from the input data
    raw_input = ""
    if isinstance(input_data, dict):
        raw_input = input_data.get("input", "")
        if isinstance(raw_input, dict):
            raw_input = raw_input.get("input", "")
        elif isinstance(raw_input, str):
            raw_input = raw_input
    else:
        raw_input = str(input_data)
    
    # Map intents to state machine actions
    intent_to_action = {
        "move": None,  # No direct state change for movement
        "interact": "start_dialogue",
        "combat": "enter_combat",
        "inventory": "open_inventory",
        "quit": None
    }
    
    # Classify intent
    intent = classify_intent(llm, raw_input)
    entities = extract_entities(llm, raw_input)
    
    # Validate action against available actions if game state is provided
    matched_action = None
    if game_state and hasattr(game_state, 'available_actions'):
        matched_action = match_action(raw_input, game_state.available_actions)
    
    return ProcessedInput(
        raw_input=raw_input,
        intent=intent,
        entities=entities,
        action=matched_action or intent_to_action.get(intent),
        valid_action=matched_action is not None
    )

def route_action(llm: BaseChatModel, input_text: str, game_state: GameState | Dict[str, Any]) -> ProcessedInput:
    """Process and route an action"""
    # Process the input
    processed_input = process_input(llm, input_text, game_state)
    
    # Convert game_state to GameState if it's a dict
    if isinstance(game_state, dict):
        # Ensure we have the required messages field
        if "messages" not in game_state:
            game_state["messages"] = []
        game_state = GameState(**game_state)
    elif not isinstance(game_state, GameState):
        game_state = GameState(messages=[])
    
    return processed_input

def create_game_chain(llm: BaseChatModel):
    """Creates the main game processing chain"""
    
    # Get action chains
    action_chains = create_action_chains(llm)
    
    def route_chain_action(data: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate action chain and include state transition info"""
        # Process the input, handling both string and dict inputs
        input_data = data.get("input", "")
        if isinstance(input_data, str):
            processed_input = process_input(llm, {"input": input_data})
        else:
            processed_input = process_input(llm, input_data)
            
        game_state = data.get("game_state", {})
        
        # Convert game_state to GameState if it's a dict
        if isinstance(game_state, dict):
            # Ensure we have the required messages field
            if "messages" not in game_state:
                game_state["messages"] = []
            game_state = GameState(**game_state)
        elif not isinstance(game_state, GameState):
            game_state = GameState(messages=[])
        
        # Get the appropriate action chain
        chain = action_chains.get(processed_input.intent)
        if not chain:
            return {
                "response": "I don't understand that action.",
                "game_state": game_state
            }
            
        # Process the action
        result = chain.invoke({
            "input": processed_input.raw_input,
            "game_state": game_state.model_dump() if hasattr(game_state, "model_dump") else game_state.dict()
        })
        
        # Include the action for state machine
        result["action"] = processed_input.action
        
        return result

    # Create the main processing chain
    input_processor = RunnableLambda(lambda x: process_input(llm, x))
    action_router = RunnableLambda(route_chain_action)

    # Combine chains using the pipe operator
    game_chain = (
        {
            "processed_input": RunnableLambda(lambda x: {"input": x["input"]}) | input_processor,
            "game_state": RunnablePassthrough()
        }
        | action_router
    )

    return game_chain
