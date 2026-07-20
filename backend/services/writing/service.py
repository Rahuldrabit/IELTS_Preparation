from typing import Optional
from shared.models import WritingTask
from shared.schemas import WritingFeedback, WritingTaskPublic

def build_scoring_prompt(essay: str, task_type: str) -> str:
    return f"""You are an expert IELTS examiner. Grade this Task {task_type.replace("_", " ").upper()} essay against the 4 official IELTS criteria.

CRITERIA:
1. Task Response (Task Achievement for Task 1) — How well did the candidate address all parts of the task?
2. Coherence and Cohesion — Is the response logically organised? Is there appropriate linking?
3. Lexical Resource — Range and accuracy of vocabulary.
4. Grammatical Range and Accuracy — Range of structures and error rate.

ESSAY:
{essay}

For EACH criterion provide:
- A band score (1.0–9.0) to one decimal place
- A 2–3 sentence explanation of why that score was awarded
- A specific improvement tip

Also list any specific inline corrections: find grammar, vocabulary, punctuation, or spelling mistakes.
For each correction provide the exact incorrect text, the corrected text, an explanation, and the error type.

Return JSON matching the WritingFeedback schema."""

def build_task_generation_prompt(task_type: str, topic: Optional[str], target_band: float) -> str:
    topic_clause = f" on the topic of: {topic}" if topic else ""

    if task_type == "task_1":
        return f"""You are an IELTS writing examiner. Generate a realistic IELTS TASK 1 Academic writing prompt{topic_clause}.

Requirements:
- The task MUST include chart/graph data that the student will describe.
- Choose one chart type: bar, line, or pie.
- Generate realistic numerical data with 4-8 data points.
- The task should be appropriate for a target Band {target_band} candidate.

Return a JSON object with exactly these fields:
{{
  "prompt": "The full question/prompt text shown to the student (e.g. 'The bar chart below shows...')",
  "description": "Brief instruction (e.g. 'Summarise the information by selecting and reporting the main features, and make comparisons where relevant.')",
  "band_descriptor": "Description of what a Band {target_band} answer looks like (2-3 sentences)",
  "chart_data": {{
    "chart_type": "bar | line | pie",
    "title": "Chart title shown above the visualization",
    "x_axis_label": "Label for the x-axis (not used for pie)",
    "y_axis_label": "Label for the y-axis (not used for pie)",
    "labels": ["Label1", "Label2", "..."],
    "datasets": [
      {{"label": "Series name", "data": [number, number, ...]}}
    ]
  }}
}}

IMPORTANT: chart_data.datasets[].data must contain only numbers. labels must match the number of data points.
Return ONLY valid JSON."""

    return f"""You are an IELTS writing examiner. Generate a realistic IELTS {task_type.replace('_', ' ').upper()} writing prompt{topic_clause}.

Requirements:
- The task should be appropriate for a target Band {target_band} candidate.
- Include a clear task description/instruction.
- Include a brief band descriptor showing what a good answer looks like.

Return a JSON object with exactly these fields:
{{
  "prompt": "The full question/prompt text shown to the student",
  "description": "Brief context or instruction (2-3 sentences)",
  "band_descriptor": "Description of what a Band {target_band} answer looks like (2-3 sentences)"
}}

Return ONLY valid JSON."""

def fallback_feedback() -> WritingFeedback:
    return WritingFeedback(
        task_response=6.0,
        coherence=6.0,
        lexical=6.0,
        grammar=6.0,
        overall=6.0,
        per_criterion_feedback=[
            {
                "criterion": "task_response",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable. Please try again later.",
                "improvement_tip": "Try again after a few moments.",
            },
            {
                "criterion": "coherence",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Ensure your essay has a clear introduction, body, and conclusion.",
            },
            {
                "criterion": "lexical",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Use a range of academic vocabulary.",
            },
            {
                "criterion": "grammar",
                "band": 6.0,
                "explanation": "AI scoring is currently unavailable.",
                "improvement_tip": "Use a mix of simple and complex sentence structures.",
            },
        ],
        inline_corrections=[],
    )

def build_writing_task_response(task: WritingTask, chart_data: dict = None) -> WritingTaskPublic:
    return WritingTaskPublic(
        id=task.id,
        task_type=task.task_type,
        prompt=task.prompt,
        description=task.description,
        min_words=task.min_words,
        band_descriptor=task.band_descriptor,
        chart_data=chart_data or (task.generation_params or {}).get("chart_data"),
    )
