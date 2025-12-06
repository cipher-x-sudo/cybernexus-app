# Multi-stage build for CyberNexus (Frontend + Backend)

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Backend + Serve Frontend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies including Node.js for frontend runtime
RUN apt-get update && apt-get install -y \
    gcc \
    supervisor \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# Supervisor config to run backend (on port 3000 for Railway) and frontend
RUN echo '[supervisord] \n\
nodaemon=true \n\
\n\
[program:backend] \n\
command=uvicorn app.main:app --host 0.0.0.0 --port 3000 \n\
directory=/app/backend \n\
autostart=true \n\
autorestart=true \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
\n\
[program:frontend] \n\
command=/usr/bin/node node_modules/next/dist/bin/next start -p 3001 \n\
directory=/app/frontend \n\
autostart=true \n\
autorestart=true \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
' > /etc/supervisor/conf.d/app.conf

# Expose main port (nginx gateway)
EXPOSE 3000

# Start supervisor
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

