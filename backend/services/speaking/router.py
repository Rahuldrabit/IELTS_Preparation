from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from . import schemas
from . import service

router = APIRouter(prefix="/speaking", tags=["Speaking"])

@router.post("/shadowing/model", response_model=schemas.ShadowingModelResponse)
async def get_shadowing_model(
    request: schemas.ShadowingModelRequest,
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    return await service.build_shadowing_model(request)

@router.get("/shadowing/session/{session_id}")
async def get_shadowing_session(
    session_id: str,
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    return {
        "session_id": session_id,
        "status": "active",
        "current_tier": 1,
        "attempts": [],
    }

@router.post("/examiner/create")
async def create_examiner_session(
    request: schemas.CreateExaminerSessionRequest,
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    from services.agents.examiner.agent import create_session
    try:
        session = create_session(part=request.part, topic=request.topic)
        return {
            "session_id": session.session_id,
            "part": session.part,
            "topic": session.topic,
            "opening_message": session.messages[0].content if session.messages else "",
            "session_state": session.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/examiner/chat", response_model=schemas.ExaminerChatResponse)
async def examiner_chat(
    request: schemas.ExaminerChatRequest,
    user_id: int = 1, # Kept for consistency and future auth
    db: AsyncSession = Depends(get_db),
):
    from services.agents.examiner.agent import (
        ExaminerSession,
        process_student_response,
    )
    try:
        session = ExaminerSession.model_validate(request.session_state)
        response = await process_student_response(session, request.message)
        return schemas.ExaminerChatResponse(
            session_id=session.session_id,
            examiner_message=response.message,
            follow_up_prompt=response.follow_up_prompt,
            is_session_end=response.is_session_end,
            estimated_band=response.estimated_band,
            feedback=response.feedback,
            session_state=session.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/examiner/topics")
async def get_examiner_topics():
    from services.agents.examiner.agent import ExaminerChatAgent
    return {
        "part1_topics": ExaminerChatAgent.PART1_TOPICS,
        "part3_topics": ExaminerChatAgent.PART3_TOPICS,
    }


from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import asyncio
import os
import tempfile
from services.llm.provider import get_llm_client

# ============ Speaking Topic Generation ============


class GenerateSpeakingTopicRequest(BaseModel):
    part: int = 2  # IELTS speaking part (1, 2, or 3)
    theme: Optional[str] = None  # Optional theme/category


class SpeakingTopic(BaseModel):
    part: int
    topic: str
    bullet_points: list[str]
    follow_up: Optional[str] = None


@router.post("/generate-speaking-topic")
async def generate_speaking_topic(request: GenerateSpeakingTopicRequest):
    """Generate a random IELTS speaking cue card topic using AI."""
    theme_hint = f" related to: {request.theme}" if request.theme else ""

    prompt = f"""Generate a realistic IELTS Speaking Part {request.part} cue card topic{theme_hint}.

For Part 1: Generate a simple question about everyday life.
For Part 2: Generate a topic card with 3-4 bullet point prompts (You should say: ...).
For Part 3: Generate a deeper discussion question related to the Part 2 topic.

Return JSON:
{{
  "part": {request.part},
  "topic": "The main topic/question text",
  "bullet_points": ["point 1", "point 2", "point 3"],
  "follow_up": "An optional follow-up question (for Part 3)"
}}

Return ONLY valid JSON."""

    try:
        client = get_llm_client()
        result = await asyncio.to_thread(
            client.generate_structured,
            prompt=prompt,
            schema=SpeakingTopic,
            temperature=0.8,
        )
        return result.model_dump()
    except Exception as e:
        # Fallback topic
        return SpeakingTopic(
            part=request.part,
            topic="Describe a skill you would like to learn. You should say:",
            bullet_points=[
                "what the skill is",
                "why you want to learn it",
                "how you would learn it",
                "and explain how this skill would help you",
            ],
            follow_up="Do you think it's important for people to keep learning new skills?",
        ).model_dump()


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
        client = get_llm_client()

        # Step 1: Transcribe + analyze in one call
        analysis_prompt = """Transcribe this 30-second IELTS speaking response accurately.
Then score the speaker on the 4 IELTS Speaking criteria:
1. Fluency & Coherence (1-9) ΓÇö flow, connected speech, hesitation
2. Lexical Resource (1-9) ΓÇö vocabulary range, accuracy, paraphrasing
3. Grammatical Range & Accuracy (1-9) ΓÇö sentence structures, error rate
4. Pronunciation (1-9) ΓÇö clarity, intonation, rhythm

Give the overall band score (average of 4 criteria rounded to nearest 0.5).
List exactly 3 specific improvement suggestions.

Return JSON matching the SpeakingFeedback schema."""

        transcript = await asyncio.to_thread(client.transcribe_audio, tmp_path, analysis_prompt)

        # Step 2: Parse structured data from transcription
        from shared.parsing import parse_json_to_model
        
        feedback = parse_json_to_model(transcript, SpeakingFeedback)
        if not feedback:
            # Transcription only ΓÇö generate analysis separately
            score_prompt = f"""Analyze this IELTS speaking transcript and provide scores.

TRANSCRIPT:
{transcript}

Score on Fluency, Lexical Resource, Grammar, and Pronunciation (each 1-9).
Give overall band and 3 improvement suggestions.
Return JSON matching SpeakingFeedback schema."""

            try:
                feedback = await asyncio.to_thread(
                    client.generate_structured,
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

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speaking analysis failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============ Language Mutation Engine ============


class MutationTier(BaseModel):
    tier: int                   # 1, 2, or 3
    band_label: str             # "Band 6.5 ΓÇö Core", etc.
    target_band: float          # 6.5, 7.5, 8.5
    text: str                   # upgraded response text
    key_changes: list[str]      # exactly 3 bullet points
    audio_hints: str            # pronunciation / rhythm guidance


class MutationGenerationRequest(BaseModel):
    transcript: str
    original_band: float = 6.0


class MutationGenerationResponse(BaseModel):
    original_transcript: str
    identified_fillers: list[str]
    tiers: list[MutationTier]   # always exactly 3


@router.post("/generate-mutations")
async def generate_mutations(request: MutationGenerationRequest):
    """
    Generate 3 language mutation tiers from a speaking transcript.
    Tier 1 = Band 6.5 (vocabulary upgrade)
    Tier 2 = Band 7.5 (structural restructure)
    Tier 3 = Band 8.5 (nominalization, inverted conditionals, idioms)
    """
    prompt = f"""You are an IELTS Speaking examiner. A student gave this response:

TRANSCRIPT:
{request.transcript}

CURRENT ESTIMATED BAND: {request.original_band}

Generate exactly 3 mutation tiers upgrading the student's response:

TIER 1 (Band 6.5 ΓÇö Core):
- Replace simple words with accurate academic equivalents only
- Keep sentence structure mostly unchanged
- Remove filled pauses ("um", "uh", "like", "you know")
- List exactly 3 key changes made

TIER 2 (Band 7.5 ΓÇö Advanced):
- Restructure sentences using subordinate clauses, parallel structures, relative clauses
- Add discourse markers and cohesive devices ("Furthermore", "In contrast", etc.)
- Expand vocabulary to idiomatic academic range
- List exactly 3 key changes made

TIER 3 (Band 8.5 ΓÇö Mastery):
- Introduce nominalization patterns (e.g. "the rapid deterioration of" instead of "things got worse quickly")
- Use inverted conditionals where appropriate ("Were this to continueΓÇª")
- Add idiomatic phrasing and sophisticated hedging language ("It could be argued thatΓÇª")
- List exactly 3 key changes made

Also identify any filler words ("um", "uh", "like", "you know") found in the original transcript.

For audio_hints in each tier: give a 1-sentence note on word stress or connected speech for that tier.

Return JSON exactly matching this structure:
{{
  "original_transcript": "...",
  "identified_fillers": ["um", "uh"],
  "tiers": [
    {{
      "tier": 1,
      "band_label": "Band 6.5 ΓÇö Core",
      "target_band": 6.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }},
    {{
      "tier": 2,
      "band_label": "Band 7.5 ΓÇö Advanced",
      "target_band": 7.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }},
    {{
      "tier": 3,
      "band_label": "Band 8.5 ΓÇö Mastery",
      "target_band": 8.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }}
  ]
}}"""

    try:
        client = get_llm_client()
        result = client.generate_structured(
            prompt=prompt,
            schema=MutationGenerationResponse,
            temperature=0.4,
        )
        # Enforce exactly 3 tiers even if model returns fewer
        if len(result.tiers) != 3:
            raise ValueError(f"Expected 3 tiers, got {len(result.tiers)}")
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mutation generation failed: {str(e)}")


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  Shadowing Assessment
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

class ShadowingAssessmentResponse(BaseModel):
    passed: bool
    phoneme_accuracy: float       # 0.0ΓÇô1.0
    rhythm_score: float           # 0.0ΓÇô1.0
    connected_speech_score: float # 0.0ΓÇô1.0
    overall_similarity: float     # average of the three
    feedback: str
    specific_errors: list[str]    # up to 3 specific issues
    word_by_word: Optional[list[dict]] = None  # word-level comparison
    pacing_analysis: Optional[dict] = None     # timing analysis


class FallbackShadowingAssessment(BaseModel):
    """Assessment using Web Speech API transcription (no Google AI)."""
    passed: bool
    phoneme_accuracy: float
    rhythm_score: float
    connected_speech_score: float
    overall_similarity: float
    feedback: str
    specific_errors: list[str]
    word_by_word: list[dict]
    note: str = "Assessment based on text comparison (Web Speech API mode)"


def _calculate_word_similarity(word1: str, word2: str) -> float:
    """Calculate similarity between two words using Levenshtein distance."""
    if not word1 or not word2:
        return 0.0
    
    word1, word2 = word1.lower(), word2.lower()
    
    if word1 == word2:
        return 1.0
    
    # Simple Levenshtein distance
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    distance = dp[m][n]
    max_len = max(m, n)
    return max(0.0, 1.0 - distance / max_len)


def _fallback_shadowing_assessment(
    user_transcript: str,
    target_text: str,
    target_band: float = 7.5,
) -> FallbackShadowingAssessment:
    """
    Calculate shadowing assessment using pure text comparison.
    Used when Google AI transcription is unavailable.
    """
    # Tokenize
    target_words = target_text.split()
    user_words = user_transcript.split()
    
    # Word-by-word comparison
    word_by_word = []
    matched_count = 0
    
    for i, target_word in enumerate(target_words):
        if i < len(user_words):
            user_word = user_words[i]
            similarity = _calculate_word_similarity(target_word, user_word)
            is_match = similarity >= 0.8
            
            if is_match:
                matched_count += 1
                
            word_by_word.append({
                "target": target_word,
                "user": user_word if i < len(user_words) else "",
                "similarity": round(similarity, 2),
                "match": is_match,
            })
        else:
            word_by_word.append({
                "target": target_word,
                "user": "",
                "similarity": 0.0,
                "match": False,
            })
    
    # Calculate scores
    phoneme_accuracy = matched_count / len(target_words) if target_words else 0.0
    
    # Rhythm score based on word count ratio and sentence structure match
    word_count_ratio = min(len(user_words), len(target_words)) / max(len(user_words), len(target_words)) if target_words else 0.0
    
    # Connected speech: check for missing articles, prepositions
    function_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "but", "or"}
    target_functions = [w for w in target_words if w.lower() in function_words]
    user_functions = [w for w in user_words if w.lower() in function_words]
    function_match = len(set(f.lower() for f in target_functions) & set(f.lower() for f in user_functions))
    connected_speech_score = function_match / len(target_functions) if target_functions else word_count_ratio
    
    # Rhythm score combines word count ratio and sentence length consistency
    rhythm_score = (word_count_ratio + phoneme_accuracy) / 2
    
    overall_similarity = (phoneme_accuracy + rhythm_score + connected_speech_score) / 3
    
    # Generate feedback
    errors = []
    if phoneme_accuracy < 0.75:
        errors.append(f"Word accuracy is {int(phoneme_accuracy * 100)}% ΓÇö aim for 75%+")
    if rhythm_score < 0.70:
        errors.append("Work on matching the pace and structure of the model")
    if connected_speech_score < 0.70:
        errors.append("Don't skip function words like articles and prepositions")
    
    feedback = "Good effort! " if overall_similarity >= 0.7 else "Keep practicing! "
    feedback += f"You matched {matched_count} of {len(target_words)} words correctly."
    
    passed = phoneme_accuracy >= 0.75 and rhythm_score >= 0.70
    
    return FallbackShadowingAssessment(
        passed=passed,
        phoneme_accuracy=round(phoneme_accuracy, 2),
        rhythm_score=round(rhythm_score, 2),
        connected_speech_score=round(connected_speech_score, 2),
        overall_similarity=round(overall_similarity, 2),
        feedback=feedback,
        specific_errors=errors[:3],
        word_by_word=word_by_word,
    )


@router.post("/assess-shadowing")
async def assess_shadowing(
    audio: UploadFile = File(...),
    target_tier_text: str = Form(...),
    target_band: float = Form(7.5),
):
    """
    Assess a student's shadowing recording against a target mutation tier.
    Accepts multipart/form-data: audio file + target_tier_text + target_band.
    Returns ShadowingAssessmentResponse. passed=True only when
    phoneme_accuracy >= 0.75 AND rhythm_score >= 0.70 (enforced server-side).
    """
    suffix = ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        client = get_llm_client()

        # Step 1: Transcribe the shadowing attempt
        user_transcript = client.transcribe_audio(
            tmp_path,
            prompt="Transcribe this speech recording accurately."
        )

        # Step 2: Compare against target text
        comparison_prompt = f"""Compare this student's spoken response against the target text.

TARGET TEXT (Band {target_band}):
{target_tier_text}

STUDENT'S TRANSCRIBED SPEECH:
{user_transcript}

Evaluate on three dimensions (each 0.0ΓÇô1.0):
1. phoneme_accuracy ΓÇö How accurately were words pronounced? (compare word-by-word)
2. rhythm_score ΓÇö Did natural stress and intonation match the target?
3. connected_speech_score ΓÇö Were words linked naturally (elision, linking)?

List up to 3 specific errors: exact word/phrase that was wrong and why.
Write a 2-sentence feedback message addressed to the student.

PASS CRITERIA: phoneme_accuracy >= 0.75 AND rhythm_score >= 0.70

Return JSON:
{{
  "passed": false,
  "phoneme_accuracy": 0.0,
  "rhythm_score": 0.0,
  "connected_speech_score": 0.0,
  "overall_similarity": 0.0,
  "feedback": "...",
  "specific_errors": ["error1", "error2", "error3"]
}}"""

        result = client.generate_structured(
            prompt=comparison_prompt,
            schema=ShadowingAssessmentResponse,
            temperature=0.2,
        )

        # Enforce pass criteria server-side ΓÇö model output is advisory only
        result.passed = (
            result.phoneme_accuracy >= 0.75
            and result.rhythm_score >= 0.70
        )
        result.overall_similarity = round(
            (result.phoneme_accuracy + result.rhythm_score + result.connected_speech_score) / 3, 2
        )

        return result

    except Exception as e:
        # Return fallback assessment indicator
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "transcription_unavailable",
                "message": "Google AI transcription not available. Use Web Speech API fallback.",
                "fallback_endpoint": "/api/agent/assess-shadowing-fallback",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shadowing assessment failed: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/assess-shadowing-fallback", response_model=FallbackShadowingAssessment)
async def assess_shadowing_fallback(
    user_transcript: str = Form(...),
    target_tier_text: str = Form(...),
    target_band: float = Form(7.5),
):
    """
    Fallback shadowing assessment using text comparison.
    Used when Web Speech API is used for transcription (non-Google mode).
    
    Frontend calls this after getting transcript from Web Speech API.
    """
    return _fallback_shadowing_assessment(user_transcript, target_tier_text, target_band)


# ============ Council of Judges ============


@router.post("/council-evaluate")
async def council_evaluate(request: WritingScoreRequest):
    """
    Run the full Council of Judges multi-agent evaluation pipeline.
    Returns per-agent verdicts + Chief Examiner reconciliation.
    Falls back to single-agent scoring if council fails.
    """
    from services.agents.council import run_council, CouncilReport

    try:
        report: CouncilReport = await run_council(
            essay=request.essay,
            task_type=request.task_type,
            target_band=7.0,
        )
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Council evaluation failed: {str(e)}")