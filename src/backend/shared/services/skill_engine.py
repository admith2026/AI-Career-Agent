"""Dynamic Skill Engine — AI-powered skill extraction, matching, and profile building.

Supports ALL technical roles: Java, Python, AI/ML, DevOps, Cloud, Frontend, Backend,
Data Engineering, Mobile, Security, QA, and more.
"""

import json
import logging
from dataclasses import dataclass, field

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

# ─── Comprehensive Skill Taxonomy ────────────────────────────────────────────

SKILL_CATEGORIES = {
    "languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart", "Elixir", "Lua",
        "Perl", "Haskell", "Clojure", "Julia", "MATLAB", "Objective-C", "Shell",
    ],
    "frontend": [
        "React", "Angular", "Vue.js", "Next.js", "Svelte", "HTML5", "CSS3",
        "Tailwind CSS", "Bootstrap", "SASS/SCSS", "Redux", "Zustand", "MobX",
        "WebPack", "Vite", "Storybook", "Three.js", "D3.js", "jQuery",
    ],
    "backend": [
        "Node.js", "Express.js", "FastAPI", "Django", "Flask", "Spring Boot",
        "ASP.NET Core", ".NET Core", "Rails", "Laravel", "NestJS", "Gin",
        "Fiber", "Phoenix", "Actix", "gRPC", "GraphQL", "REST API",
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "Neo4j", "InfluxDB", "CockroachDB",
        "SQL Server", "Oracle", "SQLite", "Supabase", "Firebase",
    ],
    "cloud_devops": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI",
        "ArgoCD", "Helm", "Istio", "Prometheus", "Grafana", "Datadog",
        "CloudFormation", "Pulumi", "Vagrant",
    ],
    "ai_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "Hugging Face",
        "LangChain", "OpenAI API", "LLM", "NLP", "Computer Vision",
        "Deep Learning", "Machine Learning", "MLOps", "MLflow", "Kubeflow",
        "Pandas", "NumPy", "Spark MLlib", "ONNX", "RAG",
    ],
    "data_engineering": [
        "Apache Spark", "Apache Kafka", "Apache Airflow", "dbt",
        "Snowflake", "BigQuery", "Redshift", "Databricks", "Flink",
        "Hadoop", "Hive", "Presto", "ETL", "Data Pipeline", "Data Lake",
    ],
    "mobile": [
        "React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android",
        "Xamarin", "Ionic", "Expo", "SwiftUI", "Jetpack Compose",
    ],
    "security": [
        "OAuth2", "JWT", "OWASP", "Penetration Testing", "SIEM",
        "SOC", "Zero Trust", "Encryption", "IAM", "RBAC", "SAML",
    ],
    "tools": [
        "Git", "Jira", "Confluence", "Slack", "VS Code", "IntelliJ",
        "Postman", "Figma", "Linux", "Nginx", "Apache",
    ],
}

# Flatten all known skills for quick lookup
ALL_KNOWN_SKILLS = set()
for category_skills in SKILL_CATEGORIES.values():
    ALL_KNOWN_SKILLS.update(s.lower() for s in category_skills)

# ─── Role Templates ──────────────────────────────────────────────────────────

