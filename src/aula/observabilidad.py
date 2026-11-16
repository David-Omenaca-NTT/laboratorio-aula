"""Logging estructurado para la API de Aula."""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOMBRE_LOGGER = "aula.observabilidad"
logger = logging.getLogger(NOMBRE_LOGGER)
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def version_actual(version_fallback: str) -> str:
    return os.environ.get("AULA_VERSION") or version_fallback


def registrar_evento(
    evento: str,
    *,
    version: str,
    correlation_id: str,
    nivel: int = logging.INFO,
    **atributos: Any,
) -> None:
    registro = {
        **atributos,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        ),
        "level": logging.getLevelName(nivel),
        "event": evento,
        "version": version_actual(version),
        "correlation_id": correlation_id,
    }
    logger.log(nivel, json.dumps(registro, ensure_ascii=False, separators=(",", ":")))


def traza_tecnica(error: Exception) -> list[dict[str, Any]]:
    return [
        {
            "file": Path(frame.filename).name,
            "line": frame.lineno,
            "function": frame.name,
        }
        for frame in traceback.extract_tb(error.__traceback__)
    ]
