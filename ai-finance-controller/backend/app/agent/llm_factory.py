import os
import json
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from typing import List, Dict, Any

load_dotenv()

class MatchDecision(BaseModel):
    match: bool = Field(description="True if the records represent the same financial transaction, False otherwise.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reasoning_summary: str = Field(description="A short 1-sentence explanation of the decision.")
    risk_flags: List[str] = Field(description="Any discrepancies noticed, e.g., 'date mismatch', 'amount discrepancy'")

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        # Initialize Groq client only if key exists and isn't empty
        self.client = Groq(api_key=self.api_key) if self.api_key and self.api_key.strip() else None

    def analyze_ambiguous_pair(self, bank: Dict[str, Any], ledger: Dict[str, Any], similarities: Dict[str, float]) -> MatchDecision:
        semantic_score = similarities.get("semantic_similarity", 0.0)
        
        # If no API key is provided, safely fallback to the local embedding math
        if not self.client:
            is_match = semantic_score > 0.80
            return MatchDecision(
                match=is_match,
                confidence=semantic_score,
                reasoning_summary="Mocked decision (No GROQ_API_KEY found). Relied entirely on local semantic vectors.",
                risk_flags=["API_KEY_MISSING"]
            )
            
        system_prompt = "You are an expert AI financial controller. Determine if the bank transaction matches the ledger entry. Output JSON only."
        user_prompt = f"""
        Bank Record: {json.dumps(bank)}
        Ledger Record: {json.dumps(ledger)}
        Semantic Similarity Score: {semantic_score:.2f}
        
        Determine if they are a match. Return a JSON object exactly matching this schema:
        {{
            "match": true or false,
            "confidence": 0.0 to 1.0,
            "reasoning_summary": "1 sentence explanation",
            "risk_flags": ["list of discrepancies"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result_dict = json.loads(response.choices[0].message.content)
            return MatchDecision(**result_dict)
            
        except Exception as e:
            return MatchDecision(
                match=False,
                confidence=0.0,
                reasoning_summary=f"LLM Error: {str(e)}",
                risk_flags=["LLM_FAILURE"]
            )

llm_service = LLMService()