ROLE_TEMPLATES = {
    "fullstack_dotnet": {
        "label": ".NET Full Stack Developer",
        "search_queries": [
            ".net full stack developer remote USA",
            "C# ASP.NET Core developer remote contract",
            "Blazor developer remote USA",
        ],
        "core_skills": ["C#", ".NET Core", "ASP.NET Core", "Azure", "SQL Server", "React", "TypeScript"],
    },
    "fullstack_java": {
        "label": "Java Full Stack Developer",
        "search_queries": [
            "java full stack developer remote USA",
            "Spring Boot developer remote contract",
            "java microservices developer USA",
        ],
        "core_skills": ["Java", "Spring Boot", "React", "TypeScript", "PostgreSQL", "AWS", "Docker"],
    },
    "python_backend": {
        "label": "Python Backend Developer",
        "search_queries": [
            "python backend developer remote USA",
            "python FastAPI developer remote contract",
            "Django developer remote USA",
        ],
        "core_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "AWS"],
    },
    "frontend_react": {
        "label": "React Frontend Developer",
        "search_queries": [
            "react developer remote USA",
            "frontend engineer react typescript remote",
            "Next.js developer remote contract USA",
        ],
        "core_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "Redux", "HTML5", "CSS3"],
    },
    "ai_ml_engineer": {
        "label": "AI/ML Engineer",
        "search_queries": [
            "machine learning engineer remote USA",
            "AI engineer python remote contract",
            "NLP engineer remote USA",
            "LLM engineer remote USA",
        ],
        "core_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP", "AWS"],
    },
    "data_engineer": {
        "label": "Data Engineer",
        "search_queries": [
            "data engineer remote USA",
            "data pipeline engineer remote contract",
            "Spark data engineer USA",
        ],
        "core_skills": ["Python", "Apache Spark", "Apache Kafka", "SQL", "Airflow", "Snowflake", "AWS"],
    },
    "devops_cloud": {
        "label": "DevOps / Cloud Engineer",
        "search_queries": [
            "devops engineer remote USA",
            "cloud engineer AWS remote contract",
            "kubernetes engineer remote USA",
            "SRE site reliability engineer remote",
        ],
        "core_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins", "Linux", "Python"],
    },
    "mobile_developer": {
        "label": "Mobile Developer",
        "search_queries": [
            "react native developer remote USA",
            "iOS developer remote contract USA",
            "android developer remote USA",
            "flutter developer remote USA",
        ],
        "core_skills": ["React Native", "Flutter", "Swift", "Kotlin", "TypeScript", "iOS", "Android"],
    },
    "security_engineer": {
        "label": "Security Engineer",
        "search_queries": [
            "security engineer remote USA",
            "cybersecurity analyst remote contract",
            "penetration tester remote USA",
        ],
        "core_skills": ["OWASP", "Penetration Testing", "AWS", "Linux", "Python", "SIEM", "IAM"],
    },
    "golang_developer": {
        "label": "Go Developer",
        "search_queries": [
            "golang developer remote USA",
            "go backend developer remote contract",
            "go microservices developer USA",
        ],
        "core_skills": ["Go", "Docker", "Kubernetes", "gRPC", "PostgreSQL", "Redis", "AWS"],
    },
}

# ─── Skill Extraction Prompt ─────────────────────────────────────────────────

SKILL_EXTRACTION_PROMPT = """You are a technical skill extraction AI. Analyze the job description and extract structured data.

## Job Posting
Title: {title}
Company: {company}
Description:
{description}

## Instructions
Return ONLY valid JSON with these fields:
- "skills": array of specific technical skills mentioned (e.g., "Python", "React", "AWS")
- "role_category": one of: fullstack_dotnet, fullstack_java, python_backend, frontend_react, ai_ml_engineer, data_engineer, devops_cloud, mobile_developer, security_engineer, golang_developer, other
- "seniority": one of: junior, mid, senior, lead, principal, staff
- "experience_years_min": integer or null
- "experience_years_max": integer or null
- "is_remote": boolean
- "is_contract": boolean
- "visa_sponsorship": boolean or null (null if not mentioned)
- "key_requirements": array of top 5 most important requirements as short phrases"""


@dataclass
class SkillExtractionResult:
    skills: list[str] = field(default_factory=list)
    role_category: str = "other"
    seniority: str = "mid"
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    is_remote: bool = True
    is_contract: bool = False
    visa_sponsorship: bool | None = None
    key_requirements: list[str] = field(default_factory=list)


