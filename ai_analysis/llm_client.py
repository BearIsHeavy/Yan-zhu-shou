"""
LLM Client for AI model interactions.

Supports OpenAI-compatible APIs including:
- OpenAI GPT models
- Azure OpenAI
- Self-hosted models (vLLM, Ollama, etc.)
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx

from ai_analysis.config import AIAnalysisConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM APIs."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key (defaults to env OPENAI_API_KEY)
            model: Model name (defaults to env OPENAI_MODEL)
            base_url: API base URL (defaults to OpenAI)
        """
        self.api_key = api_key or AIAnalysisConfig.OPENAI_API_KEY
        self.model = model or AIAnalysisConfig.OPENAI_MODEL
        self.base_url = base_url or AIAnalysisConfig.OPENAI_BASE_URL
        self.max_tokens = AIAnalysisConfig.MAX_TOKENS
        self.temperature = AIAnalysisConfig.TEMPERATURE
        self.max_retries = AIAnalysisConfig.MAX_RETRIES
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            
        Returns:
            AI response text
        """
        if not AIAnalysisConfig.is_available():
            raise RuntimeError("AI analysis is not available (missing API key)")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        url = f"{self.base_url}/chat/completions"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    logger.info(
                        f"LLM request completed: "
                        f"model={self.model}, "
                        f"tokens={data.get('usage', {})}"
                    )
                    
                    return content
                    
            except httpx.HTTPError as e:
                logger.error(f"LLM API request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def analyze_weak_points(
        self,
        wrong_questions: List[Dict[str, Any]],
        knowledge_tree: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Analyze user's weak points from wrong questions.
        
        Args:
            wrong_questions: List of wrong question data
            knowledge_tree: Optional knowledge tree structure
            
        Returns:
            Analysis result with weak points and statistics
        """
        # Build prompt
        system_prompt = """You are an expert educational analyst. 
Analyze the student's wrong answers and identify:
1. Knowledge gaps
2. Common error patterns
3. Difficulty areas
4. Learning recommendations

Respond in JSON format with this structure:
{
    "weak_points": [
        {"knowledge": "name", "error_count": N, "confidence": 0.0-1.0}
    ],
    "error_patterns": ["pattern1", "pattern2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "summary": "brief summary"
}"""
        
        # Format wrong questions for analysis
        questions_text = "\n".join([
            f"- Q{q['question_no']}: {q['category']} - {q['stem'][:100]}... "
            f"(Your answer: {q['user_answer']}, Correct: {q['correct_ans_summary']})"
            for q in wrong_questions[:20]  # Limit to 20 questions
        ])
        
        user_prompt = f"""Please analyze these wrong questions:

{questions_text}

{f'Knowledge tree context: {json.dumps(knowledge_tree)}' if knowledge_tree else ''}

Provide your analysis in JSON format."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = await self.chat(messages)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            result = json.loads(response.strip())
            result["analyzed_at"] = datetime.utcnow().isoformat()
            result["questions_analyzed"] = len(wrong_questions)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "weak_points": [],
                "error_patterns": ["Unable to analyze"],
                "recommendations": ["Please try again"],
                "summary": "Analysis failed",
                "analyzed_at": datetime.utcnow().isoformat(),
                "questions_analyzed": len(wrong_questions),
            }
    
    async def extract_knowledge_points(
        self,
        text: str,
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract knowledge points from text.
        
        Args:
            text: Text content to analyze
            subject: Optional subject context
            
        Returns:
            List of extracted knowledge points
        """
        system_prompt = """Extract knowledge points from the given text.
Return a JSON list with structure:
[
    {"name": "point name", "description": "brief description", "difficulty": 1-5}
]"""
        
        user_prompt = f"""Extract knowledge points from this {'subject: ' + subject if subject else ''} text:

{text[:3000]}..."""  # Limit text length
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = await self.chat(messages)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
            
        except json.JSONDecodeError:
            logger.error("Failed to parse knowledge points")
            return []
    
    async def generate_recommendations(
        self,
        weak_points: List[Dict],
        user_level: str = "intermediate",
    ) -> List[Dict[str, Any]]:
        """
        Generate learning recommendations based on weak points.
        
        Args:
            weak_points: List of identified weak points
            user_level: User's current level
            
        Returns:
            List of personalized recommendations
        """
        system_prompt = """Generate personalized learning recommendations.
Return JSON list:
[
    {
        "type": "practice|review|study",
        "priority": 1-5,
        "knowledge": "target knowledge",
        "action": "specific action",
        "estimated_time": "e.g., 30 minutes"
    }
]"""
        
        weak_points_text = "\n".join([
            f"- {p.get('knowledge', 'Unknown')}: {p.get('error_count', 0)} errors"
            for p in weak_points
        ])
        
        user_prompt = f"""User level: {user_level}

Weak points:
{weak_points_text}

Generate 5-10 personalized recommendations."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = await self.chat(messages)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
            
        except json.JSONDecodeError:
            logger.error("Failed to parse recommendations")
            return []


# Import asyncio for retry logic
import asyncio
