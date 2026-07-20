from typing import Optional
from pydantic import BaseModel, Field
import json
from services.agents.base import BaseAgent
from services.agents.registry import registry
from shared.schemas import ExamOutput
from shared.parsing import parse_json_from_response


class ErrorAnalysisResult(BaseModel):
    mistake_type: str
    why_wrong: str
    correct_strategy: str
    evidence_text: str


@registry.register
class ReadingAgent(BaseAgent):
    name = "ReadingAgent"
    description = "Handles reading passage generation and error analysis."

    async def generate_reading_passage(self, config_topic: str, config_difficulty: str, config_vocabulary_level: str, config_grammar_complexity: str, config_passage_length_words: int, question_types: list) -> ExamOutput:
        question_types_desc = []
        for qt in question_types:
            question_types_desc.append(f"- {qt.type}: {qt.count} questions")

        prompt = f"""You are an expert IELTS examiner. Generate an authentic IELTS Academic Reading passage and questions.

TARGET SPECIFICATIONS:
- Topic: {config_topic}
- Difficulty: {config_difficulty}
- Vocabulary Level: {config_vocabulary_level}
- Grammar Complexity: {config_grammar_complexity}
- Passage Length: approximately {config_passage_length_words} words

QUESTION TYPES TO GENERATE:
{chr(10).join(question_types_desc)}

REQUIREMENTS:
1. Create a cohesive, academic-style passage on the given topic
2. The passage should have 5-7 paragraphs, each labeled with a paragraph_id (A, B, C, D, E, F, G)
3. Generate each question type exactly as specified
4. For each question, provide:
   - The question text (prompt_text)
   - Options if applicable (for MATCHING_HEADINGS, MULTIPLE_CHOICE)
   - The correct answer
   - The paragraph where the answer can be found (paragraph_anchor_id)
   - Evidence text from the passage (evidence_text)
   - Analysis of why students might choose the wrong answer (cognitive_distractor_analysis)

5. For TRUE_FALSE_NOT_GIVEN: Options should be ["True", "False", "Not Given"]
6. For MATCHING_HEADINGS: Provide a list of headings as options, one correct per question
7. For SUMMARY_COMPLETION: Provide a summary text with blanks, and the correct word for each blank

Return the output as a valid JSON matching the ExamOutput schema."""

        return await self.run_structured(
            prompt=prompt,
            schema=ExamOutput,
            temperature=0.0
        )

    async def generate_error_analysis(self, passage_content: str, question_text: str, correct_answer: str, user_answer: str, default_evidence: str = "") -> ErrorAnalysisResult:
        prompt = f"""Analyze this IELTS reading mistake and provide targeted feedback.

PASSAGE (excerpt):
{passage_content[:1000]}...

QUESTION:
{question_text}

CORRECT ANSWER: {correct_answer}
USER'S ANSWER: {user_answer}

Analyze the mistake and return JSON with these fields:
{{
    "mistake_type": "Inference | Vocabulary | Distractor | Skim-Scan | Detail",
    "why_wrong": "Explain in 1-2 sentences why the user chose this wrong answer",
    "correct_strategy": "Give a specific reading strategy to avoid this mistake next time",
    "evidence_text": "The exact sentence from the passage that proves the correct answer"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.run_text(prompt=prompt, temperature=0.3)
            result = parse_json_from_response(response)
            if result:
                return ErrorAnalysisResult(**result)
        except Exception:
            pass
        
        return ErrorAnalysisResult(
            mistake_type="Inference",
            why_wrong=f"You answered '{user_answer}' but the correct answer is '{correct_answer}'.",
            correct_strategy="Read the relevant paragraph more carefully and look for keywords that indicate the correct answer.",
            evidence_text=default_evidence
        )
