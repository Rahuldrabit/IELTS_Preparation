"""
Achievements & Milestones System - Badges, streaks, unlocks.

Task 11: Achievements & Milestones system
- Define achievement types and criteria
- Track user progress toward achievements
- Unlock achievements when criteria met
- Support streak-based achievements
"""
from datetime import datetime, date, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import User, Session as SessionModel


# ─────────────────────────────────────────────
#  Achievement Definitions
# ─────────────────────────────────────────────

ACHIEVEMENTS = {
    # Practice Milestones
    "first_practice": {
        "name": "First Steps",
        "description": "Complete your first practice session",
        "icon": "🎯",
        "category": "milestone",
        "tier": 1,
    },
    "ten_sessions": {
        "name": "Getting Started",
        "description": "Complete 10 practice sessions",
        "icon": "📊",
        "category": "milestone",
        "tier": 1,
    },
    "fifty_sessions": {
        "name": "Half Century",
        "description": "Complete 50 practice sessions",
        "icon": "🏆",
        "category": "milestone",
        "tier": 2,
    },
    "hundred_sessions": {
        "name": "Century Club",
        "description": "Complete 100 practice sessions",
        "icon": "💎",
        "category": "milestone",
        "tier": 3,
    },
    
    # Band Score Achievements
    "band_six": {
        "name": "Band 6 Achieved",
        "description": "Score Band 6 or higher in any skill",
        "icon": "🌟",
        "category": "score",
        "tier": 1,
    },
    "band_seven": {
        "name": "Band 7 Achieved",
        "description": "Score Band 7 or higher in any skill",
        "icon": "⭐",
        "category": "score",
        "tier": 2,
    },
    "band_seven_five": {
        "name": "Band 7.5 Achieved",
        "description": "Score Band 7.5 or higher in any skill",
        "icon": "✨",
        "category": "score",
        "tier": 3,
    },
    "band_eight": {
        "name": "Band 8 Achieved",
        "description": "Score Band 8 or higher in any skill",
        "icon": "🌟",
        "category": "score",
        "tier": 4,
    },
    "first_band_7_writing": {
        "name": "Writing Master",
        "description": "Score Band 7+ in Writing",
        "icon": "✍️",
        "category": "skill",
        "tier": 2,
    },
    "first_band_7_speaking": {
        "name": "Speaking Star",
        "description": "Score Band 7+ in Speaking",
        "icon": "🎤",
        "category": "skill",
        "tier": 2,
    },
    
    # Streak Achievements
    "streak_3": {
        "name": "3-Day Streak",
        "description": "Practice for 3 consecutive days",
        "icon": "🔥",
        "category": "streak",
        "tier": 1,
    },
    "streak_7": {
        "name": "Week Warrior",
        "description": "Practice for 7 consecutive days",
        "icon": "🔥",
        "category": "streak",
        "tier": 2,
    },
    "streak_14": {
        "name": "Fortnight Fighter",
        "description": "Practice for 14 consecutive days",
        "icon": "🔥",
        "category": "streak",
        "tier": 3,
    },
    "streak_30": {
        "name": "Monthly Master",
        "description": "Practice for 30 consecutive days",
        "icon": "🔥",
        "category": "streak",
        "tier": 4,
    },
    
    # Skill-Specific Achievements
    "complete_all_reading_types": {
        "name": "Reading Variety",
        "description": "Practice all reading question types",
        "icon": "📚",
        "category": "skill",
        "tier": 2,
    },
    "complete_all_listening_sections": {
        "name": "Listening Champion",
        "description": "Complete all 4 listening sections",
        "icon": "🎧",
        "category": "skill",
        "tier": 2,
    },
    "vocabulary_100": {
        "name": "Vocabulary Builder",
        "description": "Save 100 words to your vocabulary deck",
        "icon": "📖",
        "category": "vocabulary",
        "tier": 2,
    },
    "vocabulary_master_50": {
        "name": "Word Master",
        "description": "Master 50 vocabulary words",
        "icon": "🎓",
        "category": "vocabulary",
        "tier": 3,
    },
    
    # Special Achievements
    "perfect_score": {
        "name": "Perfect Score",
        "description": "Get 100% on any practice session",
        "icon": "💯",
        "category": "special",
        "tier": 2,
    },
    "error_dna_improvement": {
        "name": "Error Crusher",
        "description": "Improve on an identified weak pattern",
        "icon": "💪",
        "category": "special",
        "tier": 2,
    },
    "shadowing_tier_3": {
        "name": "Shadowing Master",
        "description": "Pass Shadowing Tier 3 (Band 8.5)",
        "icon": "🎭",
        "category": "special",
        "tier": 3,
    },
    "dictation_90_accuracy": {
        "name": "Dictation Pro",
        "description": "Achieve 90%+ accuracy in dictation",
        "icon": "✅",
        "category": "special",
        "tier": 2,
    },
}


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────

