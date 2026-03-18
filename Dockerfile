# Python backend services
FROM python:3.12-slim AS backend-base
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip

# ─── API Gateway ─────────────────────────────────────────────────────────────
FROM backend-base AS api-gateway
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/api-gateway/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

# ─── Job Discovery ───────────────────────────────────────────────────────────
FROM backend-base AS job-discovery
COPY src/backend/shared /app/shared
COPY src/backend/job-discovery/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/job-discovery/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]

# ─── Job Intelligence ────────────────────────────────────────────────────────
FROM backend-base AS job-intelligence
COPY src/backend/shared /app/shared
COPY src/ai-services/job-intelligence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/job-intelligence/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]

# ─── Resume Generator ────────────────────────────────────────────────────────
FROM backend-base AS resume-generator
COPY src/backend/shared /app/shared
COPY src/ai-services/resume-generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/resume-generator/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5003"]

# ─── Application Automation ──────────────────────────────────────────────────
FROM backend-base AS application-automation
COPY src/backend/shared /app/shared
COPY src/backend/application-automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/application-automation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5004"]

# ─── Notifications ───────────────────────────────────────────────────────────
FROM backend-base AS notifications
COPY src/backend/shared /app/shared
COPY src/backend/notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/notifications/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5005"]

# ─── Crawl Engine ────────────────────────────────────────────────────────────
FROM backend-base AS crawl-engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    fonts-liberation fonts-noto-color-emoji fonts-unifont \
    && rm -rf /var/lib/apt/lists/*
COPY src/backend/shared /app/shared
COPY src/backend/crawl-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium
COPY src/backend/crawl-engine/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5006"]

# ─── Data Pipeline ───────────────────────────────────────────────────────────
FROM backend-base AS data-pipeline
COPY src/backend/shared /app/shared
COPY src/backend/data-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/data-pipeline/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5007
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5007"]

# ─── Knowledge Graph ─────────────────────────────────────────────────────────
FROM backend-base AS knowledge-graph
COPY src/backend/shared /app/shared
COPY src/backend/knowledge-graph/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/knowledge-graph/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5008
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5008"]

# ─── Decision Engine ─────────────────────────────────────────────────────────
FROM backend-base AS decision-engine
COPY src/backend/shared /app/shared
COPY src/backend/decision-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/decision-engine/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5009
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5009"]

# ─── Predictive AI ───────────────────────────────────────────────────────────
FROM backend-base AS predictive-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/predictive-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/predictive-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5010"]

# ─── LinkedIn Automation ─────────────────────────────────────────────────────
FROM backend-base AS linkedin-automation
COPY src/backend/shared /app/shared
COPY src/backend/linkedin-automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/linkedin-automation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5011
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5011"]

# ─── Voice AI ────────────────────────────────────────────────────────────────
FROM backend-base AS voice-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/voice-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/voice-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5012
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5012"]

# ─── Interview AI ────────────────────────────────────────────────────────────
FROM backend-base AS interview-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/interview-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/interview-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5013
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5013"]

# ─── Negotiation AI ─────────────────────────────────────────────────────────
FROM backend-base AS negotiation-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/negotiation-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/negotiation-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5014
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5014"]

# ─── Freelance Bidding ───────────────────────────────────────────────────────
FROM backend-base AS freelance-bidding
COPY src/backend/shared /app/shared
COPY src/backend/freelance-bidding/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/freelance-bidding/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5015
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5015"]

# ─── Demand Generation ───────────────────────────────────────────────────────
FROM backend-base AS demand-generation
COPY src/backend/shared /app/shared
COPY src/backend/demand-generation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/demand-generation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5016
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5016"]

# ─── Agent Orchestrator ──────────────────────────────────────────────────────
FROM backend-base AS agent-orchestrator
COPY src/backend/shared /app/shared
COPY src/ai-services/agent-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/agent-orchestrator/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5017
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5017"]

# ─── Subscription & Billing ──────────────────────────────────────────────────
FROM backend-base AS subscription
COPY src/backend/shared /app/shared
COPY src/backend/subscription/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/subscription/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5018
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5018"]

# ─── Job Marketplace ─────────────────────────────────────────────────────────
FROM backend-base AS marketplace
COPY src/backend/shared /app/shared
COPY src/backend/marketplace/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/marketplace/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5019
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5019"]

# ─── Web (Next.js) ───────────────────────────────────────────────────────────
FROM node:20-alpine AS web
WORKDIR /app
COPY src/web/package.json src/web/package-lock.json* ./
RUN npm install
COPY src/web/ .
ENV API_BACKEND_URL=http://api-gateway:5000
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]

# ─── Celery Worker ───────────────────────────────────────────────────────────
FROM backend-base AS celery-worker
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt celery[redis]==5.3.6 psycopg2-binary==2.9.9
ENV PYTHONPATH=/app
CMD ["celery", "-A", "shared.celery_app", "worker", "-l", "info", "-Q", "default,auto_apply,notifications,crawl,intelligence,feedback"]

# ─── Celery Beat ─────────────────────────────────────────────────────────────
FROM backend-base AS celery-beat
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt celery[redis]==5.3.6 psycopg2-binary==2.9.9
ENV PYTHONPATH=/app
CMD ["celery", "-A", "shared.celery_app", "beat", "-l", "info"]
