# Tests for chat_service
import pytest
from services.chat_service import ChatService

@pytest.fixture
def chat_service():
    return ChatService()

def test_generate_response(chat_service):
    response = chat_service.generate_response("What can you do?")
    assert isinstance(response, str)
    assert len(response) > 0