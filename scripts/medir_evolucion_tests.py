"""Cuenta la evolución semanal de smoke tests vs. tests de feature.

Recorre el historial git de tests/ (fecha de alta real de cada fichero,
`git log --diff-filter=A`) y agrupa por semana ISO (lunes-domingo), con
acumulado. Es la fuente de datos del artefacto "Genealogía de los tests"
(gráfico de barras acumuladas publicado como Claude Artifact) — cuando la
suite crezca y el gráfico se quede desactualizado, re-ejecutar este script
y pegar el bloque `const ... = [...]` que imprime en el <script> del HTML
del artefacto antes de republicarlo. El script no publica nada por sí
mismo: solo recalcula los números.

Uso:
    venv/Scripts/python.exe scripts/medir_evolucion_tests.py
    venv/Scripts/python.exe scripts/medir_evolucion_tests.py --salida docs_prueba/temp/evolucion_tests.json
"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta

EXCLUDE = {"tests/conftest.py", "tests/smoke/conftest.py", "tests/__init__.py", "tests/smoke/__init__.py"}


def fecha_alta_por_fichero():
    """Fecha (más antigua) en que cada fichero de tests/ entró al repo."""
    salida = subprocess.run(
        ["git", "log", "--diff-filter=A", "--name-only", "--pretty=format:@@%ad", "--date=short", "--", "tests"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    ).stdout

    fecha_por_fichero = {}
    fecha_actual = None
    for linea in salida.splitlines():
        if linea.startswith("@@"):
            fecha_actual = linea[2:]
            continue
        linea = linea.strip()
        if not linea or not linea.startswith("tests/") or not linea.endswith(".py"):
            continue
        # Se recorre de más reciente a más antiguo (orden por defecto de git log):
        # sobrescribir sin condición dejar la fecha del commit MÁS ANTIGUO al final.
        fecha_por_fichero[linea] = fecha_actual
    return fecha_por_fichero


def ficheros_vivos_hoy():
    salida = subprocess.run(
        ["git", "ls-files", "tests/*.py"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    ).stdout
    return {f for f in salida.splitlines() if f and f not in EXCLUDE}


def lunes_de_la_semana(d: date) -> date:
    return d - timedelta(days=d.weekday())


def parsear_fecha(s: str) -> date:
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def construir_serie(fecha_por_fichero):
    smoke, feature = {}, {}
    for ruta, fecha in fecha_por_fichero.items():
        if ruta in EXCLUDE:
            continue
        (smoke if ruta.startswith("tests/smoke/") else feature)[ruta] = fecha

    fechas = [parsear_fecha(f) for f in list(smoke.values()) + list(feature.values())]
    semana_min = lunes_de_la_semana(min(fechas))
    semana_max = lunes_de_la_semana(max(fechas))

    semanas = []
    cursor = semana_min
    while cursor <= semana_max:
        semanas.append(cursor)
        cursor += timedelta(days=7)

    def nuevos_por_semana(fechas_dict):
        conteo = defaultdict(int)
        for f in fechas_dict.values():
            conteo[lunes_de_la_semana(parsear_fecha(f))] += 1
        return [conteo[s] for s in semanas]

    nuevos_smoke = nuevos_por_semana(smoke)
    nuevos_feature = nuevos_por_semana(feature)

    acumulado = lambda serie: [sum(serie[:i + 1]) for i in range(len(serie))]

    return {
        "semanas_inicio": [s.isoformat() for s in semanas],
        "nuevos_smoke": nuevos_smoke,
        "nuevos_feature": nuevos_feature,
        "acumulado_smoke": acumulado(nuevos_smoke),
        "acumulado_feature": acumulado(nuevos_feature),
        "total_altas_historicas_smoke": len(smoke),
        "total_altas_historicas_feature": len(feature),
    }


def imprimir_resumen(serie, vivos):
    print(f"Ficheros vivos hoy en tests/: {len(vivos)}")
    print(f"Altas históricas — smoke: {serie['total_altas_historicas_smoke']}  "
          f"feature: {serie['total_altas_historicas_feature']}")
    print()
    print(f"{'semana':10}  {'+smoke':>6}  {'+feat':>6}  {'=smoke':>6}  {'=feat':>6}")
    for i, s in enumerate(serie["semanas_inicio"]):
        print(f"{s:10}  {serie['nuevos_smoke'][i]:6d}  {serie['nuevos_feature'][i]:6d}  "
              f"{serie['acumulado_smoke'][i]:6d}  {serie['acumulado_feature'][i]:6d}")

    print("\n--- Bloque listo para pegar en el <script> del artefacto ---\n")
    print("  var weekStart = " + json.dumps(serie["semanas_inicio"]) + ";")
    print("  var newFeature  = " + json.dumps(serie["nuevos_feature"]) + ";")
    print("  var newSmoke    = " + json.dumps(serie["nuevos_smoke"]) + ";")
    print("  var cumFeature  = " + json.dumps(serie["acumulado_feature"]) + ";")
    print("  var cumSmoke    = " + json.dumps(serie["acumulado_smoke"]) + ";")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", help="Fichero JSON de salida (por defecto: solo stdout)")
    args = parser.parse_args()

    fecha_por_fichero = fecha_alta_por_fichero()
    vivos = ficheros_vivos_hoy()
    serie = construir_serie(fecha_por_fichero)
    serie["vivos_hoy"] = len(vivos)

    imprimir_resumen(serie, vivos)

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump(serie, f, ensure_ascii=False, indent=2)
        print(f"\nJSON guardado en {args.salida}")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    main()
