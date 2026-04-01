"""
Test script for RAG module API endpoints.

Tests for Knowledge, Books, and Reports modules:
- GET /api/knowledge/tree - Get knowledge tree
- GET /api/knowledge - List knowledge points
- POST /api/books/upload - Upload book
- GET /api/books - List books
- POST /api/rag/search - Semantic search
- GET /api/reports - List reports

Usage:
    python test_api/test_rag.py
"""

import asyncio
import io
from test_base import BaseTest, run_test_module


class TestRAGAPIs(BaseTest):
    """Test class for RAG-related API endpoints."""
    
    def __init__(self):
        super().__init__("RAG APIs")
        self.uploaded_book_id = None
    
    async def test_get_knowledge_tree(self):
        """Test GET /api/knowledge/tree endpoint."""
        try:
            response = await self.client.get(
                "/api/knowledge/tree",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /api/knowledge/tree", True, f"Found {len(data)} root nodes")
            else:
                self._log_result("GET /api/knowledge/tree", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/knowledge/tree", False, str(e))
    
    async def test_list_knowledge_points(self):
        """Test GET /api/knowledge endpoint."""
        try:
            response = await self.client.get(
                "/api/knowledge",
                params={"limit": 10},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /api/knowledge", True, f"Found {len(data)} knowledge points")
            else:
                self._log_result("GET /api/knowledge", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/knowledge", False, str(e))
    
    async def test_list_books(self):
        """Test GET /api/books endpoint."""
        try:
            response = await self.client.get(
                "/api/books",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /api/books", True, f"Found {len(data)} books")
            else:
                self._log_result("GET /api/books", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/books", False, str(e))
    
    async def test_upload_book(self):
        """Test POST /api/books/upload endpoint."""
        try:
            # Create test markdown content
            content = "# Test Book\n\nThis is a test book for API testing.\n\n## Chapter 1\n\nContent here."
            
            files = {
                "file": ("test_book.md", io.BytesIO(content.encode()), "text/markdown"),
            }
            data = {
                "title": "Test Book for API Testing"
            }
            
            response = await self.client.post(
                "/api/books/upload",
                files=files,
                data=data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                book_data = response.json()
                self.uploaded_book_id = book_data["id"]
                self._log_result("POST /api/books/upload", True, f"Uploaded book ID: {self.uploaded_book_id}")
            else:
                self._log_result("POST /api/books/upload", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /api/books/upload", False, str(e))
    
    async def test_vectorize_book(self):
        """Test POST /api/rag/books/{id}/vectorize endpoint."""
        if not self.uploaded_book_id:
            self._log_result("POST /api/rag/books/{id}/vectorize", False, "No book uploaded yet")
            return
        
        try:
            response = await self.client.post(
                f"/api/rag/books/{self.uploaded_book_id}/vectorize",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self._log_result(f"POST /api/rag/books/{self.uploaded_book_id}/vectorize", True, f"Chunks: {data.get('chunks', 'N/A')}")
            else:
                self._log_result(f"POST /api/rag/books/{self.uploaded_book_id}/vectorize", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"POST /api/rag/books/{self.uploaded_book_id}/vectorize", False, str(e))
    
    async def test_rag_search(self):
        """Test POST /api/rag/search endpoint."""
        try:
            response = await self.client.post(
                "/api/rag/search",
                params={"query": "test", "limit": 5},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self._log_result("POST /api/rag/search", True, f"Knowledge: {len(data.get('knowledge', []))}, Documents: {len(data.get('documents', []))}")
            else:
                self._log_result("POST /api/rag/search", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /api/rag/search", False, str(e))
    
    async def test_list_reports(self):
        """Test GET /api/reports endpoint."""
        try:
            response = await self.client.get(
                "/api/reports",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /api/reports", True, f"Found {len(data)} reports")
            else:
                self._log_result("GET /api/reports", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/reports", False, str(e))
    
    async def test_get_report_summary(self):
        """Test GET /api/reports/summary endpoint."""
        try:
            response = await self.client.get(
                "/api/reports/summary",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self._log_result("GET /api/reports/summary", True, f"Total reports: {data.get('total_reports', 0)}")
            else:
                self._log_result("GET /api/reports/summary", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/reports/summary", False, str(e))
    
    async def test_delete_book(self):
        """Test DELETE /api/books/{id} endpoint (cleanup)."""
        if not self.uploaded_book_id:
            self._log_result("DELETE /api/books/{id}", False, "No book uploaded yet")
            return
        
        try:
            response = await self.client.delete(
                f"/api/books/{self.uploaded_book_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 204:
                self._log_result(f"DELETE /api/books/{self.uploaded_book_id}", True, "Book deleted")
            else:
                self._log_result(f"DELETE /api/books/{self.uploaded_book_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"DELETE /api/books/{self.uploaded_book_id}", False, str(e))


async def main():
    """Run all RAG API tests."""
    success = await run_test_module(TestRAGAPIs, "RAG APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
