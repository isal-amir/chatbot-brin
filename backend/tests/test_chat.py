import pytest
from unittest.mock import patch, AsyncMock
from models.chat import ChatSession, ChatMessage

# Mocked responses for our dependencies
MOCK_EMBEDDING = [0.1, 0.2, 0.3]
MOCK_CONTEXT = "This is a fake chunk from a PDF."
MOCK_LLM_RESPONSE = "This is a mocked AI response. The capital of France is Paris."

@pytest.fixture
def mock_generate_embedding():
    with patch("main.generate_embedding", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = MOCK_EMBEDDING
        yield mock_func

@pytest.fixture
def mock_search_documents():
    with patch("main.search_documents", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = MOCK_CONTEXT
        yield mock_func

@pytest.fixture
def mock_generate_response():
    with patch("main.generate_response", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = MOCK_LLM_RESPONSE
        yield mock_func

def test_chat_creates_session(client, student_token, db_session, mock_generate_embedding, mock_search_documents, mock_generate_response):
    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"query": "What is the capital of France?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == MOCK_LLM_RESPONSE
    assert "session_id" in data
    
    session_id = data["session_id"]
    
    # Verify DB state
    session = db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
    assert session is not None
    assert session.title == "What is the capital of France?"
    
    messages = db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What is the capital of France?"
    assert messages[1].role == "ai"
    assert messages[1].content == MOCK_LLM_RESPONSE

    # Verify mocks were called
    mock_generate_embedding.assert_called_once_with("What is the capital of France?")
    mock_search_documents.assert_called_once_with(MOCK_EMBEDDING)
    mock_generate_response.assert_called_once_with(
        query="What is the capital of France?",
        context=MOCK_CONTEXT,
        chat_history=""
    )

def test_chat_existing_session(client, student_token, db_session, mock_generate_embedding, mock_search_documents, mock_generate_response):
    # First, create a session manually or through the API
    create_response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    session_id = create_response.json()["id"]
    
    # Add a message to this session
    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "query": "Tell me a joke.",
            "session_id": session_id
        }
    )
    
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    
    messages = db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    assert len(messages) == 2 # 1 user, 1 AI

def test_get_sessions(client, student_token):
    # Get initial sessions (should be empty if DB cleared between tests)
    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    
    # Create a session
    client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert len(response.json()) >= 1
