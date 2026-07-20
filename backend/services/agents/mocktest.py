import json
import logging
from typing import Optional
from services.agents.base import BaseAgent
from services.agents.registry import registry
from pydantic import BaseModel
from shared.parsing import parse_json_from_response

logger = logging.getLogger(__name__)

class GeneratedQuestion(BaseModel):
    id: int
    text: str
    type: str
    correct_answer: str
    options: Optional[list] = None

class GeneratedListeningSection(BaseModel):
    section_number: int
    title: str
    transcript: str
    questions: list[GeneratedQuestion]

class GeneratedReadingPassage(BaseModel):
    passage_number: int
    title: str
    content: str
    word_count: int
    difficulty: str
    questions: list[GeneratedQuestion]

class GeneratedWritingTask(BaseModel):
    task_number: int
    task_type: str
    prompt: str
    chart_data: Optional[dict] = None
    min_words: int

class GeneratedSpeakingPart(BaseModel):
    part_number: int
    title: str
    questions: Optional[list[str]] = None
    cue_card: Optional[str] = None
    follow_up: Optional[str] = None
    topic: Optional[str] = None


@registry.register
class MocktestGeneratorAgent(BaseAgent):
    name = "MocktestGeneratorAgent"
    description = "Generates mock test content for all four IELTS skills."

    def _build_listening_prompt(self, config: dict) -> str:
        return f"""You are an expert IELTS examiner. Generate an IELTS Listening Section {config['section_number']} script with questions.

SPECIFICATIONS:
- Context: {config['context']}
- Difficulty: {config['difficulty']}
- Vocabulary Level: {config['vocabulary_level']}
- Grammar Complexity: {config['grammar_complexity']}
- Accent: {config['accent']} English
- Speech Rate: {config['speech_rate']}
- Number of Questions: {config['question_count']}
- Question Types: {', '.join(config['question_types'])}

REQUIREMENTS:
1. Generate a realistic transcript (~300-500 words) appropriate for the context
2. Include natural speech features (hesitations, corrections) for harder sections
3. Generate exactly {config['question_count']} questions
4. Each question must have: id (starting from {(config['section_number']-1)*10 + 1}), text, type, correct_answer
5. For MULTIPLE_CHOICE questions, include 4 options as a list
6. For FILL_BLANK questions, the answer should be 1-3 words

Return ONLY valid JSON matching this structure:
{{
  "section_number": {config['section_number']},
  "title": "...",
  "transcript": "...",
  "questions": [
    {{"id": 1, "text": "...", "type": "...", "correct_answer": "...", "options": [...]}}
  ]
}}"""

    def _build_reading_prompt(self, config: dict) -> str:
        return f"""You are an expert IELTS examiner. Generate an IELTS Reading Passage {config['passage_number']} with questions.

SPECIFICATIONS:
- Subject: {config['subject']}
- Word Count: {config['word_count']} words
- Difficulty: {config['difficulty']}
- Text Type: {config['text_type']}
- Question Types: {', '.join(config['question_types'])}

REQUIREMENTS:
1. Generate a cohesive reading passage on the subject
2. Generate 13-14 questions depending on passage number
3. Each question must have: id (starting from {(config['passage_number']-1)*13 + 1}), text, type, correct_answer
4. Types must be strictly chosen from: MATCHING_HEADINGS, TRUE_FALSE_NOT_GIVEN, MULTIPLE_CHOICE, FILL_BLANK, MATCHING_INFORMATION
5. Ensure answers are explicitly supported by the text

Return ONLY valid JSON matching this structure:
{{
  "passage_number": {config['passage_number']},
  "title": "...",
  "content": "...",
  "word_count": {config['word_count']},
  "difficulty": "{config['difficulty']}",
  "questions": [
    {{"id": 1, "text": "...", "type": "...", "correct_answer": "...", "options": [...]}}
  ]
}}"""

    def _build_writing_prompt(self, config: dict) -> str:
        base_prompt = f"""You are an expert IELTS examiner. Generate an IELTS Writing Task {config['task_number']}.

SPECIFICATIONS:
- Topic: {config['topic']}
- Task Type: {config['task_type']}
- Difficulty: {config['difficulty']}
"""
        if config['task_number'] == 1:
            base_prompt += """
REQUIREMENTS:
1. Generate a prompt describing a chart, graph, table, or diagram
2. Create sensible underlying data representing the visual information
3. Provide the data as a JSON object in 'chart_data'

Return ONLY valid JSON:
{
  "task_number": 1,
  "task_type": "...",
  "prompt": "...",
  "chart_data": {...},
  "min_words": 150
}"""
        else:
            base_prompt += """
REQUIREMENTS:
1. Generate a clear, debatable essay prompt
2. Ask the candidate to discuss both views/give opinion/solve a problem

Return ONLY valid JSON:
{
  "task_number": 2,
  "task_type": "...",
  "prompt": "...",
  "chart_data": null,
  "min_words": 250
}"""
        return base_prompt

    def _build_speaking_prompt(self, config: dict) -> str:
        if config['part_number'] == 1:
            return f"""You are an expert IELTS examiner. Generate IELTS Speaking Part 1 questions.
Topic: {config['topic']}

Return ONLY valid JSON:
{{
  "part_number": 1,
  "title": "Introduction and Interview",
  "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"]
}}"""
        elif config['part_number'] == 2:
            return f"""You are an expert IELTS examiner. Generate an IELTS Speaking Part 2 Cue Card.
Topic: {config['topic']}
Difficulty: {config['difficulty']}

Return ONLY valid JSON:
{{
  "part_number": 2,
  "title": "Long Turn",
  "cue_card": "Describe a... You should say: ... and explain why...",
  "follow_up": "One follow up question"
}}"""
        else:
            return f"""You are an expert IELTS examiner. Generate IELTS Speaking Part 3 questions.
Topic: {config['topic']}
Difficulty: {config['difficulty']}

Return ONLY valid JSON:
{{
  "part_number": 3,
  "title": "Two-way Discussion",
  "topic": "{config['topic']}",
  "questions": ["Deep Q1", "Deep Q2", "Deep Q3", "Deep Q4"]
}}"""

    async def generate_listening_sections(self, difficulty_configs: list) -> list:
        sections = []
        for config in difficulty_configs:
            prompt = self._build_listening_prompt(config)
            try:
                response = await self.run_text(prompt=prompt, temperature=0.4)
                parsed = parse_json_from_response(response)
                if parsed:
                    sections.append(parsed)
                else:
                    logger.error("Failed to parse JSON for listening section %s", config['section_number'])
            except Exception as e:
                logger.error("Listening generation failed: %s", e)
        return sections

    async def generate_reading_passages(self, difficulty_configs: list) -> list:
        passages = []
        for config in difficulty_configs:
            prompt = self._build_reading_prompt(config)
            try:
                response = await self.run_text(prompt=prompt, temperature=0.4)
                parsed = parse_json_from_response(response)
                if parsed:
                    passages.append(parsed)
                else:
                    logger.error("Failed to parse JSON for reading passage %s", config['passage_number'])
            except Exception as e:
                logger.error("Reading generation failed: %s", e)
        return passages

    async def generate_writing_tasks(self, difficulty_configs: list) -> list:
        tasks = []
        for config in difficulty_configs:
            prompt = self._build_writing_prompt(config)
            try:
                response = await self.run_text(prompt=prompt, temperature=0.4)
                parsed = parse_json_from_response(response)
                if parsed:
                    tasks.append(parsed)
                else:
                    logger.error("Failed to parse JSON for writing task %s", config['task_number'])
            except Exception as e:
                logger.error("Writing generation failed: %s", e)
        return tasks

    async def generate_speaking_parts(self, difficulty_configs: list) -> list:
        parts = []
        for config in difficulty_configs:
            prompt = self._build_speaking_prompt(config)
            try:
                response = await self.run_text(prompt=prompt, temperature=0.4)
                parsed = parse_json_from_response(response)
                if parsed:
                    parts.append(parsed)
                else:
                    logger.error("Failed to parse JSON for speaking part %s", config['part_number'])
            except Exception as e:
                logger.error("Speaking generation failed: %s", e)
        return parts


