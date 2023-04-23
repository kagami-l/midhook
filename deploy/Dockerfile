FROM python:3.9-slim

RUN apt-get update -y && apt install -y curl

RUN mkdir -p /midhook

COPY ../poetry.lock pyproject.toml /midhook/

WORKDIR /midhook

ENV POETRY_VIRTUALENVS_CREATE false
RUN pip install poetry && poetry install --no-root --no-dev

COPY ../midhook/ /midhook/midhook

ENTRYPOINT ["uvicorn", "midhook.app.app:app", "--host", "0.0.0.0"]
CMD ["--port", "23518"]

# ENTRYPOINT ["gunicorn", "midhook.app.app:app", "--workers", "8", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "2400"]
# CMD ["--bind", "0.0.0.0:23518"]