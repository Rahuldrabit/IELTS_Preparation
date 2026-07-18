"""
AI-powered content generation for mock tests.
Generates progressive difficulty content for each section.
"""
import asyncio
import json
import logging
from typing import Optional

from pydantic import BaseModel, Field

from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
from services.mocktest.baseline_data import (
    LISTENING_DIFFICULTY,
    READING_DIFFICULTY,
    WRITING_DIFFICULTY,
    SPEAKING_DIFFICULTY,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic schemas for AI generation output
# ═══════════════════════════════════════════════════════════════════════════════

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


class GeneratedMockTestContent(BaseModel):
    """Full generated mock test content."""
    listening: dict
    reading: dict
    writing: dict
    speaking: dict


# ═══════════════════════════════════════════════════════════════════════════════
# LISTENING GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_listening_prompt(config: dict) -> str:
    """Build AI prompt for generating one listening section."""
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

Return ONLY valid JSON with this structure:
{{
    "section_number": {config['section_number']},
    "title": "descriptive title",
    "transcript": "full transcript text",
    "questions": [
        {{"id": N, "text": "question text", "type": "FILL_BLANK|MULTIPLE_CHOICE|MATCHING|SENTENCE_COMPLETION|SUMMARY_COMPLETION", "correct_answer": "answer", "options": null_or_list}}
    ]
}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# READING GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_reading_prompt(config: dict) -> str:
    """Build AI prompt for generating one reading passage with questions."""
    q_start_id = sum(
        READING_DIFFICULTY[i]["question_count"]
        for i in range(config["passage_number"] - 1)
    ) + 1

    return f"""You are an expert IELTS Academic examiner. Generate an IELTS Reading passage with questions.

SPECIFICATIONS:
- Passage Number: {config['passage_number']} of 3
- Difficulty: {config['difficulty']}
- Vocabulary Level: {config['vocabulary_level']}
- Grammar Complexity: {config['grammar_complexity']}
- Topic Area: {config['topic']}
- Target Length: approximately {config['passage_length_words']} words
- Number of Questions: {config['question_count']}
- Question Types: {', '.join(config['question_types'])}

REQUIREMENTS:
1. Write a cohesive academic passage with 5-7 paragraphs labeled A through G
2. Vocabulary should match the specified level:
   - basic: everyday words, simple academic terms
   - academic: B2-C1 academic vocabulary
   - c1: advanced academic, specialized terminology
3. Grammar complexity should match:
   - simple: mainly simple and compound sentences
   - medium: mix of sentence types, some subordination
   - complex: heavy subordination, nominalization, passive constructions
4. Generate exactly {config['question_count']} questions
5. Question IDs start from {q_start_id}
6. For TRUE_FALSE_NOT_GIVEN: options = ["True", "False", "Not Given"]
7. For MULTIPLE_CHOICE: provide 4 options (A, B, C, D)
8. For MATCHING_HEADINGS: options = paragraph labels ["A","B","C","D","E","F","G"]
9. For FILL_BLANK/SENTENCE_COMPLETION/SUMMARY_COMPLETION: answer is 1-3 words from text

Return ONLY valid JSON:
{{
    "passage_number": {config['passage_number']},
    "title": "passage title",
    "difficulty": "{config['difficulty']}",
    "content": "full passage text with paragraph labels (A. ... B. ... etc.)",
    "word_count": approximate_word_count,
    "questions": [
        {{"id": N, "text": "question", "type": "TYPE", "correct_answer": "answer", "options": null_or_list}}
    ]
}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# WRITING GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_writing_prompt(config: dict) -> str:
    """Build AI prompt for generating a writing task."""
    if config["task_type"] == "task_1":
        return f"""You are an expert IELTS examiner. Generate an IELTS Academic Writing Task 1 prompt.

REQUIREMENTS:
1. Create a data visualization description task (bar chart, line graph, pie chart, or table)
2. The prompt should ask the candidate to describe and compare data
3. Include chart_data as JSON that describes the visualization:
   - type: "bar" | "line" | "pie" | "table"
   - title: chart title
   - categories: x-axis labels
   - series: list of data series with name and data values
4. Minimum words: {config['min_words']}

Return ONLY valid JSON:
{{
    "task_number": 1,
    "task_type": "task_1",
    "prompt": "full task prompt text including instructions",
    "chart_data": {{chart data object}},
    "min_words": {config['min_words']}
}}"""
    else:
        return f"""You are an expert IELTS examiner. Generate an IELTS Academic Writing Task 2 prompt.

REQUIREMENTS:
1. Create an essay question (discuss both views, agree/disagree, problem/solution, or advantages/disadvantages)
2. The topic should be academically relevant and thought-provoking
3. Include clear instructions about what the candidate should address
4. Minimum words: {config['min_words']}

Return ONLY valid JSON:
{{
    "task_number": 2,
    "task_type": "task_2",
    "prompt": "full task prompt text",
    "chart_data": null,
    "min_words": {config['min_words']}
}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# SPEAKING GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_speaking_prompt(config: dict) -> str:
    """Build AI prompt for generating speaking section content."""
    part = config["part_number"]

    if part == 1:
        return """You are an expert IELTS examiner. Generate IELTS Speaking Part 1 questions.

REQUIREMENTS:
1. Generate 5 introduction/general questions on 2 familiar topics
2. Questions should be natural and conversational
3. Topics: choose from home, work, studies, hobbies, food, weather, travel, technology

Return ONLY valid JSON:
{
    "part_number": 1,
    "title": "Introduction and General Questions",
    "questions": ["question1", "question2", "question3", "question4", "question5"]
}"""
    elif part == 2:
        return """You are an expert IELTS examiner. Generate an IELTS Speaking Part 2 cue card.

REQUIREMENTS:
1. Create a cue card with a topic and 4 bullet point prompts
2. The topic should require personal experience/opinion
3. Include a follow-up question

Return ONLY valid JSON:
{
    "part_number": 2,
    "title": "Individual Long Turn",
    "cue_card": "Describe... You should say:\\n- point 1\\n- point 2\\n- point 3\\n- and explain...",
    "follow_up": "follow-up question"
}"""
    else:
        return """You are an expert IELTS examiner. Generate IELTS Speaking Part 3 discussion questions.

REQUIREMENTS:
1. Generate 4 abstract/analytical questions related to a broad theme
2. Questions should require extended answers with reasoning
3. Questions should increase in complexity and abstraction
4. Include a topic label

Return ONLY valid JSON:
{
    "part_number": 3,
    "title": "Two-way Discussion",
    "topic": "broad theme label",
    "questions": ["question1", "question2", "question3", "question4"]
}"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_listening_content() -> dict:
    """Generate all 4 listening sections with progressive difficulty."""
    client = get_gemma_client()
    sections = []

    for config in LISTENING_DIFFICULTY:
        prompt = _build_listening_prompt(config)
        try:
            response = await asyncio.to_thread(
                client.generate_text, prompt, None, 0.4
            )
            parsed = _parse_json_response(response)
            if parsed:
                sections.append(parsed)
            else:
                logger.warning(f"Failed to parse listening section {config['section_number']}")
                sections.append(_fallback_listening_section(config))
        except GemmaClientError as e:
            logger.error(f"AI error generating listening section {config['section_number']}: {e}")
            sections.append(_fallback_listening_section(config))

    return {
        "sections": sections,
        "difficulty_config": LISTENING_DIFFICULTY,
        "total_questions": sum(c["question_count"] for c in LISTENING_DIFFICULTY),
    }


async def generate_reading_content() -> dict:
    """Generate 3 reading passages with progressive difficulty."""
    client = get_gemma_client()
    passages = []

    for config in READING_DIFFICULTY:
        prompt = _build_reading_prompt(config)
        try:
            response = await asyncio.to_thread(
                client.generate_text, prompt, None, 0.3
            )
            parsed = _parse_json_response(response)
            if parsed:
                passages.append(parsed)
            else:
                logger.warning(f"Failed to parse reading passage {config['passage_number']}")
                passages.append(_fallback_reading_passage(config))
        except GemmaClientError as e:
            logger.error(f"AI error generating reading passage {config['passage_number']}: {e}")
            passages.append(_fallback_reading_passage(config))

    return {
        "passages": passages,
        "difficulty_config": READING_DIFFICULTY,
        "total_questions": sum(c["question_count"] for c in READING_DIFFICULTY),
    }


async def generate_writing_content() -> dict:
    """Generate Task 1 + Task 2 writing prompts."""
    client = get_gemma_client()
    tasks = []

    for config in WRITING_DIFFICULTY:
        prompt = _build_writing_prompt(config)
        try:
            response = await asyncio.to_thread(
                client.generate_text, prompt, None, 0.5
            )
            parsed = _parse_json_response(response)
            if parsed:
                tasks.append(parsed)
            else:
                tasks.append(_fallback_writing_task(config))
        except GemmaClientError as e:
            logger.error(f"AI error generating writing task {config['task_number']}: {e}")
            tasks.append(_fallback_writing_task(config))

    return {
        "tasks": tasks,
        "difficulty_config": WRITING_DIFFICULTY,
    }


async def generate_speaking_content() -> dict:
    """Generate speaking Part 1, 2, and 3 content."""
    client = get_gemma_client()
    parts = []

    for config in SPEAKING_DIFFICULTY:
        prompt = _build_speaking_prompt(config)
        try:
            response = await asyncio.to_thread(
                client.generate_text, prompt, None, 0.5
            )
            parsed = _parse_json_response(response)
            if parsed:
                parts.append(parsed)
            else:
                parts.append(_fallback_speaking_part(config))
        except GemmaClientError as e:
            logger.error(f"AI error generating speaking part {config['part_number']}: {e}")
            parts.append(_fallback_speaking_part(config))

    return {
        "parts": parts,
        "difficulty_config": SPEAKING_DIFFICULTY,
    }


async def generate_full_mock_test() -> dict:
    """Generate complete mock test content for all 4 sections."""
    # Generate all sections concurrently for speed
    listening, reading, writing, speaking = await asyncio.gather(
        generate_listening_content(),
        generate_reading_content(),
        generate_writing_content(),
        generate_speaking_content(),
    )

    return {
        "listening": listening,
        "reading": reading,
        "writing": writing,
        "speaking": speaking,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_json_response(response: str) -> Optional[dict]:
    """Extract and parse JSON from AI response text."""
    if not response:
        return None
    try:
        # Try direct parse first
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass

    # Try finding JSON object in response
    if "{" in response:
        start = response.find("{")
        end = response.rfind("}") + 1
        if end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK CONTENT (when AI fails)
# ═══════════════════════════════════════════════════════════════════════════════

def _fallback_listening_section(config: dict) -> dict:
    """Minimal fallback listening section."""
    section_num = config["section_number"]
    base_id = (section_num - 1) * 10 + 1
    return {
        "section_number": section_num,
        "title": f"Listening Section {section_num} (Generated)",
        "transcript": (
            "This is a placeholder transcript. The AI service was unavailable "
            "when generating this section. Please try again later for a full test."
        ),
        "questions": [
            {
                "id": base_id + i,
                "text": f"Question {base_id + i} (placeholder)",
                "type": "FILL_BLANK",
                "correct_answer": "placeholder",
                "options": None,
            }
            for i in range(config["question_count"])
        ],
    }


def _fallback_reading_passage(config: dict) -> dict:
    """Minimal fallback reading passage."""
    passage_num = config["passage_number"]
    base_id = sum(
        READING_DIFFICULTY[i]["question_count"]
        for i in range(passage_num - 1)
    ) + 1
    return {
        "passage_number": passage_num,
        "title": f"Reading Passage {passage_num} (Generated)",
        "difficulty": config["difficulty"],
        "content": (
            "A. This is a placeholder passage. The AI service was unavailable "
            "when generating this content. Please try again later for a full test.\n\n"
            "B. The passage would normally contain several paragraphs of academic "
            "text with increasing complexity based on the difficulty level."
        ),
        "word_count": 50,
        "questions": [
            {
                "id": base_id + i,
                "text": f"Question {base_id + i} (placeholder)",
                "type": "MULTIPLE_CHOICE",
                "correct_answer": "A",
                "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            }
            for i in range(config["question_count"])
        ],
    }


def _fallback_writing_task(config: dict) -> dict:
    """Minimal fallback writing task."""
    if config["task_type"] == "task_1":
        return {
            "task_number": 1,
            "task_type": "task_1",
            "prompt": (
                "The chart below shows the number of international students enrolled "
                "in three different universities between 2010 and 2020.\n\n"
                "Summarise the information by selecting and reporting the main "
                "features, and make comparisons where relevant.\n\n"
                "Write at least 150 words."
            ),
            "chart_data": {
                "type": "line",
                "title": "International Student Enrollment",
                "categories": ["2010", "2012", "2014", "2016", "2018", "2020"],
                "series": [
                    {"name": "University A", "data": [500, 650, 800, 950, 1100, 1300]},
                    {"name": "University B", "data": [300, 400, 500, 700, 850, 900]},
                    {"name": "University C", "data": [200, 250, 350, 400, 450, 500]},
                ],
            },
            "min_words": 150,
        }
    else:
        return {
            "task_number": 2,
            "task_type": "task_2",
            "prompt": (
                "In many countries, the gap between the rich and the poor is "
                "increasing. What problems does this cause? What solutions can "
                "you suggest?\n\n"
                "Give reasons for your answer and include any relevant examples "
                "from your own knowledge or experience.\n\n"
                "Write at least 250 words."
            ),
            "chart_data": None,
            "min_words": 250,
        }


def _fallback_speaking_part(config: dict) -> dict:
    """Minimal fallback speaking part."""
    part = config["part_number"]
    if part == 1:
        return {
            "part_number": 1,
            "title": "Introduction and General Questions",
            "questions": [
                "What is your full name?",
                "Where do you come from?",
                "Do you work or study?",
                "What do you like to do in your spare time?",
                "Do you prefer indoor or outdoor activities?",
            ],
        }
    elif part == 2:
        return {
            "part_number": 2,
            "title": "Individual Long Turn",
            "cue_card": (
                "Describe a place you have visited that left a strong impression "
                "on you.\n\n"
                "You should say:\n"
                "- where this place is\n"
                "- when you visited it\n"
                "- what you did there\n"
                "- and explain why it made such a strong impression on you."
            ),
            "follow_up": "Do you like visiting new places?",
        }
    else:
        return {
            "part_number": 3,
            "title": "Two-way Discussion",
            "topic": "Travel and Tourism",
            "questions": [
                "How has tourism changed in recent years?",
                "Do you think tourism has a positive or negative effect on local communities?",
                "Should governments limit the number of tourists visiting certain areas?",
                "How might travel change in the future?",
            ],
        }
