from pydantic import BaseModel
from services.agents.base import BaseAgent
from services.agents.registry import registry

class MutationTier(BaseModel):
    tier: int                   # 1, 2, or 3
    band_label: str             # "Band 6.5 — Core", etc.
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


@registry.register
class SpeakingAgent(BaseAgent):
    name = "SpeakingAgent"
    description = "Provides mutation and feedback generation for IELTS speaking."

    async def generate_mutations(self, request: MutationGenerationRequest) -> MutationGenerationResponse:
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

TIER 1 (Band 6.5 — Core):
- Replace simple words with accurate academic equivalents only
- Keep sentence structure mostly unchanged
- Remove filled pauses ("um", "uh", "like", "you know")
- List exactly 3 key changes made

TIER 2 (Band 7.5 — Advanced):
- Restructure sentences using subordinate clauses, parallel structures, relative clauses
- Add discourse markers and cohesive devices ("Furthermore", "In contrast", etc.)
- Expand vocabulary to idiomatic academic range
- List exactly 3 key changes made

TIER 3 (Band 8.5 — Mastery):
- Introduce nominalization patterns (e.g. "the rapid deterioration of" instead of "things got worse quickly")
- Use inverted conditionals where appropriate ("Were this to continue…")
- Add idiomatic phrasing and sophisticated hedging language ("It could be argued that…")
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
      "band_label": "Band 6.5 — Core",
      "target_band": 6.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }},
    {{
      "tier": 2,
      "band_label": "Band 7.5 — Advanced",
      "target_band": 7.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }},
    {{
      "tier": 3,
      "band_label": "Band 8.5 — Mastery",
      "target_band": 8.5,
      "text": "...",
      "key_changes": ["change1", "change2", "change3"],
      "audio_hints": "..."
    }}
  ]
}}"""
        result = await self.run_structured(
            prompt=prompt,
            schema=MutationGenerationResponse,
            temperature=0.4,
        )
        # Enforce exactly 3 tiers even if model returns fewer
        if len(result.tiers) != 3:
            raise ValueError(f"Expected 3 tiers, got {len(result.tiers)}")
        return result
