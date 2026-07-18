# IELTS Tutor - Future Implementation Plans

This document contains detailed implementation plans for Writing, Listening, Speaking, and VLM Import modules. The Reading module has been fully implemented and serves as the reference architecture.

---

## Table of Contents

1. [Writing Module](#writing-module)
2. [Listening Module](#listening-module)
3. [Speaking Module](#speaking-module)
4. [VLM Import Module](#vlm-import-module)
5. [Database Migrations](#database-migrations)
6. [Integration Checklist](#integration-checklist)

---

## Writing Module

### Overview

AI-generated writing tasks with rubric-based scoring using Gemma 4. Users can generate Task 1 or Task 2 prompts, write essays, and receive detailed band scores with inline corrections.

### Backend Implementation

#### Files to Modify

- `backend/services/writing/main.py` — Add generate endpoint, upgrade scoring
- `backend/services/ai_agent/main.py` — Use GemmaClient for scoring

#### New Endpoints

```
POST /api/writing/generate-task
  Request: { task_type: "task_1" | "task_2", topic?: string, target_band?: number }
  Response: WritingTaskPublic

POST /api/writing/submit
  Request: { task_id: number, essay: string }
  Response: WritingSubmitResponse (with structured WritingFeedback)
```

#### Implementation Steps

1. **Generate Task Endpoint**

```python
@router.post("/generate-task")
async def generate_writing_task(
    request: GenerateWritingTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new IELTS writing task using Gemma 4."""
    from shared.schemas import WritingTaskPublic
    from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError
    
    # Build prompt
    if request.task_type == "task_1":
        prompt = f"""Generate an IELTS Writing Task 1 prompt.
        
Topic: {request.topic or "random data visualization"}
Target Band: {request.target_band}

Create a chart/graph description task. Return ONLY the prompt text."""
    else:
        prompt = f"""Generate an IELTS Writing Task 2 prompt.

Topic: {request.topic or "society/education"}
Target Band: {request.target_band}

Create an opinion/argument essay question. Return ONLY the prompt text."""
    
    try:
        client = get_gemma_client()
        prompt_text = client.generate_text(prompt, temperature=0.7)
        
        task = WritingTask(
            task_type=request.task_type,
            prompt=prompt_text,
            min_words=250 if request.task_type == "task_2" else 150,
            generation_params={"topic": request.topic, "target_band": request.target_band},
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return WritingTaskPublic.model_validate(task)
    except GemmaClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
```

2. **Upgrade Submit Endpoint**

```python
@router.post("/submit")
async def submit_essay(
    submission: WritingSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit essay for AI scoring with structured feedback."""
    from shared.schemas import WritingFeedback
    from services.ai_agent.gemma_client import get_gemma_client
    
    # ... existing session creation code ...
    
    # Build scoring prompt
    prompt = f"""You are an IELTS examiner. Score this {task.task_type} essay.

ESSAY:
{submission.essay}

Score each criterion (1-9):
- Task Response (or Task Achievement for Task 1)
- Coherence and Cohesion
- Lexical Resource
- Grammatical Range and Accuracy

For each criterion:
1. Give a band score
2. Write a 2-3 sentence explanation
3. Provide one specific improvement tip

Also identify 3-5 inline corrections (grammar, vocabulary, punctuation).

Return JSON matching the WritingFeedback schema."""
    
    client = get_gemma_client()
    feedback: WritingFeedback = client.generate_structured(
        prompt, 
        schema=WritingFeedback,
        temperature=0.2
    )
    
    # Store in session
    session.feedback_data = feedback.model_dump()
    session.band_estimate = feedback.overall
    session.score = feedback.overall * 10
    session.finished_at = datetime.utcnow()
    await db.commit()
    
    return WritingSubmitResponse(
        session_id=session.id,
        word_count=len(submission.essay.split()),
        band_estimate=feedback.overall,
        feedback=feedback,
    )
```

### Frontend Implementation

#### Files to Create

- `frontend/src/lib/store/writingStore.ts` — Zustand store
- `frontend/src/components/features/writing/WritingTaskCard.tsx` — Task display
- `frontend/src/components/features/writing/EssayEditor.tsx` — Textarea with word count
- `frontend/src/components/features/writing/CriterionFeedbackTabs.tsx` — Tab-by-criterion feedback
- `frontend/src/components/features/writing/AnnotatedEssay.tsx` — Essay with corrections highlighted

#### Components

```typescript
// writingStore.ts
interface WritingState {
  phase: 'config' | 'writing' | 'review'
  taskId: number | null
  taskType: 'task_1' | 'task_2'
  prompt: string
  minWords: number
  essay: string
  feedback: WritingFeedback | null
  // actions...
}

// CriterionFeedbackTabs.tsx
// Four tabs: Task Response, Coherence, Lexical, Grammar
// Each shows: band score, progress bar, explanation, improvement tip

// AnnotatedEssay.tsx
// Renders essay text with inline corrections highlighted
// Hover shows: "incorrect → correct: explanation"
```

#### Page Update

```typescript
// page.tsx flow:
// 1. Select task type (Task 1 / Task 2)
// 2. Optionally specify topic
// 3. Generate task → shows prompt
// 4. Write essay in editor (word count live)
// 5. Submit → loading state
// 6. Show CriterionFeedbackTabs + AnnotatedEssay
```

---

## Listening Module

### Overview

AI-generated listening scripts with browser SpeechSynthesis for audio playback. Users configure section type, accent, speed, topic, and weakness focus.

### Backend Implementation

#### Files to Modify

- `backend/services/listening/main.py` — Add generate endpoint

#### New Endpoints

```
POST /api/listening/generate
  Request: ListeningGenerationParams
  Response: GeneratedListeningResponse
```

#### Implementation

```python
@router.post("/generate")
async def generate_listening(
    config: ListeningGenerationParams,
    db: AsyncSession = Depends(get_db),
):
    """Generate an IELTS listening script with questions."""
    from shared.schemas import ExamOutput
    from services.ai_agent.gemma_client import get_gemma_client
    
    # Build prompt based on section type
    section_context = {
        1: "a conversation between two people in an everyday social situation",
        2: "a monologue set in an everyday social situation",
        3: "a discussion between up to four people in an educational context",
        4: "a monologue on an academic subject",
    }
    
    prompt = f"""Generate an IELTS Listening Section {config.section} script.

Context: {section_context[config.section]}
Topic: {config.topic}
Accent hint: {config.accent} English style

Generate:
1. A realistic {400 + config.section * 100} word script with natural hesitations
2. {config.question_count} questions of types: {', '.join(config.question_types)}

For each question:
- The correct answer
- The word range in the script where the answer appears
- Cognitive distractor analysis

Return JSON matching the ExamOutput schema."""
    
    client = get_gemma_client()
    exam: ExamOutput = client.generate_structured(prompt, schema=ExamOutput)
    
    # Build TTS config
    tts_lang = {"british": "en-GB", "australian": "en-AU", "american": "en-US"}[config.accent]
    tts_rate = {"normal": 0.9, "exam": 1.0, "fast": 1.15}[config.speed]
    
    # Store in DB
    script_text = "\n\n".join([p.text for p in exam.paragraphs])
    section = ListeningSection(
        title=exam.title,
        transcript=script_text,
        duration=len(script_text.split()) // 2,  # Rough estimate: ~120 wpm
        difficulty="medium",
        generation_params=config.model_dump(),
        tts_config={"lang": tts_lang, "rate": tts_rate},
    )
    db.add(section)
    await db.flush()
    
    # Create questions...
    # Create session...
    
    return GeneratedListeningResponse(
        section_id=section.id,
        session_id=session.id,
        title=section.title,
        script=script_text,
        tts_config=TTSConfig(lang=tts_lang, rate=tts_rate),
        question_groups=[...],  # Strip answers
    )
```

### Frontend Implementation

#### Files to Create

- `frontend/src/lib/store/listeningStore.ts`
- `frontend/src/hooks/useSpeechSynthesis.ts`
- `frontend/src/components/features/listening/ListeningPlayer.tsx`
- `frontend/src/components/features/listening/ListeningConfigPanel.tsx`

#### SpeechSynthesis Hook

```typescript
// useSpeechSynthesis.ts
export function useSpeechSynthesis() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentCharIndex, setCurrentCharIndex] = useState(0)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  
  const speak = useCallback((text: string, config: TTSConfig) => {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = config.lang
    utterance.rate = config.rate
    utterance.pitch = config.pitch || 1.0
    
    // Select voice by lang
    const voices = window.speechSynthesis.getVoices()
    const voice = voices.find(v => v.lang.startsWith(config.lang.split('-')[0]))
    if (voice) utterance.voice = voice
    
    utterance.onboundary = (e) => setCurrentCharIndex(e.charIndex)
    utterance.onend = () => setIsPlaying(false)
    
    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
    setIsPlaying(true)
  }, [])
  
  const pause = () => window.speechSynthesis.pause()
  const resume = () => window.speechSynthesis.resume()
  const stop = () => window.speechSynthesis.cancel()
  
  return { speak, pause, resume, stop, isPlaying, currentCharIndex }
}
```

#### Player Component

```typescript
// ListeningPlayer.tsx
// - Shows script text with current word highlighted
// - Play/Pause/Stop controls
// - Speed selector
// - Progress bar
// - Rewind 10s / Forward 10s buttons
```

---

## Speaking Module

### Overview

30-second audio recording with Gemma 4 transcription and IELTS band analysis. Users speak into their microphone, and receive detailed feedback on fluency, lexical resource, grammar, and pronunciation.

### Backend Implementation

#### New Endpoint

```
POST /api/agent/transcribe-speaking
  Request: multipart/form-data (audio file)
  Response: SpeakingFeedback
```

#### Implementation

```python
@router.post("/transcribe-speaking")
async def transcribe_speaking(
    audio: UploadFile = File(...),
):
    """Transcribe and analyze 30-second speaking sample."""
    from shared.schemas import SpeakingFeedback
    from services.ai_agent.gemma_client import get_gemma_client
    
    # Save temp file
    temp_path = f"/tmp/{uuid.uuid4()}.webm"
    with open(temp_path, "wb") as f:
        f.write(await audio.read())
    
    client = get_gemma_client()
    
    # Transcribe
    transcript = client.transcribe_audio(temp_path)
    
    # Analyze
    prompt = f"""You are an IELTS Speaking examiner. Analyze this speaking sample.

TRANSCRIPT:
{transcript}

Score the speaker (1-9) on:
- Fluency and Coherence
- Lexical Resource
- Grammatical Range and Accuracy
- Pronunciation

Provide the overall band score and 3 specific improvement suggestions.

Return JSON matching the SpeakingFeedback schema."""
    
    feedback: SpeakingFeedback = client.generate_structured(
        prompt,
        schema=SpeakingFeedback,
        temperature=0.2
    )
    
    # Cleanup
    os.remove(temp_path)
    
    return feedback
```

### Frontend Implementation

#### Files to Create

- `frontend/src/hooks/useAudioRecorder.ts`
- `frontend/src/components/features/speaking/SpeakingRecorder.tsx`
- `frontend/src/components/features/speaking/SpeakingFeedback.tsx`

#### Audio Recorder Hook

```typescript
// useAudioRecorder.ts
export function useAudioRecorder(maxDuration: number = 30) {
  const [isRecording, setIsRecording] = useState(false)
  const [secondsRemaining, setSecondsRemaining] = useState(maxDuration)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    const chunks: Blob[] = []
    
    recorder.ondataavailable = (e) => chunks.push(e.data)
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/webm' })
      setAudioBlob(blob)
      stream.getTracks().forEach(t => t.stop())
    }
    
    recorder.start()
    mediaRecorderRef.current = recorder
    setIsRecording(true)
    
    // Countdown
    const interval = setInterval(() => {
      setSecondsRemaining((s) => {
        if (s <= 1) {
          recorder.stop()
          setIsRecording(false)
          clearInterval(interval)
          return 0
        }
        return s - 1
      })
    }, 1000)
  }
  
  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }
  
  return { startRecording, stopRecording, isRecording, secondsRemaining, audioBlob }
}
```

---

## VLM Import Module

### Overview

Replace Tesseract OCR with Gemma 4 Vision for intelligent exam import. Users upload photos of IELTS book pages, and receive structured exams with paragraphs, questions, and hidden evaluation data.

### Backend Implementation

#### Files to Modify

- `backend/services/import_svc/main.py` — Replace OCR with VLM

#### Implementation

```python
async def process_import_with_vlm(
    import_id: int,
    image_paths: list[str],
    db: AsyncSession,
):
    """Process import using Gemma 4 Vision."""
    from shared.schemas import ExamOutput
    from services.ai_agent.gemma_client import get_gemma_client
    
    r = await get_redis()
    await r.set(f"import:{import_id}:status", "processing")
    
    try:
        client = get_gemma_client()
        
        # Process each image
        all_outputs = []
        for image_path in image_paths:
            prompt = """Analyze this IELTS exam page.

1. Extract the reading passage with paragraphs labeled A, B, C, etc.
2. Identify all question groups and their types.
3. For each question, determine:
   - The correct answer from the text
   - The paragraph where the answer is found
   - Why students might choose a wrong answer

Return JSON matching the ExamOutput schema."""
            
            exam: ExamOutput = client.generate_structured(
                prompt,
                schema=ExamOutput,
                image_path=image_path,
                temperature=0.0
            )
            all_outputs.append(exam)
        
        # Merge outputs if multiple pages
        merged = merge_exam_outputs(all_outputs)
        
        # Check if questions were found
        if not merged.question_groups:
            await r.set(f"import:{import_id}:status", "needs_questions")
            await r.set(f"import:{import_id}:text", merged.paragraphs[0].text if merged.paragraphs else "")
            return
        
        # Store in DB (same as reading generate)
        passage = await store_generated_exam(merged, db)
        
        # Update import job
        job = await db.get(ImportJob, import_id)
        job.passage_id = passage.id
        job.status = "completed"
        
        # Create session
        session = PracticeSession(
            user_id=1,
            skill="reading",
            passage_id=passage.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        await r.set(f"import:{import_id}:status", "completed")
        await r.set(f"import:{import_id}:passage_id", str(passage.id))
        await r.set(f"import:{import_id}:session_id", str(session.id))
        
    except Exception as e:
        await r.set(f"import:{import_id}:status", "failed")
        await r.set(f"import:{import_id}:error", str(e))
```

#### Updated Import Response

```python
class ImportStatusResponse(BaseModel):
    import_id: int
    status: str  # pending | processing | completed | failed | needs_questions
    passage_id: Optional[int] = None
    session_id: Optional[int] = None
    needs_question_generation: bool = False
    extracted_text: Optional[str] = None  # Preview for "needs_questions" case
    error: Optional[str] = None
```

### Frontend Update

- Update `frontend/src/lib/services/import.ts` with new response type
- Show "Generate questions?" dialog when `needs_questions: true`
- Redirect to `/practice/reading?session_id=X` on completion

---

## Database Migrations

Run these migrations to add new columns:

```bash
cd backend
alembic revision -m "add_generation_and_evaluation_columns"
```

```python
# alembic/versions/xxx_add_generation_and_evaluation_columns.py
def upgrade():
    op.add_column('reading_passages', sa.Column('generation_params', sa.JSON(), nullable=True))
    op.add_column('reading_questions', sa.Column('group_id', sa.String(50), nullable=True))
    op.add_column('reading_questions', sa.Column('question_number', sa.Integer(), nullable=True))
    op.add_column('reading_questions', sa.Column('question_evaluation', sa.JSON(), nullable=True))
    op.add_column('listening_sections', sa.Column('generation_params', sa.JSON(), nullable=True))
    op.add_column('listening_sections', sa.Column('tts_config', sa.JSON(), nullable=True))
    op.add_column('listening_questions', sa.Column('group_id', sa.String(50), nullable=True))
    op.add_column('listening_questions', sa.Column('question_number', sa.Integer(), nullable=True))
    op.add_column('listening_questions', sa.Column('question_evaluation', sa.JSON(), nullable=True))
    op.add_column('writing_tasks', sa.Column('generation_params', sa.JSON(), nullable=True))
    op.add_column('sessions', sa.Column('feedback_data', sa.JSON(), nullable=True))
    op.add_column('user_responses', sa.Column('error_analysis', sa.JSON(), nullable=True))

def downgrade():
    # Drop all added columns
    pass
```

---

## Integration Checklist

After implementing each module:

1. **Test Backend Endpoints**
   - [ ] Health check returns 200
   - [ ] Generate endpoint returns structured data
   - [ ] Submit endpoint stores to DB correctly
   - [ ] BackendEvaluation is never in frontend responses

2. **Test Frontend Components**
   - [ ] Config panel validates inputs
   - [ ] Loading states show correctly
   - [ ] Error states display helpful messages
   - [ ] Workspace renders passage + questions
   - [ ] Review panel shows tab-by-tab analysis

3. **Test E2E Flow**
   - [ ] Generate → Workspace → Submit → Review
   - [ ] Answers persist across navigation
   - [ ] Score calculated correctly
   - [ ] Evidence paragraphs highlight correctly

4. **Test Gemma 4 Integration**
   - [ ] API key configured in .env
   - [ ] Structured output parses without errors
   - [ ] Fallback handling for API failures

---

## Summary

| Module | Backend | Frontend | Status |
|--------|---------|----------|--------|
| Reading | ✅ Complete | ✅ Complete | Done |
| Writing | ✅ Complete | ✅ Complete | Done |
| Listening | ✅ Complete | ✅ Complete | Done |
| Speaking | ✅ Complete | ✅ Complete | Done |
| Import (VLM) | ✅ Complete | ✅ Complete | Done |
| Grammar | ✅ Complete | ✅ Complete | Done |
| Vocabulary | ✅ Complete | ✅ Complete | Done |
| Mock Test | ✅ Complete | ✅ Complete | Done |

The Reading module serves as the reference implementation. Follow the same patterns:
- Zustand store for state
- Config → Workspace → Review flow
- GemmaClient for all AI calls
- Schemas from `shared/schemas.py`
- BackendEvaluation never exposed to frontend
