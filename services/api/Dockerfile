# Build from the repo root: docker build -f services/api/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/api

RUN pip install --no-cache-dir uv==0.5.*

COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY services/api/app ./app
# RAG loads the corpus from parents[4]/corpus, i.e. /corpus in this image.
COPY corpus /corpus
ENV PATH="/srv/api/.venv/bin:$PATH"

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
