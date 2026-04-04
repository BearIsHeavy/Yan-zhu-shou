"""
RAG Enhancer.

Retrieval-Augmented Generation for enhanced AI responses.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ai_analysis.llm_client import LLMClient
from rag.services.retrieval_service import RetrievalService
from rag.config import RAGConfig

logger = logging.getLogger(__name__)

# System prompts for different tasks
SYSTEM_PROMPTS = {
    "analysis": """You are an expert educational analyst. Analyze the student's wrong answers using the provided textbook content and knowledge points.

Your analysis should:
1. Identify specific knowledge gaps based on the retrieved materials
2. Reference specific textbook pages and sections
3. Explain common misconceptions
4. Provide actionable learning recommendations

Be specific and cite sources from the provided context.""",

    "recommendation": """You are a personalized learning advisor. Generate study recommendations based on the student's weak points and available learning materials.

Your recommendations should:
1. Prioritize topics by importance and difficulty
2. Reference specific textbook sections to review
3. Suggest specific practice problems
4. Provide estimated study times
5. Create a logical learning progression

Be practical and actionable.""",

    "qa": """You are a helpful teaching assistant. Answer student questions using the provided textbook content and knowledge base.

Your answers should:
1. Directly answer the question
2. Cite specific textbook pages and sections
3. Provide relevant examples
4. Link to related concepts
5. Suggest practice problems if applicable

