from pydantic import BaseModel
from uuid import UUID


class ResumeRequest(BaseModel):
    user_id: UUID
    job_id: UUID
    job_title: str
    company_name: str | None = None
    job_description: str | None = None
    technologies: list[str] = []
    user_name: str = ""
    user_summary: str = ""
    user_skills: list[str] = []
    user_experience_years: int = 0
    base_resume: str = ""


class ResumeResponse(BaseModel):
    resume_id: UUID
    user_id: UUID
    job_id: UUID
    resume_content: str
    cover_letter: str
    outreach_email: str
    format: str = "markdown"
