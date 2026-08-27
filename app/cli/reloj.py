"""Comandos CLI para el reloj de desarrollo (#820).

Uso:
    flask reloj set 2026-09-15
    flask reloj show
    flask reloj clear

Fija la fecha "hoy" que usa el motor de plazos (`_hoy()` en
app/services/plazos.py) sin tocar el reloj real del sistema. Solo tiene
efecto si el servidor Flask corre con DEBUG=True (ProductionConfig.DEBUG =
False lo ignora siempre) — ver app/services/reloj_simulado.py.

Nota: este comando no informa de forma fiable si DEBUG está activo en el
servidor real. Flask reescribe `current_app.debug` en cada invocación CLI
según la variable de entorno `FLASK_DEBUG` (independiente de `FLASK_ENV`,
que es lo que de verdad decide `DevelopmentConfig`/`ProductionConfig`), así
que ese valor aquí no refleja al proceso `python run.py` que sí aplica el
candado.
"""
from datetime import date

import click
from flask.cli import with_appcontext


@click.group()
def reloj():
    """Reloj de desarrollo — fecha "hoy" simulada para el motor de plazos."""


@reloj.command('set')
@click.argument('fecha')
@with_appcontext
def set_fecha(fecha):
    """Fija la fecha simulada (formato AAAA-MM-DD)."""
    from app.services.reloj_simulado import fijar

    try:
        f = date.fromisoformat(fecha)
    except ValueError:
        click.echo(f'Fecha inválida: {fecha!r} (formato esperado AAAA-MM-DD)', err=True)
        raise SystemExit(1)

    fijar(f)
    click.echo(f'Reloj simulado fijado a {f.isoformat()}.')
    click.echo('Efectivo solo si el servidor Flask corre con DEBUG=True (desarrollo).')


@reloj.command('clear')
@with_appcontext
def clear_fecha():
    """Borra la fecha simulada — el motor vuelve a usar la fecha real."""
    from app.services.reloj_simulado import borrar

    borrar()
    click.echo('Reloj simulado borrado — usando fecha real del sistema.')


@reloj.command('show')
@with_appcontext
def show_fecha():
    """Muestra la fecha simulada fijada en el fichero, si hay alguna."""
    from app.services.reloj_simulado import obtener

    simulada = obtener()
    if simulada:
        click.echo(f'Reloj simulado fijado: {simulada.isoformat()} (efectivo solo con DEBUG=True).')
    else:
        click.echo('Sin reloj simulado — usando fecha real del sistema.')
