# ============================================================
# PEVN Frontend — Dockerfile (Development)
# ============================================================
# This Dockerfile is optimized for development with hot reload.
# For production, a multi-stage build that serves static files
# via nginx would be used instead.
# ============================================================

FROM node:20.18-alpine AS development

# Security: Create non-root user
RUN addgroup --gid 1001 pevn \
    && adduser \
        --uid 1001 \
        --ingroup pevn \
        --disabled-password \
        --no-create-home \
        pevn

WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci --prefer-offline

# Copy application source
# In development, this is overridden by a volume mount (docker-compose)
COPY . .

# Set ownership
RUN chown -R pevn:pevn /app

USER pevn

# Expose the development server port
EXPOSE 3000

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=15s \
    --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

# Start the Vite development server bound to all interfaces
CMD ["npm", "run", "dev"]
