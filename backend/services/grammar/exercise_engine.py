"""Grammar Exercise Engine - AI-powered generation and evaluation for 8 exercise types."""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError


EXERCISE_TYPES = [
    "fill_blank",
    "multiple_choice", 
    "error_correction",
    "rewrite",
    "drag_drop",
    "sentence_ordering",
    "expansion",
    "transformation"
]


class GeneratedExercise(BaseModel):
    """Schema for a generated exercise."""
    exercise_type: str
    question_data: Dict[str, Any]
    correct_answer: str
    explanation: str
    difficulty: str = "medium"


class ExerciseGenerator:
    """Generates grammar exercises using AI."""
    
    def __init__(self):
        self.ai_client = get_gemma_client()
    
    async def generate_exercises(
        self,
        topic_name: str,
        types: List[str],
        count: int = 5,
        difficulty: str = "medium",
        mistakes: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Generate exercises using AI."""
        mistakes_context = ""
        if mistakes:
            mistakes_list = "\n".join([
                f"- Incorrect: {m.get('incorrect', '')} → Correct: {m.get('correct', '')}"
                for m in mistakes[:3]
            ])
            mistakes_context = f"\nUser's recent mistakes to focus on:\n{mistakes_list}"
        
        prompt = f"""Generate exactly {count} grammar exercises for the topic: '{topic_name}'.
Difficulty: {difficulty}
{mistakes_context}

Generate exercises of these types (distribute evenly): {', '.join(types)}

For each exercise type, use this JSON structure:

1. fill_blank: {{"exercise_type": "fill_blank", "question_data": {{"question": "Fill in the blank", "sentence": "She ___ to school every day."}}, "correct_answer": "goes", "explanation": "Simple present for routines"}}

2. multiple_choice: {{"exercise_type": "multiple_choice", "question_data": {{"question": "Choose the correct sentence:", "options": ["option A", "option B", "option C", "option D"]}}, "correct_answer": "option A", "explanation": "Because..."}}

3. error_correction: {{"exercise_type": "error_correction", "question_data": {{"question": "Find and correct the error", "sentence": "She don't like pizza."}}, "correct_answer": "She doesn't like pizza.", "explanation": "Third person singular requires 'doesn't'"}}

4. rewrite: {{"exercise_type": "rewrite", "question_data": {{"question": "Rewrite using passive voice", "sentence": "The teacher marked the exams.", "instruction": "Rewrite this sentence in passive voice"}}, "correct_answer": "The exams were marked by the teacher.", "explanation": "Passive: object + be + past participle + by + agent"}}

5. drag_drop: {{"exercise_type": "drag_drop", "question_data": {{"question": "Arrange the words to form a correct sentence", "words": ["the", "student", "who", "studies", "hard", "will", "succeed"]}}, "correct_answer": "the student who studies hard will succeed", "explanation": "Relative clause modifies 'student'"}}

6. sentence_ordering: {{"exercise_type": "sentence_ordering", "question_data": {{"question": "Put these sentences in logical order", "sentences": ["First sentence", "Second sentence", "Third sentence"]}}, "correct_answer": "First sentence. Second sentence. Third sentence", "explanation": "Logical flow from introduction to conclusion"}}

7. expansion: {{"exercise_type": "expansion", "question_data": {{"question": "Expand the sentence", "sentence": "The student passed.", "instruction": "Expand using a relative clause", "target_structure": "relative clause"}}, "correct_answer": "The student who studied hard passed.", "explanation": "Added a defining relative clause"}}

8. transformation: {{"exercise_type": "transformation", "question_data": {{"question": "Transform the sentence", "sentence": "People say she is talented.", "transformation": "Convert to passive (It is said that...)", "hint": "Use 'It is said that...'"}}, "correct_answer": "It is said that she is talented.", "explanation": "Impersonal passive construction"}}

Return a JSON array of {count} exercises. Return ONLY valid JSON array, no other text."""

        try:
            raw_response = await asyncio.to_thread(
                self.ai_client.generate_text,
                prompt=prompt,
                system_prompt="You are a grammar exercise generator. Return only valid JSON arrays.",
                temperature=0.7
            )
            
            # Parse JSON from response
            if "[" in raw_response:
                start = raw_response.find("[")
                end = raw_response.rfind("]") + 1
                exercises_data = json.loads(raw_response[start:end])
                
                # Validate and return
                validated = []
                for ex in exercises_data[:count]:
                    if isinstance(ex, dict) and "exercise_type" in ex:
                        validated.append({
                            "exercise_type": ex.get("exercise_type", "fill_blank"),
                            "question_data": ex.get("question_data", {"question": "Complete the exercise"}),
                            "correct_answer": ex.get("correct_answer", ""),
                            "explanation": ex.get("explanation", ""),
                            "difficulty": difficulty
                        })
                
                if validated:
                    return validated
            
            # Fallback if parsing fails
            return self._generate_fallback_exercises(topic_name, types, count, difficulty)
            
        except (GemmaClientError, json.JSONDecodeError, Exception):
            return self._generate_fallback_exercises(topic_name, types, count, difficulty)
    
    def _generate_fallback_exercises(
        self, topic_name: str, types: List[str], count: int, difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate fallback exercises when AI is unavailable."""
        exercises = []
        
        templates = {
            "fill_blank": {
                "exercise_type": "fill_blank",
                "question_data": {
                    "question": f"Fill in the blank (Topic: {topic_name})",
                    "sentence": f"Complete the sentence using the correct form of {topic_name}."
                },
                "correct_answer": "the correct answer",
                "explanation": f"This exercise tests your knowledge of {topic_name}."
            },
            "multiple_choice": {
                "exercise_type": "multiple_choice",
                "question_data": {
                    "question": f"Which sentence correctly uses {topic_name}?",
                    "options": [
                        "The research, which was conducted last year, revealed significant findings.",
                        "The research which was conducted last year revealed significant findings.",
                        "The research that was conducted last year, revealed significant findings.",
                        "The research, that was conducted last year, revealed significant findings."
                    ]
                },
                "correct_answer": "The research, which was conducted last year, revealed significant findings.",
                "explanation": "Non-defining relative clauses use commas and 'which' (not 'that')."
            },
            "error_correction": {
                "exercise_type": "error_correction",
                "question_data": {
                    "question": f"Find and correct the grammar error related to {topic_name}",
                    "sentence": "Although he was tired but he continued working on the project."
                },
                "correct_answer": "Although he was tired, he continued working on the project.",
                "explanation": "Do not use both 'although' and 'but' - they both signal contrast."
            },
            "rewrite": {
                "exercise_type": "rewrite",
                "question_data": {
                    "question": "Rewrite this sentence",
                    "sentence": "People believe that education is important.",
                    "instruction": "Rewrite using passive voice"
                },
                "correct_answer": "It is believed that education is important.",
                "explanation": "Impersonal passive: It + passive verb + that clause."
            },
            "drag_drop": {
                "exercise_type": "drag_drop",
                "question_data": {
                    "question": "Arrange the words to form a correct sentence",
                    "words": ["Despite", "the", "challenges", "the", "project", "succeeded"]
                },
                "correct_answer": "Despite the challenges the project succeeded",
                "explanation": "'Despite' + noun phrase shows contrast."
            },
            "sentence_ordering": {
                "exercise_type": "sentence_ordering",
                "question_data": {
                    "question": "Put these sentences in the correct logical order",
                    "sentences": [
                        "Therefore, governments should invest more in renewable energy.",
                        "Climate change poses a significant threat to the environment.",
                        "However, the transition requires substantial initial investment."
                    ]
                },
                "correct_answer": "Climate change poses a significant threat to the environment. Therefore, governments should invest more in renewable energy. However, the transition requires substantial initial investment.",
                "explanation": "Problem → Solution → Counter-argument is a logical essay structure."
            },
            "expansion": {
                "exercise_type": "expansion",
                "question_data": {
                    "question": "Expand the sentence",
                    "sentence": "The government implemented the policy.",
                    "instruction": f"Expand using {topic_name}",
                    "target_structure": topic_name
                },
                "correct_answer": "The government, which faced significant public pressure, implemented the controversial policy.",
                "explanation": f"Added a {topic_name} structure to make the sentence more complex."
            },
            "transformation": {
                "exercise_type": "transformation",
                "question_data": {
                    "question": "Transform the sentence",
                    "sentence": "I didn't study hard. I failed the exam.",
                    "transformation": "Combine using a conditional structure",
                    "hint": "Use 'If I had...'"
                },
                "correct_answer": "If I had studied hard, I would not have failed the exam.",
                "explanation": "Third conditional: If + past perfect, would have + past participle."
            }
        }
        
        for i in range(count):
            exercise_type = types[i % len(types)]
            template = templates.get(exercise_type, templates["fill_blank"]).copy()
            template["difficulty"] = difficulty
            exercises.append(template)
        
        return exercises
    
    async def evaluate_answer(
        self,
        exercise_type: str,
        question_data: Dict[str, Any],
        correct_answer: str,
        user_answer: str
    ) -> Dict[str, Any]:
        """Evaluate a user's answer using AI."""
        # Use shared answer comparison
        from shared.answer_utils import answers_match
        from shared.parsing import parse_json_from_response
        
        if answers_match(user_answer, correct_answer):
            return {
                "is_correct": True,
                "feedback": "Correct! Well done.",
                "explanation": ""
            }
        
        # For text-based exercises, use AI for more flexible evaluation
        if exercise_type in ("error_correction", "rewrite", "expansion", "transformation"):
            try:
                prompt = f"""Evaluate this grammar exercise answer.

Exercise type: {exercise_type}
Question: {json.dumps(question_data)}
Expected answer: {correct_answer}
Student's answer: {user_answer}

Is the student's answer grammatically correct and does it satisfy the exercise requirements?
Consider that there may be multiple valid answers.

Return JSON: {{"is_correct": true/false, "feedback": "brief feedback", "explanation": "why correct/incorrect"}}"""

                raw = await asyncio.to_thread(
                    self.ai_client.generate_text,
                    prompt=prompt,
                    temperature=0.2
                )
                
                result = parse_json_from_response(raw)
                if result:
                    return {
                        "is_correct": result.get("is_correct", False),
                        "feedback": result.get("feedback", ""),
                        "explanation": result.get("explanation", "")
                    }
            except Exception:
                pass
        
        # Fallback: case-insensitive comparison
        is_correct = answers_match(user_answer, correct_answer)
        return {
            "is_correct": is_correct,
            "feedback": "Correct!" if is_correct else f"Incorrect. The expected answer is: {correct_answer}",
            "explanation": ""
        }


# Singleton
_exercise_generator: Optional[ExerciseGenerator] = None


def get_exercise_generator() -> ExerciseGenerator:
    """Get the singleton ExerciseGenerator instance."""
    global _exercise_generator
    if _exercise_generator is None:
        _exercise_generator = ExerciseGenerator()
    return _exercise_generator