@registry.register
class MocktestEvaluatorAgent(BaseAgent):
    name = "MocktestEvaluatorAgent"
    description = "Evaluates subjective mock test answers (writing and speaking)."

    def _build_writing_evaluation_prompt(self, task: dict, user_essay: str) -> str:
        return f"""You are a strict, professional IELTS examiner. Evaluate this Writing Task {task.get('task_number', '?')}.

TASK:
{task.get('prompt', '')}

USER ESSAY:
{user_essay}

Evaluate according to official IELTS band descriptors:
1. Task Achievement / Response (TA/TR)
2. Coherence and Cohesion (CC)
3. Lexical Resource (LR)
4. Grammatical Range and Accuracy (GRA)

Return ONLY valid JSON matching this schema:
{{
  "task_achievement": 6.5,
  "coherence_cohesion": 6.0,
  "lexical_resource": 7.0,
  "grammatical_accuracy": 6.5,
  "overall_band": 6.5,
  "feedback": "Detailed paragraph of feedback highlighting strengths and weaknesses.",
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"]
}}"""

    def _build_speaking_evaluation_prompt(self, user_audio_text: str, context: str) -> str:
        return f"""You are an IELTS examiner evaluating speaking performance.
We have an automated transcript of the user's speech. Evaluate based on text features.

CONTEXT (What was asked):
{context}

USER'S TRANSCRIBED SPEECH:
{user_audio_text}

Evaluate according to official IELTS band descriptors (estimating Fluency and Pronunciation based on hesitation markers and transcription clarity):
1. Fluency and Coherence (FC)
2. Lexical Resource (LR)
3. Grammatical Range and Accuracy (GRA)
4. Pronunciation (PR - estimate based on transcription errors)

Return ONLY valid JSON matching this schema:
{{
  "fluency": 6.0,
  "lexical_resource": 6.5,
  "grammatical_accuracy": 6.0,
  "pronunciation": 6.0,
  "overall_band": 6.0,
  "feedback": "Detailed paragraph of feedback.",
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"]
}}"""

    def _build_diagnostic_prompt(self, overall_band: float, listening_band: float, reading_band: float, writing_band: float, speaking_band: float, target_band: float, q_summary: str, combined_text: str) -> str:
        return f"""You are an expert IELTS diagnostic analyst. Produce a comprehensive analysis.

SCORES:
- Overall Band: {overall_band}
- Listening: {listening_band}
- Reading: {reading_band}
- Writing: {writing_band}
- Speaking: {speaking_band}
- Target Band: {target_band}
- Gap to Target: {target_band - overall_band:.1f}

QUESTION TYPE ACCURACY:
{q_summary}

WRITING + SPEAKING TEXT SAMPLE (for vocabulary/grammar analysis):
{combined_text[:3000]}

Produce a diagnostic report. Return ONLY valid JSON:
{{
    "vocabulary_analysis": {{
        "cefr_level": "B1|B2|C1|C2",
        "lexical_diversity_score": 0-100,
        "academic_word_percentage": 0-100,
        "strengths": ["str1", "str2"],
        "weaknesses": ["str1", "str2"]
    }},
    "grammar_analysis": {{
        "error_rate": "errors_per_100_words",
        "sentence_complexity": {{"simple": 0, "compound": 0, "complex": 0}},
        "common_mistakes": ["mistake1", "mistake2"],
        "strengths": ["str1", "str2"]
    }},
    "top_strengths": ["strength1", "strength2", "strength3"],
    "key_weaknesses": ["weakness1", "weakness2", "weakness3"],
    "estimated_weeks_to_target": 4,
    "recommended_focus_areas": ["area1", "area2", "area3"],
    "study_plan_adjustments": ["adjustment1", "adjustment2", "adjustment3"],
    "summary_text": "2-3 sentence overall summary of performance and next steps"
}}"""

    async def evaluate_writing(self, task: dict, user_essay: str) -> Optional[dict]:
        prompt = self._build_writing_evaluation_prompt(task, user_essay)
        try:
            response = await self.run_text(prompt=prompt, temperature=0.2)
            parsed = parse_json_from_response(response)
            if parsed:
                return parsed
        except Exception as e:
            logger.error("Writing evaluation failed: %s", e)
        return None

    async def evaluate_speaking(self, user_audio_text: str, context: str) -> Optional[dict]:
        prompt = self._build_speaking_evaluation_prompt(user_audio_text, context)
        try:
            response = await self.run_text(prompt=prompt, temperature=0.2)
            parsed = parse_json_from_response(response)
            if parsed:
                return parsed
        except Exception as e:
            logger.error("Speaking evaluation failed: %s", e)
        return None
        
    async def evaluate_diagnostic(self, overall_band: float, listening_band: float, reading_band: float, writing_band: float, speaking_band: float, target_band: float, q_summary: str, combined_text: str) -> Optional[dict]:
        prompt = self._build_diagnostic_prompt(overall_band, listening_band, reading_band, writing_band, speaking_band, target_band, q_summary, combined_text)
        try:
            response = await self.run_text(prompt=prompt, temperature=0.3)
            parsed = parse_json_from_response(response)
            if parsed:
                return parsed
        except Exception as e:
            logger.error("AI diagnostic failed: %s", e)
        return None