async def extract_skills_from_job(
    title: str,
    company: str,
    description: str,
) -> SkillExtractionResult:
    """Extract skills and metadata from a job description using AI."""
    settings = BaseServiceSettings()

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not configured — using regex fallback")
        return _regex_skill_extraction(title, description)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = SKILL_EXTRACTION_PROMPT.format(
        title=title,
        company=company,
        description=description[:3000],
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(content)
        return SkillExtractionResult(
            skills=data.get("skills", []),
            role_category=data.get("role_category", "other"),
            seniority=data.get("seniority", "mid"),
            experience_years_min=data.get("experience_years_min"),
            experience_years_max=data.get("experience_years_max"),
            is_remote=data.get("is_remote", True),
            is_contract=data.get("is_contract", False),
            visa_sponsorship=data.get("visa_sponsorship"),
            key_requirements=data.get("key_requirements", []),
        )
    except (json.JSONDecodeError, Exception):
        logger.exception("AI skill extraction failed — using regex fallback")
        return _regex_skill_extraction(title, description)


def _regex_skill_extraction(title: str, description: str) -> SkillExtractionResult:
    """Fallback: extract skills using keyword matching against the taxonomy."""
    text = f"{title} {description}".lower()
    found_skills = []

    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in text:
                found_skills.append(skill)

    return SkillExtractionResult(
        skills=list(set(found_skills)),
        role_category=_guess_role_category(title, found_skills),
        seniority=_guess_seniority(title, description),
    )


def _guess_role_category(title: str, skills: list[str]) -> str:
    """Guess role category from title and skills."""
    title_lower = title.lower()
    skill_set = {s.lower() for s in skills}

    if any(k in title_lower for k in ["devops", "sre", "reliability", "infrastructure"]):
        return "devops_cloud"
    if any(k in title_lower for k in ["machine learning", "ai engineer", "ml engineer", "nlp", "llm"]):
        return "ai_ml_engineer"
    if any(k in title_lower for k in ["data engineer", "data pipeline", "etl"]):
        return "data_engineer"
    if any(k in title_lower for k in ["security", "cybersecurity", "pentest"]):
        return "security_engineer"
    if any(k in title_lower for k in ["ios", "android", "mobile", "react native", "flutter"]):
        return "mobile_developer"
    if any(k in title_lower for k in ["frontend", "front-end", "ui engineer"]):
        return "frontend_react"
    if "c#" in skill_set or ".net" in title_lower or "asp.net" in skill_set:
        return "fullstack_dotnet"
    if "java" in skill_set and "javascript" not in skill_set:
        return "fullstack_java"
    if "go" in skill_set or "golang" in title_lower:
        return "golang_developer"
    if "python" in skill_set:
        return "python_backend"
    return "other"


def _guess_seniority(title: str, description: str) -> str:
    """Guess seniority from title/description."""
    text = f"{title} {description}".lower()
    if any(k in text for k in ["principal", "staff", "distinguished"]):
        return "principal"
    if any(k in text for k in ["lead", "architect", "head of"]):
        return "lead"
    if any(k in text for k in ["senior", "sr.", "sr ", "8+ years", "7+ years", "6+ years", "5+ years"]):
        return "senior"
    if any(k in text for k in ["junior", "jr.", "entry", "associate", "0-2 years", "1-3 years"]):
        return "junior"
    return "mid"


def build_dynamic_profile(
    headline: str | None = None,
    skills: list[str] | None = None,
    experience_years: int = 0,
    preferred_technologies: list[str] | None = None,
    preferred_contract_types: list[str] | None = None,
    summary: str | None = None,
) -> str:
    """Build a dynamic user profile string for AI scoring from DB fields."""
    parts = []

    if headline:
        parts.append(headline)
    elif skills:
        parts.append(f"Software Engineer with expertise in {', '.join(skills[:5])}")

    if experience_years:
        parts.append(f"{experience_years}+ years experience")

    all_tech = list(set((skills or []) + (preferred_technologies or [])))
    if all_tech:
        parts.append(", ".join(all_tech[:15]))

    if preferred_contract_types:
        parts.append(f"Seeking {', '.join(preferred_contract_types)} roles")
    else:
        parts.append("Remote roles in the USA")

    if summary:
        parts.append(summary[:200])

    return " | ".join(parts) if parts else (
        "Software Developer | 5+ years experience | "
        "Open to any technology stack | Remote roles in the USA"
    )


def get_search_queries_for_skills(
    skills: list[str],
    preferred_roles: list[str] | None = None,
    location: str = "USA",
) -> list[str]:
    """Generate diverse JSearch queries based on user skills and preferred roles."""
    queries = []

    # Use preferred roles if specified
    if preferred_roles:
        for role_key in preferred_roles:
            template = ROLE_TEMPLATES.get(role_key)
            if template:
                queries.extend(template["search_queries"])

    # Generate skill-based queries
    if skills:
        top_skills = skills[:3]
        queries.append(f"{' '.join(top_skills)} developer remote {location}")
        queries.append(f"{top_skills[0]} engineer remote contract {location}")
        if len(top_skills) > 1:
            queries.append(f"{top_skills[0]} {top_skills[1]} developer remote {location}")

    # Deduplicate while preserving order
    seen = set()
    unique: list[str] = []
    for q in queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique.append(q)

    return unique[:6]  # Cap at 6 queries to control API usage
