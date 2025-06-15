FROM python:3.12-alpine
LABEL maintainer="ttek.com"

ENV PYTHONUNBUFFERED 1

# Copy requirements
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY . /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false

# Install dependencies and create user
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        gcc postgresql-dev musl-dev zlib-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        app_user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R app_user:app_user /vol && \
    chmod -R 755 /vol

ENV PATH="/py/bin:$PATH"

USER app_user