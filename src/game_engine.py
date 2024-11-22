from typing import List
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage
from pathlib import Path
import logging
from .config import ChatConfig
from .chains import create_game_chain
from .chains.state_management import GameState, Location, PlayerStats

class GameEngine:
    def __init__(self, config: ChatConfig):
        self.config = config
        self.storyteller = config.get_chat_provider()
        self.game_chain = create_game_chain(self.storyteller)
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
        try:
            system_prompt = Path(self.config.system_prompt_path).read_text(encoding="utf-8").strip()
            character_setup = Path("templates/character_setting_setup.md").read_text(encoding="utf-8").strip()
            
            self.game_state.messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=character_setup)
            ]
        except FileNotFoundError as e:
            logging.error(f"Prompt file not found: {e.filename}")
            raise

    def _get_character_options(self):
        options_response = self.storyteller.invoke(self.game_state.messages)
        options_text = options_response.content
        print("\n=== Character and Setting Options ===")
        print(options_text)
        self.game_state.messages.append(AIMessage(content=options_text))

    def _get_user_selection(self):
        user_selection = input("Please choose a character and setting from the options above: ")
        self.game_state.messages.append(HumanMessage(content=user_selection))
        self.game_state.messages.append(HumanMessage(content="Start the adventure with the selected character and setting!"))

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
                # Generate story continuation
                response = self.storyteller.invoke(self.game_state.messages) 
                story_text = response.content
                print(story_text)
                
                self.game_state.messages.append(AIMessage(content=story_text))
                
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
                
                # Process input through game chain
                result = await self.game_chain.ainvoke({
                    "input": user_input,
                    "game_state": self.game_state
                })
                
                # Update game state with processed action
                if "game_state" in result:
                    self.game_state = result["game_state"]
                
                # Display response
                print(result["response"])
                
                # Add user input to message history
                self.game_state.messages.append(HumanMessage(content=user_input))
                
                # Maintain conversation history
                if len(self.game_state.messages) > self.config.max_history:
                    self.game_state.messages = [self.game_state.messages[0]] + \
                        self.game_state.messages[-(self.config.max_history-1):]
        
        except Exception as e:
            print(f"An error occurred: {e}")
            logging.error(f"Error in game loop: {str(e)}", exc_info=True)
            print("Would you like to save your game before exiting? (yes/no)")
            save_choice = input().lower()
            if save_choice.startswith('y'):
                self.save_game()