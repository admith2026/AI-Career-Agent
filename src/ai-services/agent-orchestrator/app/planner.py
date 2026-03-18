"""LLM-powered Career Agent Planner — breaks natural language goals into executable agent tasks.

Uses OpenAI to reason about user goals and generate a structured plan
that the executor can run autonomously.
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

AGENT_CAPABILITIES = """Available agent types and task types:
- discovery / scan_jobs: Discover new job listings from all sources
- matching / score_jobs: AI-score unscored jobs against user profile
- application / auto_apply: Auto-apply to high-scoring jobs (score >= 75)
- outreach / send_outreach: Send LinkedIn outreach to recruiters at target companies
- follow_up / schedule_follow_ups: Follow up on stale applications (>7 days)
- interview / prep: Generate interview preparation materials (needs job_title, company_name)
- negotiation / analyze: Analyze a job offer and create negotiation strategy (needs job_title, offered_rate)
"""

PLANNER_PROMPT = """You are an AI Career Agent planner. Given a user's career goal, create an execution plan.

{capabilities}

## User Goal
{goal}

## Instructions
Return ONLY valid JSON with this exact structure:
{{
  "plan_name": "Short descriptive name",
  "reasoning": "1-2 sentences explaining your approach",
  "steps": [
    {{
      "agent_type": "one of the agent types above",
      "task_type": "one of the task types above",
      "priority": 1-10 (1=highest),
      "config": {{}} // optional input data for the task
    }}
  ]
}}

Keep plans focused — 2-6 steps. Order matters: earlier steps run first.
Only use agent types and task types from the list above."""


async def create_plan(goal: str) -> dict[str, Any]:
    """Use LLM to create an execution plan from a natural language goal."""
    settings = BaseServiceSettings()

    if not settings.openai_api_key:
        return _fallback_plan(goal)

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": PLANNER_PROMPT.format(
                    capabilities=AGENT_CAPABILITIES,
                    goal=goal[:1000],
                ),
            }],
            temperature=0.3,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        plan = json.loads(content)

        # Validate structure
        if "steps" not in plan or not isinstance(plan["steps"], list):
            return _fallback_plan(goal)

        valid_agents = {"discovery", "matching", "application", "outreach", "follow_up", "interview", "negotiation"}
        plan["steps"] = [s for s in plan["steps"] if s.get("agent_type") in valid_agents]

        if not plan["steps"]:
            return _fallback_plan(goal)

        logger.info("AI planner created plan '%s' with %d steps", plan.get("plan_name"), len(plan["steps"]))
        return plan

    except json.JSONDecodeError:
        logger.warning("Planner returned invalid JSON, using fallback")
        return _fallback_plan(goal)
    except Exception:
        logger.exception("Planner failed")
        return _fallback_plan(goal)


def _fallback_plan(goal: str) -> dict[str, Any]:
    """Create a sensible default plan when LLM is unavailable."""
    goal_lower = goal.lower()

    if "interview" in goal_lower:
        return {
            "plan_name": "Interview Preparation",
            "reasoning": "Preparing for interviews by generating prep materials",
            "steps": [
                {"agent_type": "interview", "task_type": "prep", "priority": 1, "config": {}},
            ],
        }
    if "negotiate" in goal_lower or "offer" in goal_lower or "salary" in goal_lower:
        return {
            "plan_name": "Offer Negotiation",
            "reasoning": "Analyzing offer and creating negotiation strategy",
            "steps": [
                {"agent_type": "negotiation", "task_type": "analyze", "priority": 1, "config": {}},
            ],
        }
    if "apply" in goal_lower:
        return {
            "plan_name": "Smart Apply",
            "reasoning": "Score jobs then auto-apply to best matches",
            "steps": [
                {"agent_type": "matching", "task_type": "score_jobs", "priority": 1, "config": {}},
                {"agent_type": "application", "task_type": "auto_apply", "priority": 2, "config": {}},
            ],
        }

    # Default: full pipeline
    return {
        "plan_name": "Full Career Pipeline",
        "reasoning": "Running the complete autonomous career pipeline",
        "steps": [
            {"agent_type": "discovery", "task_type": "scan_jobs", "priority": 1, "config": {}},
            {"agent_type": "matching", "task_type": "score_jobs", "priority": 2, "config": {}},
            {"agent_type": "application", "task_type": "auto_apply", "priority": 3, "config": {}},
            {"agent_type": "outreach", "task_type": "send_outreach", "priority": 4, "config": {}},
            {"agent_type": "follow_up", "task_type": "schedule_follow_ups", "priority": 5, "config": {}},
        ],
    }
