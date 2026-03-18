# Python backend services
FROM python:3.12-slim AS backend-base
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip && \
    groupadd -r appuser && useradd -r -g appuser -d /app appuser && \
    chown appuser:appuser /app

# â”€â”€â”€ API Gateway â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS api-gateway
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/api-gateway/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

# â”€â”€â”€ Job Discovery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS job-discovery
COPY src/backend/shared /app/shared
COPY src/backend/job-discovery/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/job-discovery/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5001
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]

# â”€â”€â”€ Job Intelligence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS job-intelligence
COPY src/backend/shared /app/shared
COPY src/ai-services/job-intelligence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/job-intelligence/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5002
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]

# â”€â”€â”€ Resume Generator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS resume-generator
COPY src/backend/shared /app/shared
COPY src/ai-services/resume-generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/resume-generator/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5003
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5003"]

# â”€â”€â”€ Application Automation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS application-automation
COPY src/backend/shared /app/shared
COPY src/backend/application-automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/application-automation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5004
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5004"]

# â”€â”€â”€ Notifications â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS notifications
COPY src/backend/shared /app/shared
COPY src/backend/notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/notifications/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5005
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5005"]

# â”€â”€â”€ Crawl Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5006"]

# â”€â”€â”€ Data Pipeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS data-pipeline
COPY src/backend/shared /app/shared
COPY src/backend/data-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/data-pipeline/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5007
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5007"]

# â”€â”€â”€ Knowledge Graph â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS knowledge-graph
COPY src/backend/shared /app/shared
COPY src/backend/knowledge-graph/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/knowledge-graph/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5008
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5008"]

# â”€â”€â”€ Decision Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS decision-engine
COPY src/backend/shared /app/shared
COPY src/backend/decision-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/decision-engine/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5009
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5009"]

# â”€â”€â”€ Predictive AI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS predictive-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/predictive-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/predictive-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5010
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5010"]

# â”€â”€â”€ LinkedIn Automation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS linkedin-automation
COPY src/backend/shared /app/shared
COPY src/backend/linkedin-automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/linkedin-automation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5011
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5011"]

# â”€â”€â”€ Voice AI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS voice-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/voice-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/voice-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5012
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5012"]

# â”€â”€â”€ Interview AI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS interview-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/interview-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/interview-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5013
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5013"]

# â”€â”€â”€ Negotiation AI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS negotiation-ai
COPY src/backend/shared /app/shared
COPY src/ai-services/negotiation-ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/negotiation-ai/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5014
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5014"]

# â”€â”€â”€ Freelance Bidding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS freelance-bidding
COPY src/backend/shared /app/shared
COPY src/backend/freelance-bidding/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/freelance-bidding/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5015
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5015"]

# â”€â”€â”€ Demand Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS demand-generation
COPY src/backend/shared /app/shared
COPY src/backend/demand-generation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/demand-generation/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5016
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5016"]

# â”€â”€â”€ Agent Orchestrator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS agent-orchestrator
COPY src/backend/shared /app/shared
COPY src/ai-services/agent-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ai-services/agent-orchestrator/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5017
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5017"]

# â”€â”€â”€ Subscription & Billing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS subscription
COPY src/backend/shared /app/shared
COPY src/backend/subscription/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/subscription/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5018
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5018"]

# â”€â”€â”€ Job Marketplace â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS marketplace
COPY src/backend/shared /app/shared
COPY src/backend/marketplace/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/marketplace/app /app/app
ENV PYTHONPATH=/app
EXPOSE 5019
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5019"]

# â”€â”€â”€ Web (Next.js) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM node:20-alpine AS web
WORKDIR /app
COPY src/web/package.json src/web/package-lock.json* ./
RUN npm install
COPY src/web/ .
ENV API_BACKEND_URL=http://api-gateway:5000
RUN npm run build && adduser -D -h /app nodeuser && chown -R nodeuser:nodeuser /app
EXPOSE 3000
USER nodeuser
CMD ["npm", "start"]

# â”€â”€â”€ Celery Worker â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS celery-worker
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt celery[redis]==5.3.6 psycopg2-binary==2.9.9
ENV PYTHONPATH=/app
USER appuser
CMD ["celery", "-A", "shared.celery_app", "worker", "-l", "info", "-Q", "default,auto_apply,notifications,crawl,intelligence,feedback"]

# â”€â”€â”€ Celery Beat â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FROM backend-base AS celery-beat
COPY src/backend/shared /app/shared
COPY src/backend/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt celery[redis]==5.3.6 psycopg2-binary==2.9.9
ENV PYTHONPATH=/app
USER appuser
CMD ["celery", "-A", "shared.celery_app", "beat", "-l", "info"]
