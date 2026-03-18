# Autonomous AI Career Agent — System Architecture

## Overview

A production-grade, event-driven microservices platform that acts as a 24/7 AI recruiter.
It discovers remote .NET contract jobs, analyzes them with AI, generates tailored resumes,
optionally auto-applies, and delivers notifications via web, mobile, and messaging channels.

---

## High-Level Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Next.js    │     │ React Native │     │  Telegram / WA   │
│  Dashboard   │     │  Mobile App  │     │  Bot Channels    │
└──────┬───────┘     └──────┬───────┘     └────────┬─────────┘
       │                    │                      │
       └────────────────────┼──────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   API Gateway   │
                   │   (FastAPI)     │
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │   Job       │  │   Job AI    │  │  Resume     │
   │  Discovery  │  │ Intelligence│  │  Generator  │
   │  Service    │  │  Service    │  │  Service    │
   │  (FastAPI)  │  │ (FastAPI)   │  │ (FastAPI)   │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                 │                 │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ Application │  │Notification │  │   Shared    │
   │ Automation  │  │  Service    │  │   Infra     │
   │  (FastAPI)  │  │  (FastAPI)  │  │             │
   └─────────────┘  └─────────────┘  └─────────────┘

        ┌──────────────────────────────────┐
        │        Infrastructure            │
        │  PostgreSQL │ Redis │ Qdrant     │
        │  RabbitMQ   │ Docker             │
        └──────────────────────────────────┘
```

---

## Technology Stack

| Layer          | Technology                                                     |
|----------------|----------------------------------------------------------------|
| Backend        | Python 3.12, FastAPI, Uvicorn, Pydantic v2                     |
| Database       | PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg                 |
| Messaging      | RabbitMQ, aio-pika                                             |
| Cache          | Redis 7                                                        |
| Vector Search  | Qdrant                                                         |
| AI / LLM       | OpenAI GPT-4o-mini via `openai` SDK                            |
| Auth           | JWT via python-jose, bcrypt via passlib                        |
| Web Scraping   | httpx, beautifulsoup4, lxml                                    |
| Web Frontend   | Next.js 14, React 18, TailwindCSS, Zustand, Axios             |
| Mobile App     | React Native (Expo 50), React Navigation, AsyncStorage         |
| Deployment     | Docker, Docker Compose                                         |

---

## Service Breakdown

| Service                 | Stack          | Port  | Purpose                                      |
|-------------------------|----------------|-------|----------------------------------------------|
| API Gateway             | Python FastAPI | 5000  | Routes, JWT auth, reverse proxy              |
| Job Discovery Service   | Python FastAPI | 5001  | Crawls 5 job boards every 3 hours            |
| Job Intelligence AI     | Python FastAPI | 5002  | LLM analysis, scoring, entity extraction     |
| Resume Generator AI     | Python FastAPI | 5003  | Generates tailored resumes & cover letters   |
| Application Automation  | Python FastAPI | 5004  | Auto-applies to jobs via email               |
| Notification Service    | Python FastAPI | 5005  | Telegram, WhatsApp, Email, scheduled reports |
| Web Dashboard           | Next.js 14     | 3000  | Job feed, analytics, resume manager          |
| Mobile App              | React Native   | —     | Push alerts, quick apply, profile            |

---

## Event-Driven Communication

**Message Broker:** RabbitMQ (aio-pika, fanout exchanges)

| Exchange                       | Producer            | Consumer(s)                          |
|--------------------------------|---------------------|--------------------------------------|
| `career.job.discovered`        | Job Discovery       | Job Intelligence AI                  |
| `career.job.analyzed`          | Job Intelligence    | Notification, Application Automation |
| `career.resume.generated`      | Resume Generator    | Application Automation               |
| `career.application.submitted` | App Automation      | Notification                         |
| `career.notification.send`     | Any service         | Notification Service                 |
| `career.crawl.completed`       | Job Discovery       | Dashboard (polling)                  |

---

## Job Board Crawlers

| Source          | Method        | URL Pattern                              |
|-----------------|---------------|------------------------------------------|
| RemoteOK        | JSON API      | remoteok.com/api?tag=...                 |
| WeWorkRemotely  | HTML scraping | weworkremotely.com/remote-jobs/search    |
| LinkedIn        | HTML scraping | linkedin.com/jobs-guest/jobs/api/...     |
| Indeed          | HTML scraping | indeed.com/jobs?q=...&l=Remote           |
| Dice            | HTML scraping | dice.com/jobs?q=...&filters.isRemote=... |

---

## Database Schema (PostgreSQL)

See `src/shared/database/schema.sql` for full DDL.

Key tables: `users`, `user_profiles`, `jobs`, `job_analyses`, `recruiter_contacts`,
`generated_resumes`, `job_applications`, `notifications`, `crawl_logs`

---

## Getting Started

```bash
# 1. Copy environment file
cp .env.example .env
# 2. Edit .env with your API keys
# 3. Start everything
docker-compose up --build
```

Web dashboard: http://localhost:3000
API Gateway: http://localhost:5000
RabbitMQ Management: http://localhost:15672

---

## Deployment

All services are containerized with Docker. See `docker-compose.yml` and `Dockerfile`.
