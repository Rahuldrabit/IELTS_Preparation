"""AI Agent Service - LLM client, embeddings, and LangGraph agent pipelines."""
import json
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from shared import settings
from services.ai_agent.gemma_client import GemmaClient, GemmaClientError, get_gemma_client


# ============ Router ============

router = APIRouter(prefix="/agent", tags=["AI Agent"])


# ============ LLM Client ============

class LLMClient:
    """OpenAI-compatible LLM client for LM Studio."""

    def __init__(self):
        self.client = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            request_timeout=120,
        )

    def chat_sync(self, messages: list[dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        try:
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                else:
                    lc_messages.append(HumanMessage(content=msg["content"]))

            response = self.client.invoke(lc_messages)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"


llm_client = LLMClient()

# Initialize Qdrant client
try:
    qdrant_client = QdrantClient(url=settings.qdrant_url)
    try:
        qdrant_client.create_collection(
            collection_name="passages",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    except:
        pass
    try:
        qdrant_client.create_collection(
            collection_name="vocabulary",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    except:
        pass
except Exception as e:
    print(f"Warning: Could not initialize Qdrant: {e}")
    qdrant_client = None


# ============ Pydantic Schemas ============

class ChatRequest(BaseModel):
    message: str
    page: str = "dashboard"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str
    type: str = "message"
    actions: Optional[list[dict]] = None


# ============ Agent Prompts ============

SYSTEM_PROMPTS = {
    "dashboard": "You are an IELTS AI Tutor assistant. Provide encouraging, personalized messages based on their progress.",
    "reading": "You are an IELTS Reading expert. Provide strategic tips for IELTS Reading.",
    "listening": "You are an IELTS Listening expert. Provide tips for IELTS Listening.",
    "writing": "You are an IELTS Writing expert. Provide guidance on Task 1 and Task 2 essays.",
    "speaking": "You are an IELTS Speaking expert. Provide tips for all 3 parts.",
    "vocabulary": "You are an IELTS Vocabulary expert. Help users learn academic vocabulary.",
    "grammar": "You are an IELTS Grammar expert. Help users master grammar for IELTS.",
    "import": "You are an AI Exam Import assistant. Help users import their IELTS materials.",
    "insights": "You are an IELTS Progress analyst. Provide insights on the user's progress.",
    "journey": "You are an IELTS Journey planner. Help users plan their path to their target band.",
}


# ============ Endpoints ============


@router.post("/chat")
async def chat(request: ChatRequest):
    """General chat endpoint for AI mentor."""
    system_prompt = SYSTEM_PROMPTS.get(request.page, SYSTEM_PROMPTS["dashboard"])

    context_str = ""
    if request.context:
        context_str = f"\n\nUser Context: {request.context}"

    messages = [
        {"role": "system", "content": system_prompt + context_str},
        {"role": "user", "content": request.message},
    ]

    response = llm_client.chat_sync(messages)

    msg_type = "message"
    if any(word in response.lower() for word in ["recommend", "suggest", "try"]):
        msg_type = "recommendation"
    elif any(word in response.lower() for word in ["tip", "remember", "note"]):
        msg_type = "hint"

    return ChatResponse(response=response, type=msg_type)


@router.get("/mentor-messages")
async def get_mentor_messages(page: str = "dashboard"):
    """Get contextual mentor messages for a page."""
    system_prompt = SYSTEM_PROMPTS.get(page, SYSTEM_PROMPTS["dashboard"])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Give me a brief motivational message and one tip."},
    ]

    response = llm_client.chat_sync(messages)

    return [{"id": f"msg-{page}-1", "type": "greeting", "content": response}]


@router.get("/daily-plan")
async def get_daily_plan():
    """Generate a daily study plan using LangGraph agent."""
    messages = [
        {"role": "system", "content": "You are a study planner for IELTS preparation. Generate a daily study plan with 5 tasks. Return JSON: tasks=[{title, skill, priority}]"},
        {"role": "user", "content": "Generate today's study plan."},
    ]

    response = llm_client.chat_sync(messages)

    try:
        if "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            plan_data = json.loads(response[start:end])
            return plan_data
    except:
        pass

    return {
        "tasks": [
            {"title": "Complete 2 reading passages", "skill": "reading", "priority": "high"},
            {"title": "Practice 10 vocabulary words", "skill": "vocabulary", "priority": "medium"},
            {"title": "Listen to a podcast and take notes", "skill": "listening", "priority": "medium"},
            {"title": "Record a 2-minute speaking response", "skill": "speaking", "priority": "low"},
            {"title": "Write an essay and get AI feedback", "skill": "writing", "priority": "high"},
        ]
    }


# ============ Writing Scoring ============

class WritingScoreRequest(BaseModel):
    essay: str
    task_type: str = "task_2"


class WritingScoreResponse(BaseModel):
    task_response: float
    coherence: float
    lexical: float
    grammar: float
    overall: float
    feedback: dict
    corrections: list[dict]


@router.post("/score-writing")
async def score_writing(request: WritingScoreRequest):
    """Score writing using multi-step agent pipeline."""

    # Step 1: Error detection
    error_prompt = f"""Analyze this IELTS essay for errors.
Return JSON: {{"corrections": [{{"incorrect": "...", "correct": "...", "explanation": "...", "type": "grammar|vocabulary"}}]}}

Essay:
{request.essay[:2000]}"""

    error_response = llm_client.chat_sync([{"role": "user", "content": error_prompt}])

    corrections = []
    try:
        if "{" in error_response:
            start = error_response.find("{")
            end = error_response.rfind("}") + 1
            data = json.loads(error_response[start:end])
            corrections = data.get("corrections", [])
    except:
        corrections = []

    # Step 2: Scoring
    score_prompt = f"""Score this IELTS essay on a scale of 1-9 for:
- Task Response, Coherence and Cohesion, Lexical Resource, Grammatical Range and Accuracy
Return JSON: {{"task_response": X.X, "coherence": X.X, "lexical": X.X, "grammar": X.X}}

Essay:
{request.essay[:2000]}"""

    score_response = llm_client.chat_sync([{"role": "user", "content": score_prompt}])

    try:
        if "{" in score_response:
            start = score_response.find("{")
            end = score_response.rfind("}") + 1
            scores = json.loads(score_response[start:end])
        else:
            scores = {"task_response": 6.5, "coherence": 6.5, "lexical": 6.5, "grammar": 6.5}
    except:
        scores = {"task_response": 6.5, "coherence": 6.5, "lexical": 6.5, "grammar": 6.5}

    overall = (scores.get("task_response", 6.5) + scores.get("coherence", 6.5) + scores.get("lexical", 6.5) + scores.get("grammar", 6.5)) / 4

    feedback_prompt = f"Provide brief feedback on this IELTS essay.\n\nEssay (first 500 chars): {request.essay[:500]}"
    feedback_text = llm_client.chat_sync([{"role": "user", "content": feedback_prompt}])

    return WritingScoreResponse(
        task_response=scores.get("task_response", 6.5),
        coherence=scores.get("coherence", 6.5),
        lexical=scores.get("lexical", 6.5),
        grammar=scores.get("grammar", 6.5),
        overall=round(overall, 1),
        feedback={
            "task_response": f"Task Response: {scores.get('task_response', 6.5)}",
            "coherence": f"Coherence: {scores.get('coherence', 6.5)}",
            "vocabulary": f"Lexical Resource: {scores.get('lexical', 6.5)}",
            "grammar": f"Grammar: {scores.get('grammar', 6.5)}",
            "summary": feedback_text[:200],
        },
        corrections=corrections,
    )


# ============ Vocabulary Enrichment ============

class VocabEnrichRequest(BaseModel):
    word: str


@router.post("/enrich-vocab")
async def enrich_vocabulary(request: VocabEnrichRequest):
    """Enrich a vocabulary word with definitions, examples, etc."""

    prompt = f"""Provide detailed vocabulary information for the word "{request.word}".
Return JSON with: pronunciation, meaning, definition, examples[], synonyms[], antonyms[], collocations[], word_family[], cefr (A1-C2), ielts_frequency (1-10)"""

    response = llm_client.chat_sync([{"role": "user", "content": prompt}])

    try:
        if "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            data = json.loads(response[start:end])
            data["word"] = request.word
            data["examples"] = data.get("examples", [])
            data["synonyms"] = data.get("synonyms", [])
            data["antonyms"] = data.get("antonyms", [])
            data["collocations"] = data.get("collocations", [])
            data["word_family"] = data.get("word_family", [])
            data["ielts_frequency"] = data.get("ielts_frequency", 5)
            return data
    except:
        pass

    return {
        "word": request.word,
        "pronunciation": "",
        "meaning": "",
        "definition": "",
        "examples": [],
        "synonyms": [],
        "antonyms": [],
        "collocations": [],
        "word_family": [],
        "cefr": "B2",
        "ielts_frequency": 5,
    }


# ============ Grammar Exercise Generator ============

class GrammarExercisesRequest(BaseModel):
    topic: str
    mistakes: list[dict] = []


@router.post("/generate-exercises")
async def generate_grammar_exercises(request: GrammarExercisesRequest):
    """Generate grammar exercises based on topic and mistakes."""

    mistakes_context = ""
    if request.mistakes:
        mistakes_context = "\n".join([f"- Incorrect: {m.get('incorrect', '')} -> Correct: {m.get('correct', '')}" for m in request.mistakes[:5]])
        mistakes_context = f"\nUser's recent mistakes:\n{mistakes_context}"

    prompt = f"""Generate 5 grammar exercises for the topic: {request.topic}.{mistakes_context}
Return JSON array: [{{"id": 1, "question": "...", "correct_answer": "...", "explanation": "..."}}]"""

    response = llm_client.chat_sync([{"role": "user", "content": prompt}])

    try:
        if "[" in response:
            start = response.find("[")
            end = response.rfind("]") + 1
            data = json.loads(response[start:end])
            return {"exercises": data}
    except:
        pass

    return {"exercises": []}


# ============ Gemma 4 Health Check ============

@router.get("/health")
async def gemma_health():
    """Check if Gemma 4 is reachable and configured correctly."""
    try:
        client = get_gemma_client()
        result = client.health_check()
        return result
    except GemmaClientError as e:
        return {
            "model": settings.gemma_model,
            "status": "error",
            "error": str(e),
        }


# ============ Gemma 4 Test Generation (for debugging) ============

class TestGenerationRequest(BaseModel):
    topic: str = "technology"
    difficulty: str = "intermediate"


@router.post("/test-generate")
async def test_generate(request: TestGenerationRequest):
    """Test endpoint to verify Gemma 4 structured output works."""
    from shared.schemas import ExamOutput, GenerationParams

    prompt = f"""Generate a short IELTS reading passage and 2 questions.

Topic: {request.topic}
Difficulty: {request.difficulty}

The passage should be around 150 words.
Generate exactly 2 TRUE_FALSE_NOT_GIVEN questions.

Return the output matching the ExamOutput schema."""

    try:
        client = get_gemma_client()
        result = client.generate_structured(prompt, schema=ExamOutput)
        return result.model_dump()
    except GemmaClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Speaking Transcription & Analysis ============

@router.post("/transcribe-speaking")
async def transcribe_speaking(
    audio: UploadFile = File(...),
):
    """
    Transcribe a 30-second speaking recording and analyze it against IELTS criteria.
    Accepts multipart/form-data with an audio file (WAV, WebM, MP3).
    Returns SpeakingFeedback with transcript, band, and per-criterion scores.
    """
    from shared.schemas import SpeakingFeedback

    # Save uploaded audio to a temp file
    suffix = os.path.splitext(audio.filename)[0] if audio.filename else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        client = get_gemma_client()

        # Step 1: Transcribe + analyze in one call
        analysis_prompt = """Transcribe this 30-second IELTS speaking response accurately.
Then score the speaker on the 4 IELTS Speaking criteria:
1. Fluency & Coherence (1-9) — flow, connected speech, hesitation
2. Lexical Resource (1-9) — vocabulary range, accuracy, paraphrasing
3. Grammatical Range & Accuracy (1-9) — sentence structures, error rate
4. Pronunciation (1-9) — clarity, intonation, rhythm

Give the overall band score (average of 4 criteria rounded to nearest 0.5).
List exactly 3 specific improvement suggestions.

Return JSON matching the SpeakingFeedback schema."""

        transcript = client.transcribe_audio(tmp_path, prompt=analysis_prompt)

        # Step 2: If the response contains structured data, try to parse it
        # The transcription may include the analysis in one response
        try:
            if "{" in transcript:
                start = transcript.find("{")
                end = transcript.rfind("}") + 1
                data = json.loads(transcript[start:end])
                feedback = SpeakingFeedback.model_validate(data)
            else:
                # Transcription only — generate analysis separately
                score_prompt = f"""Analyze this IELTS speaking transcript and provide scores.

TRANSCRIPT:
{transcript}

Score on Fluency, Lexical Resource, Grammar, and Pronunciation (each 1-9).
Give overall band and 3 improvement suggestions.
Return JSON matching SpeakingFeedback schema."""

                feedback = client.generate_structured(
                    prompt=score_prompt,
                    schema=SpeakingFeedback,
                    temperature=0.3,
                )
        except Exception:
            # Fallback: construct basic feedback from transcription
            feedback = SpeakingFeedback(
                transcript=transcript,
                band=6.0,
                fluency=6.0,
                lexical=6.0,
                grammar=6.0,
                pronunciation=6.0,
                suggestions=[
                    "Try to speak more fluently with fewer hesitations.",
                    "Use a wider range of vocabulary to demonstrate lexical resource.",
                    "Practice complex sentence structures to improve grammatical range.",
                ],
            )

        return feedback.model_dump()

    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speaking analysis failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass