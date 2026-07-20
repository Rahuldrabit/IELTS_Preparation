from pydantic import BaseModel, Field
from typing import List
from services.agents.base import BaseAgent
from services.agents.registry import registry

class ContextDefinition(BaseModel):
    context_definition: str = Field(..., description="Definition specific to this context")
    examples: List[str] = Field(..., description="2 example sentences using this word in similar contexts")
    synonyms: List[str] = Field(..., description="3 synonyms appropriate for this usage")
    cefr: str = Field(default="B2", description="The CEFR level (A1-C2) for this word")


@registry.register
class VocabularyAgent(BaseAgent):
    name = "VocabularyAgent"
    description = "Provides context-specific vocabulary definitions and enrichment for IELTS."

    async def generate_context_definition(self, word: str, context_sentence: str) -> ContextDefinition:
        prompt = f"""You are an IELTS vocabulary expert.

WORD: {word}
CONTEXT: "{context_sentence}"

Provide:
1. A definition of "{word}" as it's used in this specific context
2. 2 example sentences using this word in similar contexts
3. 3 synonyms appropriate for this usage
4. The CEFR level (A1-C2) for this word
"""
        return await self.run_structured(
            prompt=prompt,
            schema=ContextDefinition,
            temperature=0.3
        )

    async def enrich_word(self, word: str) -> dict:
        prompt = f"""Provide detailed vocabulary information for the word "{word}".
Return JSON with: pronunciation, meaning, definition, examples[], synonyms[], antonyms[], collocations[], word_family[], cefr (A1-C2), ielts_frequency (1-10)"""
        response = await self.run_text(prompt=prompt, temperature=0.3)
        from shared.parsing import parse_json_from_response
        data = parse_json_from_response(response)
        if data:
            data["word"] = word
            data["examples"] = data.get("examples", [])
            data["synonyms"] = data.get("synonyms", [])
            data["antonyms"] = data.get("antonyms", [])
            data["collocations"] = data.get("collocations", [])
            data["word_family"] = data.get("word_family", [])
            data["ielts_frequency"] = data.get("ielts_frequency", 5)
            return data
        return {
            "word": word,
            "pronunciation": "",
            "meaning": "",
            "definition": "",
            "examples": [],
            "synonyms": [],
            "antonyms": [],
            "collocations": [],
            "word_family": [],
            "ielts_frequency": 5,
            "cefr": "B2",
        }
