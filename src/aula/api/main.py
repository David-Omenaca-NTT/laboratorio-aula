"""Servicio de arranque. S1 y S2 completan los recursos pendientes."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from ..dominio.modelos import EstadoMatricula, Expediente, SolicitudMatricula
from ..reglas.motor import (VentanaCerrada, VentanaMatricula,
                            evaluar_solicitud)
from ..reglas.planes import cargar_plan


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.matriculas = []
    app.state.expedientes = {}
    yield


app = FastAPI(title="Aula Students", version="0.0.0", lifespan=lifespan)


class SolicitudEntrada(BaseModel):
    estudiante_id: StrictStr = Field(min_length=1)
    curso_academico: StrictStr = Field(min_length=1)
    codigos: list[StrictStr] = Field(min_length=1)
    momento: datetime | None = None

    @field_validator("estudiante_id", "curso_academico")
    @classmethod
    def validar_cadena_no_vacia(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("el campo no puede estar vacio")
        return valor

    @field_validator("codigos")
    @classmethod
    def validar_codigos(cls, codigos: list[str]) -> list[str]:
        if any(not codigo.strip() for codigo in codigos):
            raise ValueError("los codigos no pueden estar vacios")
        if len(codigos) != len(set(codigos)):
            raise ValueError("la solicitud no puede repetir codigos")
        return codigos

    @field_validator("momento", mode="before")
    @classmethod
    def validar_momento_iso(cls, valor):
        if valor is None:
            return None
        if not isinstance(valor, str):
            raise ValueError("momento debe ser una fecha ISO-8601")
        try:
            datetime.fromisoformat(valor.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("momento debe ser una fecha ISO-8601") from error
        return valor


class LineaMatriculaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo_asignatura: str
    creditos: int
    admitida: bool
    en_espera: bool
    motivo_rechazo: str | None
    motivo_espera: str | None


class MatriculaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    estudiante_id: str
    curso_academico: str
    plan_aplicado: str
    version_plan_aplicada: str
    estado: EstadoMatricula
    lineas: list[LineaMatriculaRespuesta]
    creditos_admitidos: int


def _ventana_configurada() -> VentanaMatricula:
    inicio = os.environ.get("MATRICULA_INICIO")
    fin = os.environ.get("MATRICULA_FIN")
    if not inicio or not fin:
        raise HTTPException(
            status_code=503,
            detail="Configura MATRICULA_INICIO y MATRICULA_FIN en formato ISO-8601",
        )
    try:
        return VentanaMatricula(inicio=inicio, fin=fin)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail="La ventana de matricula configurada no es valida: %s" % error,
        ) from error


@app.get("/salud")
def salud():
    return {"estado": "ok", "momento": datetime.now(timezone.utc).isoformat()}


@app.post(
    "/matriculas", response_model=MatriculaRespuesta, status_code=201,
)
def crear_matricula(entrada: SolicitudEntrada):
    plan = cargar_plan("PLAN-2024")
    desconocidos = [codigo for codigo in entrada.codigos
                    if codigo not in plan.asignaturas]
    if desconocidos:
        raise HTTPException(
            status_code=422,
            detail="Asignaturas fuera del plan PLAN-2024: %s"
            % ", ".join(desconocidos),
        )

    momento = entrada.momento or datetime.now(timezone.utc)
    solicitud = SolicitudMatricula(
        estudiante_id=entrada.estudiante_id,
        curso_academico=entrada.curso_academico,
        codigos=entrada.codigos,
        momento=momento.isoformat(),
    )
    expediente = app.state.expedientes.get(
        entrada.estudiante_id,
        Expediente(estudiante_id=entrada.estudiante_id, plan=plan.codigo),
    )
    try:
        matricula = evaluar_solicitud(
            solicitud, expediente, plan, _ventana_configurada(), grupos={},
        )
    except VentanaCerrada as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    app.state.matriculas.append(matricula)
    return matricula


@app.get("/expedientes/{estudiante_id}")
def ver_expediente(estudiante_id: str):
    raise HTTPException(status_code=501, detail="S2: consulta de expediente pendiente")