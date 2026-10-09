# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS dependencies

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --disable-pip-version-check -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/aula \
    AULA_TRAZA=/tmp/aula/auditoria.jsonl

WORKDIR /aula
RUN useradd --create-home --uid 10001 appuser
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=10001:10001 src/ ./src/
COPY --chown=10001:10001 datos/ ./datos/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=2)"]

CMD ["python", "-m", "uvicorn", "src.aula.api.main:app", "--host", "0.0.0.0", "--port", "8000"]