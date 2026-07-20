import random
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import DailyTask, WeeklyStudyPlan
from . import repository

TASK_TEMPLATES = {
    "reading": [
        {"type": "passage", "title": "Complete 1 Reading Passage", "duration": 20, "priority": "high"},
        {"type": "practice", "title": "Practice T/F/NG Questions", "duration": 15, "priority": "medium"},
        {"type": "vocabulary", "title": "Learn 10 Academic Words", "duration": 10, "priority": "low"},
        {"type": "speed", "title": "Speed Reading Exercise", "duration": 15, "priority": "medium"},
        {"type": "analysis", "title": "Analyze a Model Answer", "duration": 20, "priority": "medium"},
    ],
    "listening": [
        {"type": "section", "title": "Complete 1 Listening Section", "duration": 15, "priority": "high"},
        {"type": "dictation", "title": "Dictation Practice", "duration": 10, "priority": "medium"},
        {"type": "transcript", "title": "Study Transcript Analysis", "duration": 15, "priority": "low"},
        {"type": "shadowing", "title": "Shadowing Practice", "duration": 10, "priority": "medium"},
    ],
    "writing": [
        {"type": "task1", "title": "Write Task 1 Essay", "duration": 20, "priority": "high"},
        {"type": "task2", "title": "Write Task 2 Essay", "duration": 40, "priority": "high"},
        {"type": "planning", "title": "Practice Essay Planning", "duration": 15, "priority": "medium"},
        {"type": "vocabulary", "title": "Learn Linking Words", "duration": 10, "priority": "low"},
    ],
    "speaking": [
        {"type": "part1", "title": "Practice Speaking Part 1", "duration": 10, "priority": "high"},
        {"type": "part2", "title": "Practice Cue Card (Part 2)", "duration": 15, "priority": "high"},
        {"type": "part3", "title": "Practice Discussion (Part 3)", "duration": 15, "priority": "medium"},
        {"type": "shadowing", "title": "Shadowing Practice", "duration": 10, "priority": "medium"},
        {"type": "vocabulary", "title": "Practice Idiomatic Expressions", "duration": 10, "priority": "low"},
    ],
    "vocabulary": [
        {"type": "learn", "title": "Learn 15 New Words", "duration": 15, "priority": "high"},
        {"type": "review", "title": "Review Vocabulary Deck", "duration": 10, "priority": "medium"},
        {"type": "context", "title": "Practice Words in Context", "duration": 15, "priority": "medium"},
    ],
    "grammar": [
        {"type": "exercise", "title": "Grammar Exercise Set", "duration": 15, "priority": "high"},
        {"type": "rule", "title": "Study Grammar Rule", "duration": 10, "priority": "medium"},
        {"type": "correction", "title": "Error Correction Practice", "duration": 15, "priority": "medium"},
    ],
}

GRAMMAR_TOPICS = [
    "Relative Clauses",
    "Conditionals",
    "Passive Voice",
    "Articles",
    "Tense Consistency",
    "Subject-Verb Agreement",
    "Complex Sentences",
    "Modals",
]

async def calculate_streak(user_id: int, db: AsyncSession) -> int:
    sessions = await repository.get_recent_sessions(user_id, db)
    if not sessions:
        return 0
    
    streak = 0
    today = date.today()
    session_dates = set(s.started_at.date() for s in sessions)
    
    check_date = today
    while check_date in session_dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak

def _select_tasks_for_day(task_id: int, day: str, date_obj: date, skill_weights: dict[str, float], count: int) -> list[DailyTask]:
    tasks = []
    sorted_skills = sorted(skill_weights.items(), key=lambda x: -x[1])
    selected = []
    for skill, weight in sorted_skills:
        if len(selected) >= count:
            break
        if skill in TASK_TEMPLATES and random.random() < weight:
            template = random.choice(TASK_TEMPLATES[skill])
            selected.append((skill, template))
    
    while len(selected) < count:
        skill = random.choice(list(TASK_TEMPLATES.keys()))
        template = random.choice(TASK_TEMPLATES[skill])
        selected.append((skill, template))
    
    for i, (skill, template) in enumerate(selected):
        tasks.append(DailyTask(
            id=f"task-{task_id + i}",
            day=day,
            date=date_obj,
            skill=skill,
            task_type=template["type"],
            title=template["title"],
            description=f"Focus: {skill.capitalize()} practice",
            duration_minutes=template["duration"],
            priority=template["priority"],
        ))
    
    return tasks

