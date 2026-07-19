"""SQLAlchemy ORM models for IELTS Tutor."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


# ============ User & Profile Models ============


class User(Base):
    """User profile and preferences."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)  # Nullable for no-auth MVP
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_band: Mapped[float] = mapped_column(Numeric(3, 1), default=6.5)
    target_band: Mapped[float] = mapped_column(Numeric(3, 1), default=8.0)
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    daily_goal: Mapped[int] = mapped_column(Integer, default=5)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    # Stores user's feature flag preferences (JSON, nullable — defaults to all-off)
    features_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores the latest Uma intervention from the Autonomous Syllabus Curating Agent
    ava_intervention: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Onboarding fields ────────────────────────────────────────────────────────
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    native_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ielts_module: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # academic | general
    reason_for_ielts: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    focus_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # e.g. ["reading", "writing"]
    study_hours_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    vocabulary: Mapped[list["Vocabulary"]] = relationship(
        "Vocabulary", back_populates="user", cascade="all, delete-orphan"
    )
    grammar_skills: Mapped[list["GrammarSkill"]] = relationship(
        "GrammarSkill", back_populates="user", cascade="all, delete-orphan"
    )
    daily_tasks: Mapped[list["DailyTask"]] = relationship(
        "DailyTask", back_populates="user", cascade="all, delete-orphan"
    )
    mock_tests: Mapped[list["MockTest"]] = relationship(
        "MockTest", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )


# ============ Reading Models ============


class ReadingPassage(Base):
    """IELTS reading passage."""

    __tablename__ = "reading_passages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy, medium, hard
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Stores GenerationParams dict from AI generation (topic, vocab_level, grammar_complexity etc.)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list["ReadingQuestion"]] = relationship(
        "ReadingQuestion", back_populates="passage", cascade="all, delete-orphan"
    )


class ReadingQuestion(Base):
    """Individual reading question."""

    __tablename__ = "reading_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reading_passages.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # multiple-choice, true-false, fill-blank, MATCHING_HEADINGS, SUMMARY_COMPLETION etc.
    # Group ID ties this question to its QuestionGroup (e.g. "group_1")
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Sequential number within its group
    question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # For MCQ / Matching
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Stores BackendEvaluation dict — NEVER sent to frontend
    question_evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    passage: Mapped["ReadingPassage"] = relationship("ReadingPassage", back_populates="questions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="reading_question", cascade="all, delete-orphan"
    )


# ============ Listening Models ============


class ListeningSection(Base):
    """IELTS listening section (audio with questions)."""

    __tablename__ = "listening_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Stores GenerationParams + TTS config (accent, speed, rate)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tts_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list["ListeningQuestion"]] = relationship(
        "ListeningQuestion", back_populates="section", cascade="all, delete-orphan"
    )


class ListeningQuestion(Base):
    """Individual listening question."""

    __tablename__ = "listening_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listening_sections.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    timestamp_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Stores BackendEvaluation dict — NEVER sent to frontend
    question_evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    section: Mapped["ListeningSection"] = relationship("ListeningSection", back_populates="questions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="listening_question", cascade="all, delete-orphan"
    )


# ============ Writing Models ============


class WritingTask(Base):
    """IELTS writing task (Task 1 or Task 2)."""

    __tablename__ = "writing_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # task_1, task_2
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_words: Mapped[int] = mapped_column(Integer, default=150)
    band_descriptor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Stores generation params (topic, target_band)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============ Session & Response Models ============


