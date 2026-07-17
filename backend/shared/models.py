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
    mastery: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="grammar_skills")
    mistakes: Mapped[list["GrammarMistake"]] = relationship(
        "GrammarMistake", back_populates="skill", cascade="all, delete-orphan"
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    skill: Mapped["GrammarSkill"] = relationship("GrammarSkill", back_populates="mistakes")


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


# Add indexes for performance
Index("idx_sessions_user_skill", Session.user_id, Session.skill)
Index("idx_sessions_created", Session.started_at)
Index("idx_user_responses_session", UserResponse.session_id)
Index("idx_vocabulary_user_mastery", Vocabulary.user_id, Vocabulary.mastery)
Index("idx_grammar_skill_user", GrammarSkill.user_id)
Index("idx_daily_tasks_user_date", DailyTask.user_id, DailyTask.date)