If the answer is not in the provided context, say so clearly."""
}


class RAGEnhancer:
    """
    RAG (Retrieval-Augmented Generation) Enhancer.
    
    Enhances AI responses by retrieving relevant context from:
    - Knowledge points
    - Textbook content
    - User's learning history
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize RAG enhancer.
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm = LLMClient()
        self.retrieval = RetrievalService(db)
        self.max_context_tokens = RAGConfig.MAX_CONTEXT_TOKENS
    
    async def analyze_wrong_questions_with_rag(
        self,
        wrong_questions: List[Dict[str, Any]],
        user_id: int,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze wrong questions with RAG enhancement.
        
        Args:
            wrong_questions: List of wrong question data
            user_id: User ID
            subject: Optional subject filter
            
        Returns:
            Enhanced analysis result
        """
        # 1. Extract keywords from wrong questions
        keywords = self._extract_keywords(wrong_questions)
        
        # 2. Retrieve relevant knowledge
        knowledge_results = await self.retrieval.search_similar_knowledge(
            query=keywords,
            limit=10,
            subject=subject
        )
        
        # 3. Retrieve relevant textbook content
        document_results = await self.retrieval.search_similar_documents(
            query=keywords,
            limit=10
        )
        
        # 4. Build context
        context = self._build_context(
            knowledge=knowledge_results,
            documents=document_results
        )
        
        # 5. Generate analysis with LLM
        analysis = await self._generate_analysis(
            wrong_questions=wrong_questions,
            context=context,
            user_id=user_id
        )
        
        # 6. Log query
        await self.retrieval.log_query(
            user_id=user_id,
            query=keywords,
            results_count=len(knowledge_results) + len(document_results),
            response_type="analysis"
        )
        
        return analysis
    
    def _extract_keywords(self, wrong_questions: List[Dict]) -> str:
        """Extract search keywords from wrong questions."""
        # Extract categories and key terms
        categories = set()
        stems = []
        
        for q in wrong_questions[:10]:  # Limit to 10 questions
            if 'category' in q:
                categories.add(q['category'])
            if 'stem' in q:
                stems.append(q['stem'][:100])  # First 100 chars
        
        # Combine into search query
        keywords = " ".join(categories) + " " + " ".join(stems)
        return keywords[:500]  # Limit length
    
    def _build_context(
        self,
        knowledge: List[Dict],
        documents: List[Dict]
    ) -> Dict[str, Any]:
        """Build context from retrieved results."""
        context = {
            "knowledge_points": [],
            "textbook_content": [],
            "sources": []
        }
        
        # Add knowledge points
        for kp in knowledge[:5]:
            context["knowledge_points"].append({
                "name": kp.get('name', 'Unknown'),
                "subject": kp.get('subject', 'Unknown'),
                "description": kp.get('description', ''),
                "similarity": kp.get('similarity', 0)
            })
        
        # Add textbook content
        for doc in documents[:5]:
            context["textbook_content"].append({
                "book_title": doc.get('book_title', 'Unknown'),
                "chapter": doc.get('chapter', ''),
                "page": doc.get('page_number'),
                "content": doc.get('content', '')[:500],  # Limit content
                "similarity": doc.get('similarity', 0)
            })
            
            # Track sources
            if doc.get('book_title') and doc.get('page_number'):
                context["sources"].append({
                    "title": doc.get('book_title'),
                    "chapter": doc.get('chapter'),
                    "page": doc.get('page_number')
                })
        
        return context
    
    async def _generate_analysis(
        self,
        wrong_questions: List[Dict],
        context: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Generate analysis using LLM with RAG context."""
        # Format questions
        questions_text = "\n".join([
            f"- Q{q.get('question_no', '?')}: {q.get('category', 'Unknown')} - {q.get('stem', '')[:100]}...\n"
            f"  Your answer: {q.get('user_answer', 'N/A')}\n"
            f"  Correct: {q.get('correct_ans_summary', 'N/A')}"
            for q in wrong_questions[:15]
        ])
        
        # Format context
        knowledge_text = "\n".join([
            f"• {kp['name']} ({kp['subject']}): {kp['description']}"
            for kp in context["knowledge_points"]
        ])
        
        textbook_text = "\n".join([
            f"📖 {doc['book_title']} - {doc['chapter']} (P.{doc['page']}):\n{doc['content']}"
            for doc in context["textbook_content"]
        ])
        
        # Build prompt
        user_prompt = f"""Based on the following textbook content and knowledge points, analyze the student's wrong answers:

【Related Knowledge Points】
{knowledge_text if knowledge_text else "No relevant knowledge points found."}

【Textbook Content】
{textbook_text if textbook_text else "No relevant textbook content found."}

【Student's Wrong Answers】
{questions_text}

Please provide:
1. Specific knowledge gaps identified
2. Reference to textbook sections
3. Common misconceptions
4. Actionable learning recommendations

Respond in JSON format:
{{
    "weak_points": [
        {{"knowledge": "name", "description": "desc", "textbook_ref": "book P.page", "error_count": N}}
    ],
    "error_patterns": ["pattern1", "pattern2"],
    "recommendations": [
        {{"type": "review|practice", "action": "specific action", "reference": "textbook ref", "estimated_time": "X minutes"}}
    ],
    "summary": "brief summary"
}}"""
        
        # Call LLM
        response = await self.llm.chat([
            {"role": "system", "content": SYSTEM_PROMPTS["analysis"]},
            {"role": "user", "content": user_prompt}
        ])
        
        # Parse JSON response
        try:
            analysis = self._parse_json_response(response)
            analysis["context_used"] = {
                "knowledge_points_count": len(context["knowledge_points"]),
                "textbook_chunks_count": len(context["textbook_content"]),
                "sources": context["sources"]
            }
            return analysis
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {
                "weak_points": [],
                "error_patterns": ["Analysis failed"],
                "recommendations": ["Please try again"],
                "summary": "Failed to generate analysis",
                "error": str(e)
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response using the robust parser."""
        return self.llm.parse_json_response(response) or {}
    
    async def answer_question_with_rag(
        self,
        question: str,
        user_id: int,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a student question using RAG.
        
        Args:
            question: Student's question
            user_id: User ID
            subject: Optional subject filter
            
        Returns:
            Answer with citations
        """
        # Retrieve relevant content
        results = await self.retrieval.hybrid_search(
            query=question,
            limit=5,
            subject=subject
        )
        
        # Build context
        context = self._build_context(
            knowledge=results.get('knowledge', []),
            documents=results.get('documents', [])
        )
        
        # Generate answer
        user_prompt = f"""Answer the student's question using the provided context.

【Question】
{question}

【Context from Knowledge Base】
{self._format_knowledge_context(context['knowledge_points'])}

【Context from Textbooks】
{self._format_document_context(context['textbook_content'])}

Please provide a clear, helpful answer with citations to specific textbook pages."""
        
        response = await self.llm.chat([
            {"role": "system", "content": SYSTEM_PROMPTS["qa"]},
            {"role": "user", "content": user_prompt}
        ])
        
        # Log query
        await self.retrieval.log_query(
            user_id=user_id,
            query=question,
            results_count=len(results.get('knowledge', [])) + len(results.get('documents', [])),
            response_type="qa"
        )
        
        return {
            "question": question,
            "answer": response,
            "sources": context["sources"],
            "confidence": "high" if context["knowledge_points"] else "medium"
        }
    
    def _format_knowledge_context(self, knowledge_points: List[Dict]) -> str:
        """Format knowledge points for context."""
        if not knowledge_points:
            return "No relevant knowledge points found."
        return "\n".join([f"• {kp['name']}: {kp['description']}" for kp in knowledge_points])
    
    def _format_document_context(self, documents: List[Dict]) -> str:
        """Format documents for context."""
        if not documents:
            return "No relevant textbook content found."
        return "\n".join([f"📖 {doc['book_title']} P.{doc.get('page', '?')}: {doc['content'][:200]}" for doc in documents])
