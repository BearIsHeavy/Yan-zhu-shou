"""
Book Parser Service.

Parses book content and extracts knowledge structure.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from ai_analysis.llm_client import LLMClient
from ai_analysis.config import AIAnalysisConfig

logger = logging.getLogger(__name__)


class BookParserService:
    """Service for parsing book content."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize book parser service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm = LLMClient() if AIAnalysisConfig.is_available() else None

    @staticmethod
    def _read_pdf(file_path: str) -> Optional[str]:
        """Read PDF file content."""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text_parts.append(page.extract_text())
            
            return '\n'.join(text_parts)
            
        except ImportError:
            logger.warning("pypdf not installed. PDF parsing unavailable.")
            return None
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            return None
    
    @staticmethod
    def _read_markdown(file_path: str) -> Optional[str]:
        """Read Markdown file content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _read_docx(file_path: str) -> Optional[str]:
        """Read DOCX file content."""
        try:
            from docx import Document

            doc = Document(file_path)
            text_parts = []

            for paragraph in doc.paragraphs:
                text_parts.append(paragraph.text)

            return '\n'.join(text_parts)

        except ImportError:
            logger.warning("python-docx not installed. DOCX parsing unavailable.")
            return None
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            return None

    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        Read file content based on file type.

        Args:
            file_path: Path to the file

        Returns:
            File content as string or None
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.pdf':
                return self._read_pdf(file_path)
            elif ext in ['.md', '.markdown']:
                return self._read_markdown(file_path)
            elif ext == '.docx':
                return self._read_docx(file_path)
            else:
                logger.error(f"Unsupported file type: {ext}")
                return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    @staticmethod
    def extract_chapters_markdown(content: str) -> List[Dict[str, Any]]:
        """
        Extract chapter structure from Markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of chapter dicts
        """
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for chapter heading (# Chapter Title)
            if line.startswith('# '):
                # Save previous chapter
                if current_chapter:
                    chapters.append({
                        "title": current_chapter,
                        "content": '\n'.join(current_content),
                        "level": 1,
                    })
                
                current_chapter = line[2:].strip()
                current_content = []
            
            # Check for subheading (## Section Title)
            elif line.startswith('## ') and current_chapter:
                current_content.append(line)
            
            # Regular content
            elif current_chapter:
                current_content.append(line)
        
        # Save last chapter
        if current_chapter:
            chapters.append({
                "title": current_chapter,
                "content": '\n'.join(current_content),
                "level": 1,
            })
        
        return chapters
    
    async def extract_knowledge_tree(
        self,
        content: str,
        subject: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract knowledge tree from book content using AI.
        
        Args:
            content: Book content
            subject: Optional subject context
            
        Returns:
            Knowledge tree structure or None
        """
        if not self.llm:
            logger.info("AI not available for knowledge extraction")
            return None
        
        # Limit content length for API
        max_content_length = 10000
        truncated_content = content[:max_content_length]
        
        system_prompt = """Extract a hierarchical knowledge tree from the educational content.
Return a JSON structure:
{
    "subject": "subject name",
    "topics": [
        {
            "name": "topic name",
            "subtopics": [...],
            "key_concepts": ["concept1", "concept2"]
        }
    ]
}"""
        
        user_prompt = f"""Extract knowledge tree from this {'subject: ' + subject if subject else ''} content:

{truncated_content}...

Return the knowledge tree in JSON format."""
        
        try:
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            
            # Parse JSON response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            knowledge_tree = json.loads(response.strip())
            return knowledge_tree
            
        except Exception as e:
            logger.error(f"Knowledge extraction failed: {e}")
            return None
    
    async def parse_book(
        self,
        file_path: str,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse a book and extract knowledge structure.
        
        Args:
            file_path: Path to the book file
            subject: Optional subject context
            
        Returns:
            Parsing result with chapters and knowledge tree
        """
        # Read content
        content = self.read_file_content(file_path)
        
        if not content:
            return {
                "success": False,
                "error": "Failed to read file content",
            }
        
        result = {
            "success": True,
            "content_length": len(content),
            "chapters": [],
            "knowledge_tree": None,
        }
        
        # Extract chapters based on file type
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.md', '.markdown']:
            result["chapters"] = self.extract_chapters_markdown(content)
            result["chapter_count"] = len(result["chapters"])
        
        # Extract knowledge tree using AI
        if AIAnalysisConfig.is_available():
            knowledge_tree = await self.extract_knowledge_tree(content, subject)
            result["knowledge_tree"] = knowledge_tree
        
        return result
