"""Data ingestion processor — deduplicates, normalizes, and routes crawled data."""

import hashlib
import logging
from datetime import datetime

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db_session
from shared.models import Job, Company, HiringSignal, PipelineEvent
from shared.events import EventBus, Exchanges
from app.config import settings

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes raw crawled items into structured database records."""

    def __init__(self):
        self.event_bus = EventBus(settings.rabbitmq_url)
        self.redis: aioredis.Redis | None = None

    async def connect(self):
        await self.event_bus.connect()
        self.redis = aioredis.from_url(settings.redis_url)

    async def _is_duplicate(self, content_hash: str) -> bool:
        """Check content hash against Redis dedup cache."""
        key = f"dedup:{content_hash}"
        exists = await self.redis.exists(key)
        if exists:
            return True
        await self.redis.setex(key, settings.dedup_ttl_hours * 3600, "1")
        return False

    async def process_job(self, data: dict) -> dict | None:
        """Process a crawled job item into a Job record."""
        content_hash = data.get("content_hash", "")
        if content_hash and await self._is_duplicate(content_hash):
            logger.debug(f"Duplicate job skipped: {data.get('title', '')}")
            return None

        extracted = data.get("extracted_data", {})

        async for db in get_db_session():
            # Check DB-level dedup by external_id + source
            external_id = data.get("external_id", "")
            source = data.get("source", "unknown")

            # Generate a stable ID from content_hash or URL+title
            if not external_id:
                content_hash = data.get("content_hash", "")
                if content_hash:
                    external_id = content_hash[:32]
                else:
                    external_id = hashlib.sha256(
                        f"{data.get('url', '')}:{data.get('title', '')}".encode()
                    ).hexdigest()[:32]

            existing = await db.execute(
                select(Job).where(Job.external_id == external_id, Job.source == source)
            )
            if existing.scalar_one_or_none():
                return None

            # Normalize and create job
            date_posted = None
            dp_raw = data.get("date_posted") or extracted.get("date_posted")
            if dp_raw:
                try:
                    date_posted = datetime.fromisoformat(dp_raw) if isinstance(dp_raw, str) else dp_raw
                except (ValueError, TypeError):
                    pass

            job = Job(
                external_id=external_id,
                source=source,
                job_title=self._normalize_title(data.get("title", "")),
                company_name=extracted.get("company_name", ""),
                job_description=extracted.get("job_description", ""),
                job_link=data.get("url", ""),
                location=extracted.get("location", ""),
                is_remote=self._detect_remote(data),
                contract_type=self._detect_contract_type(data),
                salary_or_rate=extracted.get("salary", ""),
                recruiter_name=extracted.get("recruiter_name", ""),
                recruiter_email=extracted.get("recruiter_email", ""),
                raw_data=data,
                date_discovered=datetime.utcnow(),
                date_posted=date_posted,
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            # Log pipeline event
            event = PipelineEvent(
                event_type="job_ingested",
                source_service="data-pipeline",
                payload={"job_id": str(job.id), "source": source, "title": job.job_title},
            )
            db.add(event)
            await db.commit()

            # Publish for AI analysis
            await self.event_bus.publish(Exchanges.JOB_ANALYZED, {
                "job_id": str(job.id),
                "job_title": job.job_title,
                "company_name": job.company_name,
                "job_description": job.job_description or "",
                "job_link": job.job_link,
            })

            logger.info(f"Ingested job: {job.job_title} from {source}")
            return {"job_id": str(job.id), "title": job.job_title}

    async def process_signal(self, data: dict) -> dict | None:
        """Process a hiring signal into a HiringSignal record."""
        content_hash = data.get("content_hash", "")
        if content_hash and await self._is_duplicate(content_hash):
            return None

        extracted = data.get("extracted_data", {})

        async for db in get_db_session():
            # Resolve or create company
            company_id = None
            company_name = extracted.get("company_name", "")
            if company_name:
                result = await db.execute(
                    select(Company).where(Company.name == company_name)
                )
                company = result.scalar_one_or_none()
                if not company:
                    company = Company(name=company_name, is_actively_hiring=True)
                    db.add(company)
                    await db.flush()
                else:
                    company.is_actively_hiring = True
                    company.hiring_velocity = (company.hiring_velocity or 0) + 1
                company_id = company.id

            signal_types = extracted.get("signal_types", [])
            signal = HiringSignal(
                company_id=company_id,
                signal_type=signal_types[0] if signal_types else "unknown",
                title=data.get("title", ""),
                description=extracted.get("description", ""),
                source_url=data.get("url", ""),
                source_name=data.get("source", ""),
                confidence=extracted.get("confidence", 0.5),
                predicted_roles=extracted.get("predicted_roles", []),
                raw_data=data,
            )
            db.add(signal)

            event = PipelineEvent(
                event_type="signal_ingested",
                source_service="data-pipeline",
                payload={
                    "signal_id": str(signal.id),
                    "signal_type": signal.signal_type,
                    "company": company_name,
                },
            )
            db.add(event)
            await db.commit()

            # Publish signal event
            await self.event_bus.publish("signal.detected", {
                "signal_id": str(signal.id),
                "company_name": company_name,
                "signal_type": signal.signal_type,
                "confidence": float(signal.confidence) if signal.confidence else 0.5,
            })

            logger.info(f"Ingested signal: {signal.title} ({signal.signal_type})")
            return {"signal_id": str(signal.id), "type": signal.signal_type}

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize job titles."""
        title = title.strip()
        # Remove common prefixes
        for prefix in ["HIRING:", "[HIRING]", "NEW:", "🔥", "🚀"]:
            if title.upper().startswith(prefix):
                title = title[len(prefix):].strip()
        return title[:500]

    @staticmethod
    def _detect_remote(data: dict) -> bool:
        text = f"{data.get('title', '')} {data.get('extracted_data', {}).get('location', '')}".lower()
        return any(kw in text for kw in ["remote", "work from home", "wfh", "anywhere", "distributed"])

    @staticmethod
    def _detect_contract_type(data: dict) -> str:
        text = f"{data.get('title', '')} {data.get('extracted_data', {}).get('job_description', '')}".lower()
        if "contract" in text or "c2c" in text or "w2" in text:
            return "contract"
        if "freelance" in text or "contractor" in text:
            return "freelance"
        if "full-time" in text or "full time" in text or "permanent" in text:
            return "full-time"
        return "unknown"