class AchievementUnlock(BaseModel):
    """An unlocked achievement."""
    achievement_id: str
    name: str
    description: str
    icon: str
    category: str
    tier: int
    unlocked_at: datetime
    progress: float = 1.0


class AchievementProgress(BaseModel):
    """Progress toward an achievement."""
    achievement_id: str
    name: str
    description: str
    icon: str
    category: str
    tier: int
    progress: float  # 0.0 to 1.0
    current_value: int
    target_value: int
    is_unlocked: bool = False


class AchievementSummary(BaseModel):
    """User's achievement summary."""
    total_unlocked: int
    total_available: int
    by_category: dict[str, int]
    by_tier: dict[int, int]
    recent_unlocks: list[AchievementUnlock]
    in_progress: list[AchievementProgress]


# ─────────────────────────────────────────────
#  Achievement Checking Functions
# ─────────────────────────────────────────────

async def check_and_unlock_achievements(
    user_id: int,
    db: AsyncSession,
    trigger_event: Optional[str] = None,
) -> list[AchievementUnlock]:
    """
    Check all achievement criteria and return newly unlocked achievements.
    
    Args:
        user_id: User ID
        db: Database session
        trigger_event: Optional event that triggered this check (e.g., "session_complete")
    
    Returns:
        List of newly unlocked achievements
    """
    newly_unlocked = []
    
    # Get user's existing achievements
    from shared.models import UserAchievement
    
    existing = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user_id)
    )
    existing_achievements = {a.achievement_id for a in existing.scalars().all()}
    
    # Check each achievement
    for achievement_id, achievement in ACHIEVEMENTS.items():
        if achievement_id in existing_achievements:
            continue
        
        # Check criteria
        if await check_achievement_criteria(user_id, db, achievement_id, trigger_event):
            # Unlock achievement
            unlock = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                unlocked_at=datetime.utcnow(),
            )
            db.add(unlock)
            
            newly_unlocked.append(AchievementUnlock(
                achievement_id=achievement_id,
                name=achievement["name"],
                description=achievement["description"],
                icon=achievement["icon"],
                category=achievement["category"],
                tier=achievement["tier"],
                unlocked_at=datetime.utcnow(),
            ))
    
    if newly_unlocked:
        await db.commit()
    
    return newly_unlocked


async def check_achievement_criteria(
    user_id: int,
    db: AsyncSession,
    achievement_id: str,
    trigger_event: Optional[str] = None,
) -> bool:
    """Check if user meets criteria for a specific achievement."""
    
    # Session count achievements
    if achievement_id == "first_practice":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return count >= 1
    
    if achievement_id == "ten_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return count >= 10
    
    if achievement_id == "fifty_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return count >= 50
    
    if achievement_id == "hundred_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return count >= 100
    
    # Band score achievements
    if achievement_id == "band_six":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.band_estimate >= 6.0)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    if achievement_id == "band_seven":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.band_estimate >= 7.0)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    if achievement_id == "band_seven_five":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.band_estimate >= 7.5)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    if achievement_id == "band_eight":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.band_estimate >= 8.0)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    # Streak achievements
    if achievement_id.startswith("streak_"):
        days = int(achievement_id.split("_")[1])
        current_streak = await calculate_streak(user_id, db)
        return current_streak >= days
    
    # Skill-specific achievements
    if achievement_id == "first_band_7_writing":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.skill == "writing")
            .where(SessionModel.band_estimate >= 7.0)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    if achievement_id == "first_band_7_speaking":
        result = await db.execute(
            select(SessionModel.band_estimate)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.skill == "speaking")
            .where(SessionModel.band_estimate >= 7.0)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    # Perfect score
    if achievement_id == "perfect_score":
        result = await db.execute(
            select(SessionModel.score)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.score == 100)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    # Default: not implemented
    return False


