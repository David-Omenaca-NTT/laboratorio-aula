# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS dependencies

WORKDIR /build

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-prod.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install \
    --disable-pip-version-check \
    -r requirements-prod.txt

RUN rm -rf /opt/venv/lib/python3.12/site-packages/pip \
           /opt/venv/lib/python3.12/site-packages/pip-*.dist-info \
    && find /opt/venv -type d -name '__pycache__' -prune -exec rm -rf {} +

FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/aula \
    AULA_TRAZA=/aula/.aula/auditoria.jsonl

WORKDIR /aula

LABEL org.opencontainers.image.source="https://github.com/David-Omenaca-NTT/laboratorio-aula"

RUN useradd --create-home --uid 10001 appuser

COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=10001:10001 src/ ./src/
COPY --chown=10001:10001 datos/planes/ ./datos/planes/

RUN install -d -o 10001 -g 10001 /aula/.aula

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
    --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=2)"]

CMD ["python", "-m", "uvicorn", "src.aula.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
