from typing import List, Dict, Any
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage
from pathlib import Path
import logging
from .config import ChatConfig
from .chains import create_game_chain
from .chains.state_management import GameState, Location, PlayerStats
from .chains.state_machine import StateMachine, GameStateType
from .chains.message_manager import MessageManager, MessageType

class GameEngine:
    def __init__(self, config: ChatConfig):
        self.config = config
        self.storyteller = config.get_chat_provider()
        self.game_chain = create_game_chain(self.storyteller)
        self.state_machine = StateMachine()
        self.message_manager = MessageManager(
            max_history=config.max_history,
            context_window=20  # Configurable context window size
        )
        self.game_state = GameState(
            player_stats=PlayerStats(),
            locations={
                "start": Location(
                    name="start",
                    description="Starting location",
                    available_exits=["forest", "village"],
                    objects=["old_map", "backpack"],
                    npcs=["guide"]
                )
            }
        )
        
    def initialize_game(self):
        """Setup initial game state and prompts"""
        self._load_prompts()
        self._get_character_options()
        self._get_user_selection()
        
    def _load_prompts(self):
        """Setup initial game state and prompts"""
        try:
            system_prompt = Path(self.config.system_prompt_path).read_text(encoding="utf-8").strip()
            character_setup = Path("templates/character_setting_setup.md").read_text(encoding="utf-8").strip()
            
            # Add system prompt
            self.message_manager.add_system_prompt(system_prompt)
            
            # Add character setup as narrative message
            self.message_manager.add_message(
                content=character_setup,
                message_type=MessageType.NARRATIVE,
                is_ai=False,
                context={"importance": 4}  # High importance for setup
            )
            
            # Update game state messages
            self.game_state.messages = self.message_manager.get_relevant_history(
                current_context={"location": self.game_state.current_location}
            )
            
        except FileNotFoundError as e:
            logging.error(f"Prompt file not found: {e.filename}")
            raise

    def _get_character_options(self):
        options_response = self.storyteller.invoke(self.game_state.messages)
        options_text = options_response.content
        print("\n=== Character and Setting Options ===")
        print(options_text)
        self.message_manager.add_message(
            content=options_text,
            message_type=MessageType.NARRATIVE,
            is_ai=True,
            context={
                "location": self.game_state.current_location,
                "entities": list(self.game_state.inventory),
                "importance": 3
            }
        )

    def _get_user_selection(self):
        user_input = input("Please choose a character and setting from the options above: ")
        self.message_manager.add_message(
            content=user_input,
            message_type=MessageType.PLAYER_ACTION,
            is_ai=False,
            context={
                "location": self.game_state.current_location,
                "entities": list(self.game_state.inventory)
            }
        )
        self.message_manager.add_message(
            content="Start the adventure with the selected character and setting!",
            message_type=MessageType.NARRATIVE,
            is_ai=False,
            context={
                "location": self.game_state.current_location,
                "entities": list(self.game_state.inventory)
            }
        )

    def save_game(self, save_path: str = "save_game.json"):
        """Save current game state"""
        try:
            self.game_state.save_game(save_path)
            print(f"Game saved successfully to {save_path}")
        except Exception as e:
            logging.error(f"Failed to save game: {str(e)}")
            print("Failed to save game. Please try again.")

    def load_game(self, save_path: str = "save_game.json"):
        """Load saved game state"""
        try:
            self.game_state = GameState.load_game(save_path)
            print(f"Game loaded successfully from {save_path}")
        except Exception as e:
            logging.error(f"Failed to load game: {str(e)}")
            print("Failed to load game. Starting new game instead.")

    async def run_game_loop(self):
        """Main game loop using LCEL chains"""
        try:
            while True:
                # Get current state and valid actions
                current_state = self.state_machine.get_current_state()
                valid_actions = self.state_machine.get_valid_actions(self.game_state)
                
                # Get relevant message history for current context
                current_context = {
                    "location": self.game_state.current_location,
                    "entities": list(self.game_state.inventory)
                }
                relevant_history = self.message_manager.get_relevant_history(current_context)
                self.game_state.messages = relevant_history
                
                # Generate story continuation
                response = self.storyteller.invoke(self.game_state.messages) 
                story_text = response.content
                print(story_text)
                
                # Add AI response to message history
                self.message_manager.add_message(
                    content=story_text,
                    message_type=MessageType.NARRATIVE,
                    is_ai=True,
                    context={
                        "location": self.game_state.current_location,
                        "entities": list(self.game_state.inventory),
                        "importance": 3
                    }
                )
                
                # Get player input
                user_input = input("What would you like to do? (or type 'quit' to end): ")
                
                if user_input.lower() == 'quit':
                    print("\nWould you like to save your game? (yes/no)")
                    save_choice = input().lower()
                    if save_choice.startswith('y'):
                        self.save_game()
                    print("\nThanks for playing!")
                    break
                
                if user_input.lower() == 'save':
                    self.save_game()
                    continue
                
                if user_input.lower() == 'load':
                    self.load_game()
                    continue
                
                # Process player input
                result = self.process_action(user_input)
                
                if "quit" in result:
                    print("\nWould you like to save your game? (yes/no)")
                    save_choice = input().lower()
                    if save_choice.startswith('y'):
                        self.save_game()
                    print("\nThanks for playing!")
                    break
                
                if "error" in result:
                    print(result["error"])
                    continue
                
                # Update game state with processed action
                if "game_state" in result:
                    new_game_state = result["game_state"]
                    # Attempt state transition based on the action
                    action = result.get("action", "")
                    if action and self.state_machine.can_transition(action, new_game_state):
                        if self.state_machine.transition(action, new_game_state):
                            self.game_state = new_game_state
                        else:
                            print("Invalid state transition: State validation failed")
                    else:
                        self.game_state = new_game_state
                
                # Display response
                print(result["response"])
        
        except Exception as e:
            print(f"An error occurred: {e}")
            logging.error(f"Error in game loop: {str(e)}", exc_info=True)
            print("Would you like to save your game before exiting? (yes/no)")
            save_choice = input().lower()
            if save_choice.startswith('y'):
                self.save_game()

    def process_action(self, user_input: str) -> Dict[str, Any]:
        """Process a user action and update game state"""
        if user_input.lower().strip() == 'quit':
            return {"quit": True}

        # Process the action through the game chain
        try:
            processed_input = self.game_chain.invoke({
                "input": user_input,
                "game_state": self.game_state
            })

            # Check if the action is valid
            if not processed_input.valid_action:
                available_actions_str = ", ".join(f"'{action}'" for action in self.game_state.available_actions)
                return {
                    "error": f"I don't understand that action. Available actions are: {available_actions_str}"
                }

            # Update game state based on the action
            response = self._update_game_state(processed_input)
            return response

        except Exception as e:
            logging.error(f"Error processing action: {str(e)}")
            return {"error": "There was an error processing your action. Please try again."}

    def _update_game_state(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Update game state based on processed input"""
        # Update state machine if there's a valid state transition
        if processed_input.action and processed_input.valid_action:
            self.state_machine.transition(processed_input.action)

        # Get the next game state from the chain
        response = self.game_chain.invoke({
            "input": processed_input.raw_input,
            "game_state": self.game_state
        })

        # Update the game state with the response
        if isinstance(response, dict):
            self.game_state.update(response)
        
        return response