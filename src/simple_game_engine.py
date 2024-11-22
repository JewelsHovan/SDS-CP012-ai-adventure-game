from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)

class GameState(BaseModel):
    """Game state with description and available actions"""
    description: str = Field(description="Narrative description of the current game state")
    available_actions: List[str] = Field(description="List of actions available to the player")
    state_updates: Dict[str, Any] = Field(description="Updates to game state like inventory, stats, etc")

class SimpleGameEngine:
    def __init__(self, model_name: str = "gpt-4"):
        # Load environment variables
        load_dotenv()
        
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        self.llm = ChatOpenAI(model_name=model_name)
        self.parser = PydanticOutputParser(pydantic_object=GameState)
        self.current_state = None
        self.setup_prompt()
        
    def setup_prompt(self):
        """Load and setup the game prompt"""
        try:
            # Load the system prompt from template
            prompt_path = Path(__file__).parent.parent / "templates" / "simple_game_prompt.md"
            system_prompt = prompt_path.read_text(encoding="utf-8")
            
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", """Current game state: 
{current_state}

Player action: {player_action}

Remember to maintain the exact JSON structure and provide clear, contextual actions.""")
            ])
        except Exception as e:
            logging.error(f"Error loading prompt template: {e}")
            raise

    def start_game(self):
        """Initialize the game with character and setting selection"""
        initial_prompt = """I choose rogue character and castle setting. 
        Remember to respond with the exact JSON structure including description, available_actions, and state_updates."""
        
        try:
            # Get initial game state
            formatted_messages = self.prompt.format_messages(
                current_state="{}",  # Empty initial state
                player_action=initial_prompt
            )
            response = self.llm.invoke(formatted_messages)
            
            try:
                self.current_state = json.loads(response.content)
                print("\n" + self.current_state["description"])
                print("\nAvailable actions:", ", ".join(self.current_state["available_actions"]))
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error parsing initial game state: {e}")
                print("Error starting game. Please try again.")
                raise
                
        except Exception as e:
            logging.error(f"Error in game initialization: {e}")
            raise

    def process_action(self, player_action: str) -> Optional[Dict[str, Any]]:
        """Process a player action and update game state"""
        if player_action.lower() == "quit":
            return None

        try:
            # Prepare the prompt with current state and player action
            formatted_messages = self.prompt.format_messages(
                current_state=json.dumps(self.current_state),
                player_action=player_action
            )
            
            # Get LLM response
            result = self.llm.invoke(formatted_messages)
            
            try:
                # Parse the response into structured format
                new_state = json.loads(result.content)
                
                # Validate required fields
                required_fields = ["description", "available_actions", "state_updates"]
                if not all(field in new_state for field in required_fields):
                    raise ValueError("Missing required fields in game state")
                
                self.current_state = new_state
                
                # Display the result
                print("\n" + new_state["description"])
                print("\nAvailable actions:", ", ".join(new_state["available_actions"]))
                
                return new_state
                
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing game state: {e}")
                print("There was an error processing your action. Please try again.")
                return self.current_state
                
            except ValueError as e:
                logging.error(f"Invalid game state format: {e}")
                print("There was an error with the game state. Please try again.")
                return self.current_state
                
        except Exception as e:
            logging.error(f"Error processing action: {e}")
            print("There was an unexpected error. Please try again.")
            return self.current_state

    def play(self):
        """Main game loop"""
        self.start_game()

        while True:
            action = input("\nWhat would you like to do? (or type 'quit' to end): ")
            if action.lower() == "quit":
                print("\nThanks for playing!")
                break

            result = self.process_action(action)
            if result is None:
                break

if __name__ == "__main__":
    game = SimpleGameEngine()
    game.play()
