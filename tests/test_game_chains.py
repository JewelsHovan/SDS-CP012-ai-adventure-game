import pytest
from unittest.mock import Mock
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from src.chains.models import GameState, ProcessedInput
from src.chains.game_chains import route_action

class MockChatModel(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content="move"),
                    text="move"
                )
            ]
        )

    @property
    def _llm_type(self):
        return "mock"

@pytest.fixture
def game_chain():
    llm = MockChatModel()
    return create_game_chain(llm)

def test_route_action_with_empty_game_state():
    """Test routing an action with an empty game state"""
    llm = MockChatModel()
    game_state = GameState(messages=[])
    result = route_action(llm, "look around", game_state)
    assert isinstance(result, ProcessedInput)
    assert result.raw_input == "look around"

def test_route_action_with_existing_game_state():
    """Test routing an action with an existing game state"""
    llm = MockChatModel()
    game_state = GameState(
        character_name="Test Character",
        character_class="Warrior",
        location="Test Location",
        inventory=["sword"],
        health=100,
        messages=[]
    )
    result = route_action(llm, "attack goblin", game_state)
    assert isinstance(result, ProcessedInput)
    assert result.raw_input == "attack goblin"

def test_route_action_with_unknown_action():
    """Test routing an unknown action"""
    llm = MockChatModel()
    game_state = GameState(messages=[])
    result = route_action(llm, "nonsense command", game_state)
    assert isinstance(result, ProcessedInput)
    assert result.raw_input == "nonsense command"

def test_action_mapping():
    """Test that common action phrases are correctly mapped to intents"""
    llm = MockChatModel()
    game_state = GameState(messages=[])
    
    # Test look action
    result = route_action(llm, "look around", game_state)
    assert isinstance(result, ProcessedInput)
    
    # Test movement action
    result = route_action(llm, "go north", game_state)
    assert isinstance(result, ProcessedInput)
    
    # Test attack action
    result = route_action(llm, "attack goblin", game_state)
    assert isinstance(result, ProcessedInput)
