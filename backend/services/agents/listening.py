from typing import Optional
from pydantic import BaseModel, Field
from services.agents.base import BaseAgent
from services.agents.registry import registry
from shared.schemas import ExamOutput
from shared.parsing import parse_json_from_response

class ListeningErrorAnalysisResult(BaseModel):
    mistake_type: str
    why_wrong: str
    correct_strategy: str
    evidence_text: str

@registry.register
class ListeningAgent(BaseAgent):
    name = "ListeningAgent"
    description = "Handles listening transcript generation and error analysis."

    async def generate_listening_section(self, section: int, accent: str, speed: str, topic: str, weakness_focus: list, question_types: list, question_count: int) -> ExamOutput:
        question_types_desc = ", ".join(question_types)

        prompt = f"""You are an expert IELTS examiner. Generate a realistic IELTS Listening Section {section} script and questions.

TARGET SPECIFICATIONS:
- Section: {section}
- Accent: {accent}
- Speaking speed: {speed}
- Topic: {topic}
- Weakness focus areas: {', '.join(weakness_focus) if weakness_focus else 'none'}

SECTION CONTEXT:
- Section 1: Everyday social context (e.g., booking a hotel, enrolling in a course)
- Section 2: Social/monologue context (e.g., tour guide, information about an event)
- Section 3: Educational/training context (e.g., tutorial discussion, group project)
- Section 4: Academic lecture context

REQUIREMENTS:
1. Create a realistic dialogue or monologue (~{300 + section * 100} words) with natural speech patterns
2. Include speaker labels (e.g., "WOMAN:", "MAN:", "LECTURER:")
3. The transcript should have natural hesitations and connectors
4. Generate {question_count} questions of types: {question_types_desc}
5. For each question provide:
   - The question text (prompt_text)
   - Options if applicable (for MULTIPLE_CHOICE, MATCHING)
   - The correct answer
   - Evidence text from the transcript
   - Analysis of why students might choose wrong answer

6. For FILL_BLANK: The answer should be a word or short phrase from the transcript
7. For MULTIPLE_CHOICE: Provide options A-D

The passage (for schema compatibility) should contain a single paragraph with the full script text.
Use paragraph_id "S1" for the script.

Return JSON matching the ExamOutput schema."""

        return await self.run_structured(
            prompt=prompt,
            schema=ExamOutput,
            temperature=0.0
        )

    async def analyze_wrong_answer(self, transcript: str, question_text: str, correct_answer: str, user_answer: str, default_evidence: str = "") -> ListeningErrorAnalysisResult:
        prompt = f"""Analyze this IELTS listening mistake and provide targeted feedback.

TRANSCRIPT:
{transcript[:1500]}

QUESTION:
{question_text}

CORRECT ANSWER: {correct_answer}
USER'S ANSWER: {user_answer}

The correct answer appears in the transcript. Analyze the mistake and return JSON:
{{
    "mistake_type": "Spelling | Misheard | Similar_Sound | Wrong_Speaker | Timing",
    "why_wrong": "Explain in 1-2 sentences why the user chose this wrong answer",
    "correct_strategy": "Give a specific listening strategy to avoid this mistake",
    "evidence_text": "The exact section of the transcript where the answer appears"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = await self.run_text(prompt=prompt, temperature=0.3)
            result = parse_json_from_response(response)
            if result:
                return ListeningErrorAnalysisResult(**result)
        except Exception:
            pass

        return ListeningErrorAnalysisResult(
            mistake_type="Misheard",
            why_wrong=f"You answered '{user_answer}' but the correct answer is '{correct_answer}'.",
            correct_strategy="Listen more carefully for the specific information requested.",
            evidence_text=default_evidence
        )
