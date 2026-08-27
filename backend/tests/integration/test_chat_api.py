"""
Integration tests for Chat API & conversation management.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.rag.pipeline import PipelineResult


def test_chat_and_conversations_flow(client: TestClient, auth_headers: dict[str, str]):
    with patch("app.services.chat_service.run_pipeline") as mock_pipeline:
        mock_pipeline.return_value = PipelineResult(
            answer="This is a mock RAG answer.",
            sources=[{"chunk_id": 1, "document_id": 1, "filename": "doc.txt", "page_number": 1, "chunk_index": 0, "score": 0.95}],
            chunks_used=1,
        )

        # Send chat message
        res = client.post(
            "/api/chat",
            json={"question": "What is in the documentation?"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["answer"] == "This is a mock RAG answer."
        assert "conversation_id" in data
        conv_id = data["conversation_id"]

        # List conversations
        conv_res = client.get("/api/conversations", headers=auth_headers)
        assert conv_res.status_code == 200
        conv_list = conv_res.json()
        assert any(c["id"] == conv_id for c in conv_list)

        # Get conversation detail
        detail_res = client.get(f"/api/conversations/{conv_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        messages = detail_res.json()["messages"]
        assert len(messages) >= 2  # user + assistant

        # Delete conversation
        del_res = client.delete(f"/api/conversations/{conv_id}", headers=auth_headers)
        assert del_res.status_code == 204


def test_chat_stream_api(client: TestClient, auth_headers: dict[str, str]):
    with patch("app.services.chat_service.run_pipeline_stream") as mock_stream:
        def fake_stream(*args, **kwargs):
            yield 'data: {"token": "Hello", "done": false}\n\n'
            yield 'data: {"token": "", "sources": [], "done": true}\n\n'

        mock_stream.return_value = fake_stream()

        res = client.post(
            "/api/chat/stream",
            json={"question": "Stream test question?"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        assert "Hello" in res.text
