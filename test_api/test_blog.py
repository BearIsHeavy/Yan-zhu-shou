"""
Test script for Blog API endpoints.

Tests:
- GET /blogs - List blogs
- POST /blogs - Create blog
- GET /blogs/{id} - Get blog details
- PUT /blogs/{id} - Update blog
- DELETE /blogs/{id} - Delete blog
- POST /blogs/{id}/like - Like/unlike blog
- GET /blogs/{id}/comments - List comments
- POST /blogs/{id}/comments - Add comment
- GET /blogs/tags - List tags

Usage:
    python -m test_api.test_blog
"""

import asyncio
import io
from test_base import BaseTest, run_test_module
from test_file_generator import TestFileGenerator


class TestBlogAPIs(BaseTest):
    """Test class for blog-related API endpoints."""
    
    def __init__(self):
        super().__init__("Blog APIs")
        self.created_blog_id = None
    
    async def test_list_blogs(self):
        """Test GET /blogs endpoint."""
        try:
            response = await self.client.get(
                "/blogs",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result("GET /blogs", True, f"Found {len(data['items'])} blogs")
            else:
                self._log_result("GET /blogs", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /blogs", False, str(e))
    
    async def test_get_blog_stats(self):
        """Test GET /blogs/stats endpoint."""
        try:
            response = await self.client.get(
                "/blogs/stats",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "total_posts" in data
                self._log_result("GET /blogs/stats", True, f"Stats retrieved")
            else:
                self._log_result("GET /blogs/stats", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /blogs/stats", False, str(e))
    
    async def test_get_my_blogs(self):
        """Test GET /blogs/my endpoint."""
        try:
            response = await self.client.get(
                "/blogs/my",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result("GET /blogs/my", True, f"Found {len(data['items'])} my blogs")
            else:
                self._log_result("GET /blogs/my", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /blogs/my", False, str(e))
    
    async def test_create_blog(self):
        """Test POST /blogs endpoint."""
        try:
            # Generate test markdown file
            md_file = TestFileGenerator.create_markdown_file(
                filename=f"test_blog_{asyncio.get_event_loop().time()}.md",
                title="Test Blog Post"
            )
            
            with open(md_file, 'rb') as f:
                files = {
                    "content_file": (md_file.name, f, "text/markdown"),
                }
                data = {
                    "title": "Test Blog Post",
                    "content_type": "markdown",
                    "is_published": "true",
                    "tags": "test,api"
                }
                
                response = await self.client.post(
                    "/blogs",
                    files=files,
                    data=data,
                    headers=self._get_headers()
                )
            
            if response.status_code == 201:
                blog_data = response.json()
                self.created_blog_id = blog_data["blog_id"]
                self._log_result("POST /blogs", True, f"Created blog ID: {self.created_blog_id}")
            else:
                self._log_result("POST /blogs", False, f"Status: {response.status_code} - {response.text}")
        except Exception as e:
            self._log_result("POST /blogs", False, str(e))
    
    async def test_get_blog(self):
        """Test GET /blogs/{id} endpoint."""
        blog_id = self.created_blog_id or self.get_first_blog_id()
        
        if not blog_id:
            self._log_result("GET /blogs/{id}", False, "No blog available")
            return
        
        try:
            response = await self.client.get(
                f"/blogs/{blog_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["blog_id"] == blog_id
                self._log_result(f"GET /blogs/{blog_id}", True, "Blog retrieved")
            else:
                self._log_result(f"GET /blogs/{blog_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /blogs/{blog_id}", False, str(e))
    
    async def test_like_blog(self):
        """Test POST /blogs/{id}/like endpoint."""
        blog_id = self.created_blog_id or self.get_first_blog_id()
        
        if not blog_id:
            self._log_result("POST /blogs/{id}/like", False, "No blog available")
            return
        
        try:
            response = await self.client.post(
                f"/blogs/{blog_id}/like",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "has_liked" in data
                self._log_result(f"POST /blogs/{blog_id}/like", True, f"Liked: {data['has_liked']}")
            else:
                self._log_result(f"POST /blogs/{blog_id}/like", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"POST /blogs/{blog_id}/like", False, str(e))
    
    async def test_get_like_status(self):
        """Test GET /blogs/{id}/like endpoint."""
        blog_id = self.created_blog_id or self.get_first_blog_id()
        
        if not blog_id:
            self._log_result("GET /blogs/{id}/like", False, "No blog available")
            return
        
        try:
            response = await self.client.get(
                f"/blogs/{blog_id}/like",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "has_liked" in data
                self._log_result(f"GET /blogs/{blog_id}/like", True, f"Has liked: {data['has_liked']}")
            else:
                self._log_result(f"GET /blogs/{blog_id}/like", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /blogs/{blog_id}/like", False, str(e))
    
    async def test_list_tags(self):
        """Test GET /blogs/tags endpoint."""
        try:
            response = await self.client.get(
                "/blogs/tags",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result("GET /blogs/tags", True, f"Found {len(data['items'])} tags")
            else:
                self._log_result("GET /blogs/tags", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /blogs/tags", False, str(e))
    
    async def test_add_comment(self):
        """Test POST /blogs/{id}/comments endpoint."""
        blog_id = self.created_blog_id or self.get_first_blog_id()
        
        if not blog_id:
            self._log_result("POST /blogs/{id}/comments", False, "No blog available")
            return
        
        try:
            response = await self.client.post(
                f"/blogs/{blog_id}/comments",
                json={"content": "Test comment from API test"},
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                assert "comment_id" in data
                self._log_result(f"POST /blogs/{blog_id}/comments", True, f"Comment ID: {data['comment_id']}")
            else:
                self._log_result(f"POST /blogs/{blog_id}/comments", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"POST /blogs/{blog_id}/comments", False, str(e))
    
    async def test_list_comments(self):
        """Test GET /blogs/{id}/comments endpoint."""
        blog_id = self.created_blog_id or self.get_first_blog_id()
        
        if not blog_id:
            self._log_result("GET /blogs/{id}/comments", False, "No blog available")
            return
        
        try:
            response = await self.client.get(
                f"/blogs/{blog_id}/comments",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result(f"GET /blogs/{blog_id}/comments", True, f"Found {len(data['items'])} comments")
            else:
                self._log_result(f"GET /blogs/{blog_id}/comments", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /blogs/{blog_id}/comments", False, str(e))
    
    async def test_delete_blog(self):
        """Test DELETE /blogs/{id} endpoint (cleanup)."""
        # Only delete blogs we created in this test session
        if not self.created_blog_id:
            self._log_result("DELETE /blogs/{id}", True, "Skipped (no test blog created)")
            return
        
        try:
            response = await self.client.delete(
                f"/blogs/{self.created_blog_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 204:
                self._log_result(f"DELETE /blogs/{self.created_blog_id}", True, "Blog deleted")
            else:
                self._log_result(f"DELETE /blogs/{self.created_blog_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"DELETE /blogs/{self.created_blog_id}", False, str(e))


async def main():
    """Run all blog API tests."""
    success = await run_test_module(TestBlogAPIs, "Blog APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
