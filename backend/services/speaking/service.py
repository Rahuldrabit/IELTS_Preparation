import re
from typing import List
from .schemas import ShadowingModelRequest, ShadowingModelResponse, TierAudioConfig, SegmentMeta

def split_into_segments(text: str, max_words: int = 8) -> List[SegmentMeta]:
    words = text.split()
    segments = []
    segment_id = 0
    
    raw_segments = re.split(r'(?<=[.!?,;:])\s+', text)
    
    for raw_seg in raw_segments:
        seg_words = raw_seg.split()
        word_count = len(seg_words)
        if word_count == 0:
            continue
            
        duration_estimate = int(word_count * 150 / 0.9)
        pause_after = 200 if raw_seg.rstrip().endswith(('.', '!', '?')) else 100
        
        segments.append(SegmentMeta(
            segment_id=segment_id,
            text=raw_seg.strip(),
            word_count=word_count,
            duration_estimate_ms=duration_estimate,
            pause_after_ms=pause_after,
        ))
        segment_id += 1
    
    return segments

def generate_fallback_tiers(transcript: str):
    from services.agents.speaking import MutationGenerationResponse, MutationTier
    
    return MutationGenerationResponse(
        original_transcript=transcript,
        identified_fillers=["um", "uh"],
        tiers=[
            MutationTier(
                tier=1,
                band_label="Band 6.5 — Core",
                target_band=6.5,
                text=transcript.replace("quite", "rather").replace("think", "believe"),
                key_changes=[
                    "Upgraded vocabulary from 'think' to 'believe'",
                    "Replaced 'quite' with 'rather' for more academic tone",
                    "Removed filler words",
                ],
                audio_hints="Focus on clear word stress and steady pacing.",
            ),
            MutationTier(
                tier=2,
                band_label="Band 7.5 — Advanced",
                target_band=7.5,
                text=f"From my perspective, {transcript.lower()} Furthermore, this is an issue of considerable significance.",
                key_changes=[
                    "Added discourse marker 'From my perspective'",
                    "Restructured with formal opening",
                    "Added cohesive device 'Furthermore'",
                ],
                audio_hints="Use rising intonation for the opening phrase, then steady pacing.",
            ),
            MutationTier(
                tier=3,
                band_label="Band 8.5 — Mastery",
                target_band=8.5,
                text=f"The significance of this matter cannot be overstated. {transcript.replace('I think', 'It is my considered view that').replace('I believe', 'I am of the firm conviction that')}",
                key_changes=[
                    "Used nominalization 'The significance of'",
                    "Introduced sophisticated hedging 'It is my considered view'",
                    "Elevated register throughout",
                ],
                audio_hints="Emphasize key content words, use connected speech for natural flow.",
            ),
        ],
    )

async def build_shadowing_model(request: ShadowingModelRequest) -> ShadowingModelResponse:
    from services.agents.speaking import SpeakingAgent, MutationGenerationRequest
    
    base_responses = {
        1: f"Well, I think {request.topic} is quite interesting. I've been interested in it for a while now.",
        2: f"I'd like to talk about {request.topic}. It's something I've been thinking about quite a lot lately. "
           f"There are several reasons why I find this topic fascinating. "
           f"First of all, it's very relevant to my daily life. "
           f"Secondly, I believe it's an important issue that affects many people. "
           f"And finally, I think understanding {request.topic} can help us make better decisions.",
        3: f"I believe {request.topic} is a complex issue that requires careful consideration from multiple perspectives.",
    }
    
    base_transcript = base_responses.get(request.part, base_responses[2])
    
    mutation_request = MutationGenerationRequest(
        transcript=base_transcript,
        original_band=6.0,
    )
    
    try:
        agent = SpeakingAgent()
        mutation_result = await agent.generate_mutations(mutation_request)
    except Exception:
        mutation_result = generate_fallback_tiers(base_transcript)
    
    lang_map = {
        "british": "en-GB",
        "american": "en-US",
        "australian": "en-AU",
    }
    
    tiers_config = []
    for tier in mutation_result.tiers:
        segments = split_into_segments(tier.text)
        
        tiers_config.append(TierAudioConfig(
            tier=tier.tier,
            band_label=tier.band_label,
            target_band=tier.target_band,
            text=tier.text,
            key_changes=tier.key_changes,
            audio_hints=tier.audio_hints,
            segments=segments,
            tts_config={
                "lang": lang_map.get(request.accent, "en-GB"),
                "rate": request.speed,
                "pitch": 1.0,
            },
        ))
    
    return ShadowingModelResponse(
        topic=request.topic,
        part=request.part,
        session_id=f"shadow-{request.part}-{hash(request.topic) % 10000}",
        mutation_tiers=tiers_config,
        current_tier=1,
        pass_criteria={
            "phoneme_threshold": 0.75,
            "rhythm_threshold": 0.70,
        },
    )
