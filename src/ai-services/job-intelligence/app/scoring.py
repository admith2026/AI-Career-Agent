"""Dynamic job scoring — works with ALL technical roles, not just .NET."""

import re
from app.models import ScoreBreakdown


# High-value technology keywords by category
TECH_CATEGORIES = {
    "backend": [
        r"\.net\s*(core|8|7|6)", r"asp\.net\s*core", r"\bdjango\b", r"\bflask\b",
        r"\bfastapi\b", r"\bspring\s*boot\b", r"\bnode\.?js\b", r"\bexpress\.?js\b",
        r"\brails\b", r"\blaravel\b", r"\bnestjs\b", r"\bgin\b", r"\bfiber\b",
    ],
    "frontend": [
        r"\breact\b", r"\bangular\b", r"\bvue\.?js\b", r"\bnext\.?js\b",
        r"\bsvelte\b", r"\bblazor\b", r"\btailwind\b",
    ],
    "cloud": [
        r"\bazure\b", r"\baws\b", r"\bgcp\b", r"\bgoogle\s*cloud\b",
    ],
    "devops": [
        r"\bdocker\b", r"\bkubernetes\b", r"\bk8s\b", r"\bterraform\b",
        r"\bjenkins\b", r"\bgithub\s*actions\b", r"\bci/?cd\b",
    ],
    "data": [
        r"\bspark\b", r"\bkafka\b", r"\bairflow\b", r"\bsnowflake\b",
        r"\bbigquery\b", r"\bdatabricks\b",
    ],
    "ai_ml": [
        r"\btensorflow\b", r"\bpytorch\b", r"\bmachine\s*learning\b",
        r"\bdeep\s*learning\b", r"\bnlp\b", r"\bllm\b", r"\blangchain\b",
    ],
    "languages": [
        r"\bc#\b|\bcsharp\b", r"\bjava\b(?!script)", r"\bpython\b",
        r"\bgolang\b|\bgo\b(?:\s+developer|\s+engineer)", r"\brust\b",
        r"\btypescript\b", r"\bkotlin\b", r"\bswift\b",
    ],
}


def calculate_match_score(
    job_title: str,
    job_description: str | None,
    technologies: list[str],
    is_remote: bool,
    is_contract: bool,
) -> tuple[int, ScoreBreakdown]:
    """Calculate a relevance score (0-100) based on job attributes.

    Dynamic scoring: awards points for remote, contract, tech stack breadth,
    rather than hardcoded .NET-only matching.
    """
    breakdown = ScoreBreakdown()
    text = f"{job_title} {job_description or ''}".lower()

    # Remote = +25
    if is_remote or _matches(text, r"\bremote\b"):
        breakdown.remote = 25

    # Contract / Freelance = +25
    if is_contract or _matches(text, r"\bcontract\b|\bfreelance\b|\bc2c\b|\bcorp.to.corp\b"):
        breakdown.contract = 25

    # Technology stack breadth = up to +30
    tech_score = 0
    matched_categories = set()
    for category, patterns in TECH_CATEGORIES.items():
        for pattern in patterns:
            if _matches(text, pattern):
                matched_categories.add(category)
                break
    tech_score = min(30, len(matched_categories) * 8)
    breakdown.tech_stack = tech_score

    # Skill match (number of technologies detected) = up to +10
    skill_score = min(10, len(technologies) * 2)
    breakdown.skill_match = skill_score

    # Bonus for microservices, API design, etc.
    bonus = 0
    if _matches(text, r"\bmicroservice"):
        bonus += 5
    if _matches(text, r"\brest\s*api\b|\bgraphql\b|\bgrpc\b"):
        bonus += 5
    breakdown.bonus = min(10, bonus)

    total = min(
        100,
        breakdown.remote
        + breakdown.contract
        + breakdown.tech_stack
        + breakdown.skill_match
        + breakdown.bonus,
    )

    return total, breakdown


def _matches(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE))
