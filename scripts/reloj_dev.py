"""Reloj de desarrollo (#820) — cambio rápido sin bootstrap de Flask.

Lee/escribe directamente D:\\BDDAT\\instance\\reloj_simulado.txt, el mismo
fichero que `_hoy()` (app/services/plazos.py) y el CLI `flask reloj` (misma
lógica que app/services/reloj_simulado.py, aquí sin depender de la app). Pensado
para cambiar la fecha muchas veces seguidas sin el coste de arrancar Flask
(validar catálogo + SQLALCHEMY_ECHO) en cada invocación.

Uso:
    python scripts/reloj_dev.py show
    python scripts/reloj_dev.py set 2026-09-20
    python scripts/reloj_dev.py reset
    python scripts/reloj_dev.py avanzar 5
    python scripts/reloj_dev.py avanzar 5 --habiles
    python scripts/reloj_dev.py retroceder 3 --habiles

No sustituye a `flask reloj` ni al badge web — los tres tocan el mismo
fichero. El candado DEBUG=True que hace que el servidor real respete ese
fichero lo aplica `_hoy()`, no este script.
"""
import argparse
import os
import sys
from datetime import date, timedelta

BDDAT_DIR = r"D:\BDDAT"
RUTA_FICHERO = os.path.join(BDDAT_DIR, "instance", "reloj_simulado.txt")


def obtener() -> date | None:
    if not os.path.isfile(RUTA_FICHERO):
        return None
    with open(RUTA_FICHERO, "r", encoding="utf-8") as f:
        contenido = f.read().strip()
    return date.fromisoformat(contenido) if contenido else None


def fijar(fecha: date) -> None:
    os.makedirs(os.path.dirname(RUTA_FICHERO), exist_ok=True)
    with open(RUTA_FICHERO, "w", encoding="utf-8") as f:
        f.write(fecha.isoformat())


def borrar() -> None:
    if os.path.isfile(RUTA_FICHERO):
        os.remove(RUTA_FICHERO)


def _cargar_inhabiles(fecha_ini: date, fecha_fin: date) -> frozenset:
    """Replica _obtener_inhabiles_bd de plazos.py, sin pasar por el ORM/app."""
    import psycopg2
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BDDAT_DIR, ".env"))
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL no configurado (.env) — no se puede calcular días hábiles.", file=sys.stderr)
        raise SystemExit(1)

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT fecha FROM dias_inhabiles WHERE fecha >= %s AND fecha <= %s",
            (fecha_ini, fecha_fin),
        )
        return frozenset(row[0] for row in cur.fetchall())


def _es_habil(fecha: date, inhabiles: frozenset) -> bool:
    return fecha.weekday() < 5 and fecha not in inhabiles


def _sumar_dias_habiles(fecha_ini: date, n: int, inhabiles: frozenset) -> date:
    """Mismo bucle que _medir() en plazos.py; n negativo retrocede."""
    paso = timedelta(days=1) if n >= 0 else timedelta(days=-1)
    cursor = fecha_ini
    dias = 0
    objetivo = abs(n)
    while dias < objetivo:
        cursor += paso
        if _es_habil(cursor, inhabiles):
            dias += 1
    return cursor


def _fecha_base() -> date:
    return obtener() or date.today()


def cmd_show(_args):
    activa = obtener()
    if activa:
        print(f"Reloj simulado activo: {activa.isoformat()} ({activa.strftime('%A')})")
    else:
        print(f"Sin reloj simulado — fecha real: {date.today().isoformat()}")


def cmd_set(args):
    fecha = date.fromisoformat(args.fecha)
    fijar(fecha)
    print(f"Reloj simulado fijado a {fecha.isoformat()}")


def cmd_reset(_args):
    borrar()
    print(f"Reloj simulado borrado — fecha real: {date.today().isoformat()}")


def _mover(delta: int, habiles: bool) -> None:
    base = _fecha_base()
    if habiles:
        margen = abs(delta) * 3 + 30
        inhabiles = _cargar_inhabiles(base - timedelta(days=margen), base + timedelta(days=margen))
        nueva = _sumar_dias_habiles(base, delta, inhabiles)
    else:
        nueva = base + timedelta(days=delta)
    fijar(nueva)
    signo = "+" if delta >= 0 else ""
    tipo = "hábiles" if habiles else "naturales"
    print(f"{base.isoformat()} {signo}{delta} días {tipo} -> {nueva.isoformat()}")


def cmd_avanzar(args):
    _mover(args.dias, args.habiles)


def cmd_retroceder(args):
    _mover(-args.dias, args.habiles)


def main():
    parser = argparse.ArgumentParser(description="Reloj de desarrollo BDDAT (#820) — sin bootstrap de Flask.")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("show", help="Muestra la fecha simulada activa").set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="Fija una fecha absoluta (AAAA-MM-DD)")
    p_set.add_argument("fecha")
    p_set.set_defaults(func=cmd_set)

    sub.add_parser("reset", help="Borra la simulación — vuelve a la fecha real").set_defaults(func=cmd_reset)

    p_av = sub.add_parser("avanzar", help="Avanza N días desde la fecha activa (o desde hoy si no hay ninguna)")
    p_av.add_argument("dias", type=int)
    p_av.add_argument("--habiles", action="store_true", help="Cuenta solo días hábiles (salta fines de semana e inhábiles)")
    p_av.set_defaults(func=cmd_avanzar)

    p_re = sub.add_parser("retroceder", help="Retrocede N días desde la fecha activa (o desde hoy si no hay ninguna)")
    p_re.add_argument("dias", type=int)
    p_re.add_argument("--habiles", action="store_true", help="Cuenta solo días hábiles (salta fines de semana e inhábiles)")
    p_re.set_defaults(func=cmd_retroceder)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
