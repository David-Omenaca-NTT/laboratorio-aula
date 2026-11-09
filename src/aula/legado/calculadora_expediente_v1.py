# -*- coding: utf-8 -*-
# calculadora_expediente_v1.py
# Modulo heredado. Comportamiento historico caracterizado por tests.
# NO TOCAR sin caracterizar antes: hay comportamiento del que depende
# el proceso de becas.
#
# Historico (lo poco que se sabe):
#   2019-03  version inicial
#   2020-11  parche convalidaciones (jlm)
#   2021-06  ajuste redondeo por peticion de secretaria
#   2023-01  se anade progreso, sin tocar la media
#
# ATENCION para el student: este fichero es el objeto de la estacion S5.
# Antes de refactorizar nada tienes que caracterizarlo. Si empiezas por el
# refactor, el verificador de S5 lo detecta en el historial de git y la
# estacion no se supera.

import json

APROBADO = 5.0
NOTA_CONVALIDADA = 5.0
DEC = 2
MAX_CONV = 6
_CACHE = {}
DEBUG = False


def _log(msg):
    if DEBUG:
        print("[calc] " + str(msg))


def cargar_plan(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        d = json.load(f)
    m = {}
    for a in d["asignaturas"]:
        m[a["codigo"]] = a
    return d, m


def creditos_de(mapa, cod):
    if cod in mapa:
        return mapa[cod]["creditos"]
    return 0


def es_aprobada(reg):
    return (
        reg["estado"] == "aprobada"
        or reg["estado"] == "convalidada"
    )


def ultima_aprobada(regs, cod):
    seleccionada = None
    for registro in regs:
        if registro["codigo_asignatura"] != cod:
            continue
        if registro["estado"] != "aprobada":
            continue
        if seleccionada is None:
            seleccionada = registro
        else:
            if registro["convocatoria"] > seleccionada["convocatoria"]:
                seleccionada = registro
    return seleccionada


def hay_convalidacion(regs, cod):
    for x in regs:
        if x["codigo_asignatura"] == cod and x["estado"] == "convalidada":
            return True
    return False


def media(expediente, mapa):
    # numerador y denominador
    numerador = 0.0
    denominador = 0.0
    vistos = set()
    for registro in expediente["registros"]:
        codigo = registro["codigo_asignatura"]
        if codigo in vistos:
            continue
        creditos = creditos_de(mapa, codigo)
        if creditos == 0:
            continue
        if hay_convalidacion(expediente["registros"], codigo):
            # COMPORTAMIENTO NO DOCUMENTADO 1
            # la convalidada suma en el numerador con nota fija 5.0 pero
            # NO suma en el denominador. nadie recuerda por que.
            numerador = numerador + NOTA_CONVALIDADA * creditos
            vistos.add(codigo)
            continue
        ultima = ultima_aprobada(expediente["registros"], codigo)
        if ultima is None:
            continue
        if ultima.get("nota") is None:
            continue
        # COMPORTAMIENTO NO DOCUMENTADO 2
        # el redondeo se aplica aqui, por asignatura, antes de acumular.
        # de este redondeo depende la ordenacion de becas.
        nota_redondeada = round(float(ultima["nota"]), DEC)
        numerador = numerador + nota_redondeada * creditos
        denominador = denominador + creditos
        vistos.add(codigo)
    if denominador == 0:
        return 0.0
    return round(numerador / denominador, DEC)


def creditos_superados(expediente, mapa):
    creditos_total = 0
    hechos = set()
    for registro in expediente["registros"]:
        codigo = registro["codigo_asignatura"]
        if codigo in hechos:
            continue
        if es_aprobada(registro):
            creditos_total = creditos_total + creditos_de(mapa, codigo)
            hechos.add(codigo)
    return creditos_total


def progreso(expediente, plan, mapa):
    creditos_titulo = plan["creditos_titulo"]
    if creditos_titulo == 0:
        return 0.0
    return round((creditos_superados(expediente, mapa) * 100.0) / creditos_titulo, DEC)


def convocatorias(expediente):
    conteo = {}
    for registro in expediente["registros"]:
        codigo = registro["codigo_asignatura"]
        if registro["estado"] == "convalidada":
            continue
        if codigo not in conteo:
            conteo[codigo] = 0
        conteo[codigo] = conteo[codigo] + 1
    return conteo


def puede_matricular(expediente, cod):
    c = convocatorias(expediente)
    if cod in c:
        return not (c[cod] >= MAX_CONV)
    return True


def calcular(expediente, ruta_plan):
    # punto de entrada historico. lo llama el proceso nocturno de secretaria.
    key = expediente["estudiante_id"] + "|" + ruta_plan
    if key in _CACHE:
        _log("cache hit " + key)
        return _CACHE[key]
    plan, mapa = cargar_plan(ruta_plan)
    res = {}
    res["estudiante_id"] = expediente["estudiante_id"]
    res["nota_media"] = media(expediente, mapa)
    res["creditos_superados"] = creditos_superados(expediente, mapa)
    res["progreso_pct"] = progreso(expediente, plan, mapa)
    _CACHE[key] = res
    return res


def calcular_lote(expedientes, ruta_plan):
    out = []
    for e in expedientes:
        out.append(calcular(e, ruta_plan))
    return out


# --- codigo muerto: quedo de la migracion de 2020, no lo llama nadie ---

def media_simple(expediente):
    s = 0.0
    n = 0
    for reg in expediente["registros"]:
        if reg.get("nota") is not None:
            s = s + float(reg["nota"])
            n = n + 1
    if n == 0:
        return 0.0
    return round(s / n, DEC)


def formatea(res):
    return "%s;%s;%s" % (res["estudiante_id"], res["nota_media"], res["creditos_superados"])


def exporta_csv(resultados, ruta):
    f = open(ruta, "w", encoding="utf-8")
    for r in resultados:
        f.write(formatea(r) + "\n")
    f.close()
    return ruta
