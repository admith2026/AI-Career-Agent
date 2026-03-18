"""AI-powered job matching using OpenAI gpt-4o-mini.

Supports dynamic user profiles — loads from DB or accepts profile string.
Works with ALL technical roles (not just .NET).
"""

import json
import logging
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

# Default fallback profile (generic, not role-specific)
DEFAULT_PROFILE = (
    "Software Developer | 5+ years experience | "
    "Open to any technology stack | Remote roles in the USA"
)

SCORING_PROMPT = """You are a job-matching AI. Score how well this job matches the candidate profile.

## Candidate Profile
{profile}

## Job Posting
Title: {title}
Company: {company}
Description:
{description}

## Instructions
Return ONLY valid JSON with exactly these fields:
- "score": integer 0-100 (100 = perfect match)
- "explanation": string (2-3 sentences explaining the score)
- "matched_skills": array of skills from the profile that match this job
- "missing_skills": array of important job skills the candidate lacks
- "match_reasons": array of short strings explaining why this is/isn't a match

Consider: skill overlap, seniority fit, remote/contract alignment, technology stack match."""


@dataclass
class MatchResult:
    score: int
    explanation: str
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    match_reasons: list[str] = field(default_factory=list)


async def score_job(
    title: str,
    company: str,
    description: str,
    profile: str = DEFAULT_PROFILE,
) -> MatchResult:
    """Score a single job against a user profile using gpt-4o-mini.

    The profile parameter should be dynamically built from the user's DB profile
    using skill_engine.build_dynamic_profile(). Falls back to DEFAULT_PROFILE.
    """
    settings = BaseServiceSettings()

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not configured — returning default score")
        return MatchResult(score=50, explanation="AI scoring unavailable (no API key)")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = SCORING_PROMPT.format(
        profile=profile,
        title=title,
        company=company,
        description=description[:2500],
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        result = json.loads(content)
        score = max(0, min(100, int(result.get("score", 0))))
        explanation = str(result.get("explanation", "No explanation provided"))

        logger.info("Scored '%s' at %s/100", title[:60], score)
        return MatchResult(
            score=score,
            explanation=explanation,
            matched_skills=result.get("matched_skills", []),
            missing_skills=result.get("missing_skills", []),
            match_reasons=result.get("match_reasons", []),
        )

    except json.JSONDecodeError:
        logger.error("Failed to parse OpenAI response as JSON for '%s'", title[:60])
        return MatchResult(score=0, explanation="AI scoring failed — invalid response format")
    except Exception:
        logger.exception("OpenAI scoring failed for '%s'", title[:60])
        return MatchResult(score=0, explanation="AI scoring failed — API error")


async def score_job_for_user(
    title: str,
    company: str,
    description: str,
    user_profile_data: dict,
) -> MatchResult:
    """Score a job using a user's profile data from the database.

    user_profile_data should contain keys matching UserProfile columns:
    headline, skills, experience_years, preferred_technologies, etc.
    """
    from shared.services.skill_engine import build_dynamic_profile

    profile_str = build_dynamic_profile(
        headline=user_profile_data.get("headline"),
        skills=user_profile_data.get("skills", []),
        experience_years=user_profile_data.get("experience_years", 0),
        preferred_technologies=user_profile_data.get("preferred_technologies", []),
        preferred_contract_types=user_profile_data.get("preferred_contract_types", []),
        summary=user_profile_data.get("summary"),
    )
    return await score_job(title, company, description, profile=profile_str)