class Session(Base):
    """Practice session (reading, listening, writing, etc.)."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, listening, writing, etc.
    passage_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_passages.id"), nullable=True
    )
    listening_section_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_sections.id"), nullable=True
    )
    writing_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("writing_tasks.id"), nullable=True
    )
    user_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Essay text for writing
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    band_estimate: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    # Stores structured WritingFeedback or SpeakingFeedback JSON from Gemma 4
    feedback_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    responses: Mapped[list["UserResponse"]] = relationship(
        "UserResponse", back_populates="session", cascade="all, delete-orphan"
    )


class UserResponse(Base):
    """User's answer to a specific question."""

    __tablename__ = "user_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    reading_question_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_questions.id"), nullable=True
    )
    listening_question_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_questions.id"), nullable=True
    )
    user_answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores per-question ExplanationResult from Gemma 4 analysis — includes why_wrong, strategy
    error_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="responses")
    reading_question: Mapped[Optional["ReadingQuestion"]] = relationship(
        "ReadingQuestion", back_populates="responses"
    )
    listening_question: Mapped[Optional["ListeningQuestion"]] = relationship(
        "ListeningQuestion", back_populates="responses"
    )


# ============ Vocabulary Models ============


class Vocabulary(Base):
    """User's vocabulary word."""

    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    pronunciation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meaning: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    synonyms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    antonyms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    collocations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    word_family: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    cefr: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # A1-C2
    ielts_frequency: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    mastery: Mapped[str] = mapped_column(String(20), default="new")  # new, learning, mastered
    ease_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=2.5)  # SM-2
    interval: Mapped[int] = mapped_column(Integer, default=1)  # days
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    first_seen: Mapped[date] = mapped_column(Date, default=date.today)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Smart Vocabulary Harvesting fields
    ai_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Context-specific AI definition
    contexts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of {sentence, source_type, source_id}

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vocabulary")


# ============ Grammar Models ============


class GrammarSkill(Base):
    """User's grammar skill mastery."""

    __tablename__ = "grammar_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Articles, Tenses, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Which module this belongs to (e.g., "Foundations", "Verb System")
    mastery: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)  # 0-1 based on performance consistency
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    recent_performance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Last 5 attempts: {"scores": [1,0,1,1,0], "timestamps": [...]}
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="grammar_skills")
    mistakes: Mapped[list["GrammarMistake"]] = relationship(
        "GrammarMistake", back_populates="skill", cascade="all, delete-orphan"
    )
    learning_history: Mapped[list["GrammarLearningHistory"]] = relationship(
        "GrammarLearningHistory", back_populates="skill", cascade="all, delete-orphan"
    )
    notes: Mapped[list["GrammarNote"]] = relationship(
        "GrammarNote", back_populates="skill", cascade="all, delete-orphan"
    )


class GrammarMistake(Base):
    """Recorded grammar mistake."""

    __tablename__ = "grammar_mistakes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False
    )
    incorrect_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    correct_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # reading, writing, etc.
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # More specific error classification
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="mistakes")


class GrammarTopic(Base):
    """Grammar topic structure from curriculum."""

    __tablename__ = "grammar_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # Which module this belongs to
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_in_module: Mapped[int] = mapped_column(Integer, default=0)  # For ordering within module
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of prerequisite topic IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GrammarExercise(Base):
    """Generated grammar exercise instance."""

    __tablename__ = "grammar_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_topics.id"), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fill_blank, drag_drop, etc.
    question_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Structure varies by type
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    topic: Mapped["GrammarTopic"] = relationship("GrammarTopic")


class GrammarAttempt(Base):
    """User's attempt at a grammar exercise."""

    __tablename__ = "grammar_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_exercises.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id"), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    exercise: Mapped["GrammarExercise"] = relationship("GrammarExercise")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill")


class GrammarNote(Base):
    """Auto-generated grammar note for repeated mistakes."""

    __tablename__ = "grammar_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mistake_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="notes")


class GrammarLearningHistory(Base):
    """Track grammar learning activities."""

    __tablename__ = "grammar_learning_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_skills.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # lesson, exercise, writing_practice, speaking_practice
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="learning_history")


# ============ Daily Tasks Model ============


class DailyTask(Base):
    """Daily roadmap task for user."""

    __tablename__ = "daily_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, vocabulary, etc.
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_tasks")


# ============ Import Queue Model ============


class ImportJob(Base):
    """Background import job for OCR processing."""

    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_type: Mapped[str] = mapped_column(String(20), nullable=False)  # reading, listening
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    file_paths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    passage_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reading_passages.id"), nullable=True
    )
    listening_section_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("listening_sections.id"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ============ Milestones Model ============


class Milestone(Base):
    """User's progress milestones (band levels)."""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    band: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="locked"
    )  # locked, current, completed
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============ Mock Test Models ============


