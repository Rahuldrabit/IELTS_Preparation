from .core import User, Session
from .exam import ReadingPassage, ReadingQuestion, ListeningSection, ListeningQuestion, WritingTask, MockTest, MockTestSection
from .grammar import GrammarSkill, GrammarMistake, GrammarTopic, GrammarExercise, GrammarAttempt, GrammarNote, GrammarLearningHistory, ErrorSignature
from .learning import Vocabulary, DailyTask, Milestone, UserAchievement
from .telemetry import UserResponse, WeeklyErrorReport, ImportJob

# Indexes
from sqlalchemy import Index
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
Index("idx_error_signature_user_skill", ErrorSignature.user_id, ErrorSignature.skill)
Index("idx_error_signature_user_pattern", ErrorSignature.user_id, ErrorSignature.pattern_key)
Index("idx_weekly_error_report_user_week", WeeklyErrorReport.user_id, WeeklyErrorReport.week_start)
