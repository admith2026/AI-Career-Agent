import json
import logging
from contextlib import asynccontextmanager
from uuid import UUID

import aio_pika
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models import JobAnalysisRequest, JobDiscoveredEvent, JobAnalyzedEvent
from app.analyzer import analyze_job

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def start_event_consumer():
    """Subscribe to job.discovered events and process them."""
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)

        exchange = await channel.declare_exchange(
            "career.job.discovered", aio_pika.ExchangeType.FANOUT, durable=True
        )
        queue = await channel.declare_queue(
            "job-intelligence.job.discovered", durable=True
        )
        await queue.bind(exchange)

        # Output exchange
        analyzed_exchange = await channel.declare_exchange(
            "career.job.analyzed", aio_pika.ExchangeType.FANOUT, durable=True
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        event = JobDiscoveredEvent(**data)
                        logger.info(f"Processing job: {event.JobId} - {event.JobTitle}")

                        # Fetch full job from DB
                        job_data = await _fetch_job(event.JobId)
                        if not job_data:
                            logger.warning(f"Job {event.JobId} not found in DB")
                            continue

                        # Analyze
                        request = JobAnalysisRequest(
                            job_id=event.JobId,
                            job_title=job_data["job_title"],
                            company_name=job_data["company_name"],
                            job_description=job_data["job_description"],
                            job_link=job_data["job_link"],
                        )
                        result = await analyze_job(request)

                        # Store analysis
                        await _store_analysis(result)

                        # Publish analyzed event
                        analyzed_event = JobAnalyzedEvent(
                            JobId=result.job_id,
                            MatchScore=result.match_score,
                            Technologies=result.technologies,
                            IsContract=result.is_contract,
                            IsRemote=result.is_remote_confirmed,
                            AiSummary=result.ai_summary,
                        )
                        await analyzed_exchange.publish(
                            aio_pika.Message(
                                body=analyzed_event.model_dump_json().encode(),
                                content_type="application/json",
                            ),
                            routing_key="",
                        )

                        logger.info(
                            f"Job {event.JobId} analyzed: score={result.match_score}"
                        )

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

    except Exception as e:
        logger.error(f"Event consumer error: {e}")


async def _fetch_job(job_id: UUID) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT job_title, company_name, job_description, job_link "
                "FROM jobs WHERE id = :id"
            ),
            {"id": str(job_id)},
        )
        row = result.first()
        if row:
            return {
                "job_title": row[0],
                "company_name": row[1],
                "job_description": row[2],
                "job_link": row[3],
            }
        return None


async def _store_analysis(result) -> None:
    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO job_analyses
                    (id, job_id, technologies, seniority_level, is_contract,
                     is_remote_confirmed, has_recruiter, vendor_detected,
                     match_score, score_breakdown, key_requirements, ai_summary,
                     llm_model, analyzed_at, created_at)
                VALUES
                    (gen_random_uuid(), :job_id, :technologies, :seniority_level, :is_contract,
                     :is_remote, :has_recruiter, :vendor_detected,
                     :match_score, :score_breakdown, :key_requirements, :ai_summary,
                     :llm_model, NOW(), NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    technologies = EXCLUDED.technologies,
                    match_score = EXCLUDED.match_score,
                    score_breakdown = EXCLUDED.score_breakdown,
                    ai_summary = EXCLUDED.ai_summary,
                    analyzed_at = NOW()
                """
            ),
            {
                "job_id": str(result.job_id),
                "technologies": result.technologies,
                "seniority_level": result.seniority_level,
                "is_contract": result.is_contract,
                "is_remote": result.is_remote_confirmed,
                "has_recruiter": result.has_recruiter,
                "vendor_detected": result.vendor_detected,
                "match_score": result.match_score,
                "score_breakdown": result.score_breakdown.model_dump_json(),
                "key_requirements": result.key_requirements,
                "ai_summary": result.ai_summary,
                "llm_model": result.llm_model,
            },
        )
        await session.commit()
