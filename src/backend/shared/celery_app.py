"""Celery application for background task processing.

Uses the synchronous database_url_sync from settings since Celery workers
run synchronously.  Each service can import ``celery_app`` and register tasks.
"""

from celery import Celery
from celery.schedules import crontab
from shared.config import BaseServiceSettings

_settings = BaseServiceSettings()

celery_app = Celery(
    "career_agent",
    broker=_settings.rabbitmq_url,
    backend=_settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "auto_apply": {"exchange": "auto_apply", "routing_key": "auto_apply"},
        "notifications": {"exchange": "notifications", "routing_key": "notifications"},
        "crawl": {"exchange": "crawl", "routing_key": "crawl"},
        "intelligence": {"exchange": "intelligence", "routing_key": "intelligence"},
        "feedback": {"exchange": "feedback", "routing_key": "feedback"},
    },
    beat_schedule={
        "crawl-every-30-min": {
            "task": "tasks.crawl.run_scheduled_crawl",
            "schedule": 1800.0,
            "options": {"queue": "crawl"},
        },
        "auto-apply-check-every-15-min": {
            "task": "tasks.auto_apply.check_and_apply",
            "schedule": 900.0,
            "options": {"queue": "auto_apply"},
        },
        "feedback-loop-hourly": {
            "task": "tasks.feedback.run_feedback_cycle",
            "schedule": 3600.0,
            "options": {"queue": "feedback"},
        },
        "job-hunt-morning-9am": {
            "task": "tasks.job_hunt.run_job_hunt",
            "schedule": crontab(hour=9, minute=0),
            "options": {"queue": "intelligence"},
        },
        "job-hunt-evening-6pm": {
            "task": "tasks.job_hunt.run_job_hunt",
            "schedule": crontab(hour=18, minute=0),
            "options": {"queue": "intelligence"},
        },
    },
)