class MockTest(Base):
    """Full IELTS mock test session (Listening + Reading + Writing + Speaking)."""

    __tablename__ = "mock_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    test_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # baseline | generated
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress"
    )  # in_progress | completed | abandoned
    # Overall results
    overall_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    listening_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    reading_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    writing_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    speaking_band: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    # Full AI diagnostic report JSON
    diagnostic_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Stores generated content for each section (so test can be resumed/reviewed)
    section_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mock_tests")
    sections: Mapped[list["MockTestSection"]] = relationship(
        "MockTestSection", back_populates="mock_test", cascade="all, delete-orphan",
        order_by="MockTestSection.section_order"
    )


class MockTestSection(Base):
    """Individual section within a mock test."""

    __tablename__ = "mock_test_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mock_test_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # listening | reading | writing | speaking
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=listening, 2=reading, 3=writing, 4=speaking
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending | in_progress | completed | skipped
    # Timing
    time_allocated_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Content and answers
    content_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Generated/loaded section content
    answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # User's answers for this section
    # Scoring
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    band_estimate: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    # Per-section AI feedback
    section_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Difficulty configuration used for generation
    difficulty_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    mock_test: Mapped["MockTest"] = relationship("MockTest", back_populates="sections")


# Add indexes for performance
Index("idx_sessions_user_skill", Session.user_id, Session.skill)
Index("idx_sessions_created", Session.started_at)
Index("idx_user_responses_session", UserResponse.session_id)
Index("idx_vocabulary_user_mastery", Vocabulary.user_id, Vocabulary.mastery)
Index("idx_grammar_skill_user", GrammarSkill.user_id)
Index("idx_daily_tasks_user_date", DailyTask.user_id, DailyTask.date)
Index("idx_mock_tests_user", MockTest.user_id)
Index("idx_mock_tests_status", MockTest.user_id, MockTest.status)
Index("idx_mock_test_sections_test", MockTestSection.mock_test_id)
Index("idx_grammar_skill_module", GrammarSkill.module)
Index("idx_grammar_topic_module", GrammarTopic.module)
Index("idx_grammar_exercise_topic", GrammarExercise.topic_id)
Index("idx_grammar_attempt_user_exercise", GrammarAttempt.user_id, GrammarAttempt.exercise_id)
Index("idx_grammar_note_user_skill", GrammarNote.user_id, GrammarNote.skill_id)
Index("idx_grammar_history_user_skill", GrammarLearningHistory.user_id, GrammarLearningHistory.skill_id)


# ============ Error DNA Models ============


class ErrorSignature(Base):
    """Recurring error pattern identified by Error DNA analysis."""

    __tablename__ = "error_signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill: Mapped[str] = mapped_column(String(50), nullable=False)  # reading, listening, writing, speaking, grammar
    question_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # IELTS question type
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # comprehension, grammar, vocabulary
    pattern_label: Mapped[str] = mapped_column(String(200), nullable=False)  # Human-readable pattern name
    pattern_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Normalized key for deduplication
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    example_refs: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of session/response IDs
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, fixed, suppressed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WeeklyErrorReport(Base):
    """Weekly Error DNA report generated every Monday."""

    __tablename__ = "weekly_error_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False)  # Contains headline, insight_text, top_patterns
    signature_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of ErrorSignature IDs
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Add indexes for Error DNA
Index("idx_error_signature_user_skill", ErrorSignature.user_id, ErrorSignature.skill)
Index("idx_error_signature_user_pattern", ErrorSignature.user_id, ErrorSignature.pattern_key)
Index("idx_weekly_error_report_user_week", WeeklyErrorReport.user_id, WeeklyErrorReport.week_start)



# ============ Achievement Models ============


class UserAchievement(Base):
    """User's unlocked achievements."""

    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    achievement_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "band_seven", "streak_7"
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
