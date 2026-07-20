from datetime import datetime
from typing import List, Optional
from .models import TelemetrySummary, AttentionScore
from .schemas import TelemetryReportResponse, AttentionScoreData, TelemetryProfileResponse

def build_report_response(session, summaries: List[TelemetrySummary], attention: Optional[AttentionScore]) -> TelemetryReportResponse:
    total_fixations = sum(s.fixation_count for s in summaries)
    total_regressions = sum(s.regression_count for s in summaries)
    avg_focus = sum(s.focus_score for s in summaries) / len(summaries) if summaries else 0
    avg_fixation_ms = sum(s.avg_fixation_ms for s in summaries) / len(summaries) if summaries else 0
    avg_speed = sum(s.reading_speed_wpm for s in summaries) / len(summaries) if summaries else 0
    avg_blink = sum(s.blink_rate for s in summaries) / len(summaries) if summaries else 0
    avg_skip = sum(s.skip_rate for s in summaries) / len(summaries) if summaries else 0

    merged_para_time: dict = {}
    for s in summaries:
        if s.paragraph_time:
            for para_id, time_ms in s.paragraph_time.items():
                merged_para_time[para_id] = merged_para_time.get(para_id, 0) + time_ms

    duration_ms = None
    if session.ended_at and session.started_at:
        duration_ms = int((session.ended_at - session.started_at).total_seconds() * 1000)

    attention_data = None
    if attention:
        attention_data = AttentionScoreData(
            overall=attention.overall_attention,
            scanning_efficiency=attention.scanning_efficiency,
            regression_severity=attention.regression_severity,
            time_management=attention.time_management,
            focus_stability=attention.focus_stability,
        )

    return TelemetryReportResponse(
        session_id=session.id,
        skill=session.skill,
        duration_ms=duration_ms,
        total_fixations=total_fixations,
        total_regressions=total_regressions,
        avg_focus_score=round(avg_focus, 1),
        avg_fixation_ms=round(avg_fixation_ms, 1),
        avg_reading_speed_wpm=round(avg_speed, 1),
        avg_blink_rate=round(avg_blink, 1),
        avg_skip_rate=round(avg_skip, 3),
        paragraph_time=merged_para_time,
        attention_score=attention_data,
    )

def build_profile_response(user_id: int, num_sessions: int, summaries: List[TelemetrySummary]) -> TelemetryProfileResponse:
    if not summaries:
        return TelemetryProfileResponse(
            user_id=user_id,
            total_sessions=num_sessions,
            avg_focus_score=0,
            avg_reading_speed_wpm=0,
            avg_regression_rate=0,
            strengths=[],
            weaknesses=[],
        )

    avg_focus = sum(s.focus_score for s in summaries) / len(summaries)
    avg_speed = sum(s.reading_speed_wpm for s in summaries) / len(summaries)
    total_fix = sum(s.fixation_count for s in summaries)
    total_reg = sum(s.regression_count for s in summaries)
    reg_rate = total_reg / total_fix if total_fix > 0 else 0

    strengths = []
    weaknesses = []

    if avg_focus >= 75:
        strengths.append("Sustained attention")
    elif avg_focus < 50:
        weaknesses.append("Focus drops during reading")

    if avg_speed >= 200:
        strengths.append("Fast reading speed")
    elif avg_speed < 120:
        weaknesses.append("Slow reading speed")

    if reg_rate < 0.1:
        strengths.append("Low regression rate")
    elif reg_rate > 0.25:
        weaknesses.append("High regression rate (comprehension difficulty)")

    return TelemetryProfileResponse(
        user_id=user_id,
        total_sessions=num_sessions,
        avg_focus_score=round(avg_focus, 1),
        avg_reading_speed_wpm=round(avg_speed, 1),
        avg_regression_rate=round(reg_rate, 3),
        strengths=strengths,
        weaknesses=weaknesses,
    )