async def _generate_tasks(
    user_id: int,
    db: AsyncSession,
    week_start: date,
    weak_skills: dict[str, float],
    days_until_exam: Optional[int],
) -> list[DailyTask]:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    tasks = []
    
    skill_weights = {
        "reading": max(0.5, weak_skills.get("reading", 0.5)),
        "listening": max(0.5, weak_skills.get("listening", 0.5)),
        "writing": max(0.5, weak_skills.get("writing", 0.5)),
        "speaking": max(0.5, weak_skills.get("speaking", 0.5)),
        "vocabulary": 0.3,
        "grammar": weak_skills.get("grammar", 0.3),
    }
    
    if days_until_exam and days_until_exam < 14:
        for skill in skill_weights:
            skill_weights[skill] *= 1.3
    
    task_id = 0
    for i, day in enumerate(days):
        current_date = week_start + timedelta(days=i)
        tasks_per_day = 3 if i < 5 else 4
        day_tasks = _select_tasks_for_day(task_id, day, current_date, skill_weights, tasks_per_day)
        tasks.extend(day_tasks)
        task_id += len(day_tasks)
    
    return tasks

def _generate_plan_message(weak_skills: dict[str, float], streak: int, days_until_exam: Optional[int], target_band: float) -> str:
    parts = []
    if streak > 0:
        parts.append(f"You're on a {streak}-day streak! Keep it up!")
    if weak_skills:
        weakest = max(weak_skills.items(), key=lambda x: x[1])
        if weakest[1] > 0.5:
            parts.append(f"This week, we're focusing on improving your {weakest[0]}.")
    if days_until_exam:
        if days_until_exam <= 7:
            parts.append(f"Just {days_until_exam} days until your exam. You've got this!")
        elif days_until_exam <= 14:
            parts.append(f"{days_until_exam} days to your exam. Stay focused!")
    if not parts:
        parts.append(f"Here's your personalized plan to reach Band {target_band}.")
    return " ".join(parts)

def _default_plan(user_id: int, week_start: date) -> WeeklyStudyPlan:
    tasks = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    task_id = 0
    for i, day in enumerate(days):
        current_date = week_start + timedelta(days=i)
        default_tasks = [
            ("reading", TASK_TEMPLATES["reading"][0]),
            ("listening", TASK_TEMPLATES["listening"][0]),
            ("vocabulary", TASK_TEMPLATES["vocabulary"][0]),
        ]
        for skill, template in default_tasks:
            tasks.append(DailyTask(
                id=f"task-{task_id}", day=day, date=current_date, skill=skill, task_type=template["type"],
                title=template["title"], description=f"Focus: {skill.capitalize()} practice",
                duration_minutes=template["duration"], priority=template["priority"],
            ))
            task_id += 1
    
    return WeeklyStudyPlan(
        user_id=user_id, week_start=week_start, week_end=week_start + timedelta(days=6), target_band=7.0,
        current_streak=0, tasks=tasks, focus_skills=["reading", "listening", "vocabulary"],
        total_minutes=sum(t.duration_minutes for t in tasks), completed_tasks=0,
        message="Here's your weekly study plan. Complete practice sessions to get personalized recommendations!",
    )

async def generate_weekly_study_plan(user_id: int, db: AsyncSession, week_start: Optional[date] = None) -> WeeklyStudyPlan:
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    user = await repository.get_user(user_id, db)
    if not user:
        return _default_plan(user_id, week_start)
    
    target_band = float(user.target_band) if user.target_band else 7.0
    days_until_exam = (user.exam_date - date.today()).days if user.exam_date else None
    weak_skills = await repository.get_weak_skills(user_id, db)
    streak = await calculate_streak(user_id, db)
    
    tasks = await _generate_tasks(user_id, db, week_start, weak_skills, days_until_exam)
    grammar_focus = random.choice(GRAMMAR_TOPICS) if weak_skills.get("grammar", 0) > 0.3 else None
    
    total_minutes = sum(t.duration_minutes for t in tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    message = _generate_plan_message(weak_skills, streak, days_until_exam, target_band)
    
    return WeeklyStudyPlan(
        user_id=user_id, week_start=week_start, week_end=week_end, target_band=target_band,
        days_until_exam=days_until_exam, current_streak=streak, tasks=tasks,
        focus_skills=list(weak_skills.keys())[:3], grammar_focus=grammar_focus,
        total_minutes=total_minutes, completed_tasks=completed_tasks, message=message,
    )
