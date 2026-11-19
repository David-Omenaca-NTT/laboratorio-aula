import subprocess
from unittest.mock import patch
from agentes.mcp_aula.servidor import _descargar_junit
from agentes.mcp_aula.servidor import _interpretar_junit


def test_interpretar_junit_con_fallo():
    """Comprueba la interpretación de un informe JUnit con un fallo."""

    xml = """
    <testsuite tests="2" failures="1" errors="0" skipped="0">
        <testcase classname="tests.test_media" name="test_correcto"/>
        <testcase classname="tests.test_media" name="test_incorrecto">
            <failure
                type="AssertionError"
                message="Esperado 7.25, obtenido 116.00"
            >Error en media ponderada</failure>
        </testcase>
    </testsuite>
    """

    resultado = _interpretar_junit(xml)

    assert resultado["disponible"] is True
    assert resultado["total"] == 2
    assert resultado["passed"] == 1
    assert resultado["failed"] == 1
    assert resultado["errors"] == 0
    assert resultado["skipped"] == 0

    assert len(resultado["fallos"]) == 1

    fallo = resultado["fallos"][0]
    assert fallo["test"] == "test_incorrecto"
    assert fallo["tipo"] == "AssertionError"
    assert fallo["categoria"] == "failure"

def test_interpretar_junit_con_error_y_omitido():
    """Distingue errores de ejecución, tests omitidos y tests correctos."""

    xml = """
    <testsuites>
        <testsuite name="pytest" tests="3" failures="0" errors="1" skipped="1">
            <testcase classname="tests.test_aula" name="test_correcto"/>

            <testcase classname="tests.test_aula" name="test_error">
                <error type="RuntimeError" message="Fallo al preparar datos">
                    Error durante la ejecución
                </error>
            </testcase>

            <testcase classname="tests.test_aula" name="test_omitido">
                <skipped message="No aplicable"/>
            </testcase>
        </testsuite>
    </testsuites>
    """

    resultado = _interpretar_junit(xml)

    assert resultado["disponible"] is True
    assert resultado["total"] == 3
    assert resultado["passed"] == 1
    assert resultado["failed"] == 0
    assert resultado["errors"] == 1
    assert resultado["skipped"] == 1

    assert len(resultado["fallos"]) == 1
    assert resultado["fallos"][0]["test"] == "test_error"
    assert resultado["fallos"][0]["tipo"] == "RuntimeError"
    assert resultado["fallos"][0]["categoria"] == "error"

def test_descargar_junit_sin_artifact():
    """Una descarga fallida devuelve diagnóstico sin exponer stderr."""

    respuesta_gh = subprocess.CompletedProcess(
        args=["gh", "run", "download"],
        returncode=1,
        stdout="",
        stderr="Error de descarga: TOKEN_SECRETO_SIMULADO",
    )

    with patch(
        "agentes.mcp_aula.servidor.subprocess.run",
        return_value=respuesta_gh,
    ) as ejecutar:
        resultado = _descargar_junit("44099682194")

    assert resultado["disponible"] is False
    assert resultado["codigo_salida"] == 1
    assert resultado["tipo_error"] == "descarga_fallida"
    assert "motivo" in resultado
    assert "xml" not in resultado

    # El error original no debe aparecer en el resultado.
    assert "TOKEN_SECRETO_SIMULADO" not in str(resultado)

    # La descarga debe identificar explícitamente el repositorio.
    comando = ejecutar.call_args.args[0]

    assert "--repo" in comando
    assert comando[comando.index("--repo") + 1] == (
        "David-Omenaca-NTT/laboratorio-aula"
    )