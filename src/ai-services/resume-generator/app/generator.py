import json
import logging
from uuid import uuid4

from openai import AsyncOpenAI
from app.config import settings
from app.models import ResumeRequest, ResumeResponse

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

RESUME_PROMPT = """You are an expert resume writer specializing in technical roles.

Generate a tailored resume for the following job opportunity.

Target Job:
- Title: {job_title}
- Company: {company_name}
- Key Technologies: {technologies}
- Description: {job_description}

Candidate Info:
- Name: {user_name}
- Experience: {experience_years} years
- Skills: {user_skills}
- Summary: {user_summary}

Base Resume:
{base_resume}

Requirements:
1. Emphasize the candidate's skills that match the job requirements
2. Tailor the professional summary to this specific role and technology stack
3. Highlight relevant technical experience with the listed technologies
4. Use quantifiable achievements where possible
5. Format in clean Markdown
6. Do NOT assume or add skills the candidate doesn't have

Return ONLY the resume content in Markdown format."""

COVER_LETTER_PROMPT = """Write a professional cover letter for a developer applying to:

Job: {job_title} at {company_name}
Technologies: {technologies}
Description: {job_description}

Candidate: {user_name} with {experience_years} years of experience.
Key skills: {user_skills}

The cover letter should:
1. Be concise (3-4 paragraphs)
2. Highlight how the candidate's specific skills match this role
3. Show enthusiasm for the role and company
4. Be professional but personable
5. Reference specific technologies from the job posting that the candidate knows

Return ONLY the cover letter text."""

OUTREACH_PROMPT = """Write a short, professional recruiter outreach email for:

Job: {job_title} at {company_name}
Candidate: {user_name}, {experience_years} years experience
Key skills: {user_skills}

The email should be:
1. Brief (2-3 paragraphs max)
2. Professional and confident
3. Highlight top relevant skills for THIS specific role
4. Include a call to action

Return ONLY the email text (no subject line)."""


async def generate_resume(request: ResumeRequest) -> ResumeResponse:
    """Generate tailored resume, cover letter, and outreach email."""

    tech_str = ", ".join(request.technologies) if request.technologies else "Various technologies"
    skills_str = ", ".join(request.user_skills) if request.user_skills else "Software Development"

    resume_content = _generate_fallback_resume(request)
    cover_letter = _generate_fallback_cover_letter(request)
    outreach_email = _generate_fallback_outreach(request)

    if client:
        try:
            # Generate resume
            resume_resp = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer."},
                    {"role": "user", "content": RESUME_PROMPT.format(
                        job_title=request.job_title,
                        company_name=request.company_name or "the company",
                        technologies=tech_str,
                        job_description=(request.job_description or "")[:3000],
                        user_name=request.user_name or "Candidate",
                        experience_years=request.user_experience_years,
                        user_skills=skills_str,
                        user_summary=request.user_summary or "",
                        base_resume=request.base_resume[:2000] if request.base_resume else "Not provided",
                    )},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            resume_content = resume_resp.choices[0].message.content or resume_content

            # Generate cover letter
            cl_resp = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer."},
                    {"role": "user", "content": COVER_LETTER_PROMPT.format(
                        job_title=request.job_title,
                        company_name=request.company_name or "the company",
                        technologies=tech_str,
                        job_description=(request.job_description or "")[:2000],
                        user_name=request.user_name or "Candidate",
                        experience_years=request.user_experience_years,
                        user_skills=skills_str,
                    )},
                ],
                temperature=0.4,
                max_tokens=1000,
            )
            cover_letter = cl_resp.choices[0].message.content or cover_letter

            # Generate outreach email
            out_resp = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional email writer."},
                    {"role": "user", "content": OUTREACH_PROMPT.format(
                        job_title=request.job_title,
                        company_name=request.company_name or "the company",
                        user_name=request.user_name or "Candidate",
                        experience_years=request.user_experience_years,
                        user_skills=skills_str,
                    )},
                ],
                temperature=0.4,
                max_tokens=500,
            )
            outreach_email = out_resp.choices[0].message.content or outreach_email

        except Exception as e:
            logger.error(f"LLM generation failed: {e}. Using fallback templates.")

    return ResumeResponse(
        resume_id=uuid4(),
        user_id=request.user_id,
        job_id=request.job_id,
        resume_content=resume_content,
        cover_letter=cover_letter,
        outreach_email=outreach_email,
    )


def _generate_fallback_resume(req: ResumeRequest) -> str:
    name = req.user_name or "Your Name"
    skills = ", ".join(req.user_skills) if req.user_skills else "Software Development"
    return f"""# {name}

## Professional Summary
Experienced Software Developer with {req.user_experience_years}+ years of experience in building
production-grade applications. Strong technical background with proven expertise in
modern development practices and technologies.

## Technical Skills
{skills}

## Tailored For
**{req.job_title}** at **{req.company_name or 'Company'}**

## Experience
*Details to be customized based on your base resume*

---
*This is a template resume. Configure your OpenAI API key for AI-generated tailored resumes.*
"""


def _generate_fallback_cover_letter(req: ResumeRequest) -> str:
    skills = ", ".join(req.user_skills[:5]) if req.user_skills else "software development"
    return f"""Dear Hiring Manager,

I am writing to express my interest in the {req.job_title} position at {req.company_name or 'your company'}.
With {req.user_experience_years}+ years of experience, I am confident in my ability
to contribute effectively to your team.

My expertise in {skills} aligns well with the requirements of this role.
I have a strong background in building scalable, production-quality applications.

I look forward to discussing how my skills and experience can benefit your team.

Best regards,
{req.user_name or 'Candidate'}
"""


def _generate_fallback_outreach(req: ResumeRequest) -> str:
    return f"""Hi,

I came across the {req.job_title} position at {req.company_name or 'your company'} and I'm very interested.
With {req.user_experience_years}+ years of development experience, I believe I'd be a great fit.

Would you have time for a brief call this week to discuss the opportunity?

Best regards,
{req.user_name or 'Candidate'}
"""