async def calculate_streak(user_id: int, db: AsyncSession) -> int:
    """Calculate current practice streak."""
    result = await db.execute(
        select(SessionModel.started_at)
        .where(SessionModel.user_id == user_id)
        .order_by(SessionModel.started_at.desc())
        .limit(30)
    )
    sessions = result.scalars().all()
    
    if not sessions:
        return 0
    
    streak = 0
    today = date.today()
    session_dates = set(s.date() for s in sessions)
    
    check_date = today
    while check_date in session_dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak


async def get_achievement_summary(
    user_id: int,
    db: AsyncSession,
) -> AchievementSummary:
    """Get user's achievement summary."""
    from shared.models import UserAchievement
    
    # Get unlocked achievements
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.unlocked_at.desc())
    )
    unlocked = result.scalars().all()
    
    unlocked_set = {u.achievement_id for u in unlocked}
    
    # Build summary
    recent_unlocks = [
        AchievementUnlock(
            achievement_id=u.achievement_id,
            name=ACHIEVEMENTS[u.achievement_id]["name"],
            description=ACHIEVEMENTS[u.achievement_id]["description"],
            icon=ACHIEVEMENTS[u.achievement_id]["icon"],
            category=ACHIEVEMENTS[u.achievement_id]["category"],
            tier=ACHIEVEMENTS[u.achievement_id]["tier"],
            unlocked_at=u.unlocked_at,
        )
        for u in unlocked[:5]
        if u.achievement_id in ACHIEVEMENTS
    ]
    
    # Calculate progress for locked achievements
    in_progress = []
    for achievement_id, achievement in ACHIEVEMENTS.items():
        if achievement_id in unlocked_set:
            continue
        
        # Calculate progress (simplified - would need specific logic per achievement)
        progress = await calculate_achievement_progress(user_id, db, achievement_id)
        
        if progress > 0:
            in_progress.append(AchievementProgress(
                achievement_id=achievement_id,
                name=achievement["name"],
                description=achievement["description"],
                icon=achievement["icon"],
                category=achievement["category"],
                tier=achievement["tier"],
                progress=progress,
                current_value=int(progress * 10),
                target_value=10,
            ))
    
    # Sort by progress
    in_progress.sort(key=lambda x: -x.progress)
    
    # Count by category and tier
    by_category: dict[str, int] = {}
    by_tier: dict[int, int] = {}
    
    for u in unlocked:
        if u.achievement_id in ACHIEVEMENTS:
            cat = ACHIEVEMENTS[u.achievement_id]["category"]
            tier = ACHIEVEMENTS[u.achievement_id]["tier"]
            by_category[cat] = by_category.get(cat, 0) + 1
            by_tier[tier] = by_tier.get(tier, 0) + 1
    
    return AchievementSummary(
        total_unlocked=len(unlocked),
        total_available=len(ACHIEVEMENTS),
        by_category=by_category,
        by_tier=by_tier,
        recent_unlocks=recent_unlocks,
        in_progress=in_progress[:5],
    )


async def calculate_achievement_progress(
    user_id: int,
    db: AsyncSession,
    achievement_id: str,
) -> float:
    """Calculate progress toward an achievement (0.0 to 1.0)."""
    
    if achievement_id == "ten_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return min(count / 10, 1.0)
    
    if achievement_id == "fifty_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return min(count / 50, 1.0)
    
    if achievement_id == "hundred_sessions":
        count = await db.scalar(
            select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id)
        ) or 0
        return min(count / 100, 1.0)
    
    if achievement_id.startswith("streak_"):
        days = int(achievement_id.split("_")[1])
        streak = await calculate_streak(user_id, db)
        return min(streak / days, 1.0)
    
    return 0.0
