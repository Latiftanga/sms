FROM python:3.13-alpine
LABEL maintainer="ttek.com"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apk update && \
    apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        postgresql-dev \
        linux-headers \
        libc-dev \
        jpeg-dev \
        zlib-dev && \
    apk add --no-cache \
        postgresql-client \
        jpeg \
        zlib

# Create virtual environment and upgrade pip
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip --no-cache-dir

# Copy requirements files
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Install Python dependencies
ARG DEV=false
RUN /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install --no-cache-dir -r /tmp/requirements.dev.txt; \
    fi

# Clean up build dependencies and temporary files
RUN apk del .build-deps && \
    rm -rf /tmp/* && \
    rm -rf /var/cache/apk/* && \
    find /py -name "*.pyc" -delete && \
    find /py -name "__pycache__" -type d -exec rm -rf {} + || true

# Create non-root user
RUN adduser \
        --disabled-password \
        --no-create-home \
        --shell /bin/false \
        --uid 1000 \
        sms_user

# Set up application directory
WORKDIR /sms
COPY --chown=sms_user:sms_user ./sms /sms

# Create necessary directories with proper ownership
RUN mkdir -p /sms/logs /sms/media /sms/static && \
    chown -R sms_user:sms_user /sms && \
    chmod -R 755 /sms

# Set PATH
ENV PATH="/py/bin:$PATH"

# Switch to non-root user
USER sms_user

EXPOSE 8000

# Health check that works with Django
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/admin/', timeout=5)" || exit 1