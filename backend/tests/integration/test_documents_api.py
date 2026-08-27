"""
Integration tests for Documents API endpoints.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_upload_and_list_documents(client: TestClient, auth_headers: dict[str, str]):
    file_content = b"This is a test documentation file for upload testing."
    files = {"file": ("test_doc.txt", file_content, "text/plain")}

    with patch("app.services.embedding_service.embed_texts") as mock_embed:
        mock_embed.return_value = [[0.1] * 3072]

        # Upload
        res = client.post("/api/documents/upload", files=files, headers=auth_headers)
        assert res.status_code == 201
        doc_data = res.json()
        assert doc_data["filename"] == "test_doc.txt"
        assert doc_data["status"] == "ready"
        doc_id = doc_data["id"]

        # List
        list_res = client.get("/api/documents", headers=auth_headers)
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert any(d["id"] == doc_id for d in items)

        # Get by ID
        get_res = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == doc_id

        # Delete
        del_res = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
        assert del_res.status_code == 204


def test_url_ingestion_api(client: TestClient, auth_headers: dict[str, str]):
    with patch("app.services.document_service.load_url") as mock_load_url, \
         patch("app.services.embedding_service.embed_texts") as mock_embed:

        mock_load_url.return_value = ("Test Web Page", "Scraped documentation content from web.")
        mock_embed.return_value = [[0.1] * 3072]

        res = client.post(
            "/api/documents/url",
            json={"url": "https://example.com/docs"},
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["file_type"] == "url"
        assert data["status"] == "ready"
