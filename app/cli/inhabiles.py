"""Comandos CLI para gestión del calendario de días inhábiles.

Uso:
    flask inhabiles importar --year 2027
    flask inhabiles importar --year 2027 --province CÁDIZ --municipio CÁDIZ
    flask inhabiles importar --year 2027 --dry-run

Fuente: API pública de la Junta de Andalucía.
Documentación: docs/guias/GUIA_ADMINISTRACION.md
"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import date

import click
from flask.cli import with_appcontext

log = logging.getLogger(__name__)

_API_BASE = 'https://www.juntadeandalucia.es/ssdigitales/datasets/work-calendar'
_ENDPOINT  = '/work-calendar/get/search_calendar_weekends'

# Mapping de (province, municipality) de la API → código de AmbitoInhabilidad
# Las entradas con province/municipality vacíos son nacionales+autonómicos andaluces.
_AMBITO_VACIO = 'AUTONOMICO_AND'


def _codigo_ambito(province: str, municipality: str, prov_param: str, mun_param: str) -> str:
    """Devuelve el código de ámbito según los valores del registro de la API."""
    if not province and not municipality:
        return 'AUTONOMICO_AND'
    p = province.upper().replace(' ', '_')[:10]
    m = municipality.upper().replace(' ', '_')[:10]
    if municipality:
        return f'LOCAL_{p}_{m}'
    return f'PROVINCIAL_{p}'


def _obtener_o_crear_ambito(codigo: str, db):
    """Devuelve AmbitoInhabilidad con ese código, creándolo si no existe."""
    from app.models.ambitos_inhabilidad import AmbitoInhabilidad
    ambito = AmbitoInhabilidad.query.filter_by(codigo=codigo).first()
    if ambito is None:
        nombre = codigo.replace('_', ' ').title()
        ambito = AmbitoInhabilidad(codigo=codigo, nombre=nombre)
        db.session.add(ambito)
        db.session.flush()
        click.echo(f'  [nuevo ámbito] {codigo}')
    return ambito


def _fetch_inhabiles(year: int, province: str, municipio: str) -> list:
    """Llama a la API de la Junta y devuelve los registros del año."""
    params = urllib.parse.urlencode({
        'municipality': municipio,
        'province': province,
        'year': str(year),
    })
    url = f'{_API_BASE}{_ENDPOINT}?{params}'
    click.echo(f'  GET {url}')
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    # La API devuelve {"results": [...]} o directamente una lista
    if isinstance(data, dict):
        return data.get('results', data.get('result', []))
    return data


def _parse_fecha(date_int: int) -> date:
    """Convierte entero YYYYMMDD a date."""
    s = str(date_int)
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


@click.group()
def inhabiles():
    """Gestión del calendario de días inhábiles."""


@inhabiles.command('importar')
@click.option('--year', default=None, type=int,
              help='Año a importar. Defecto: año siguiente al actual.')
@click.option('--province', default='CÁDIZ', show_default=True,
              help='Provincia (mayúsculas exactas según la API).')
@click.option('--municipio', default='CÁDIZ', show_default=True,
              help='Municipio (mayúsculas exactas según la API).')
@click.option('--dry-run', is_flag=True, default=False,
              help='Mostrar lo que se importaría sin modificar la BD.')
@with_appcontext
def importar(year, province, municipio, dry_run):
    """Importa días inhábiles desde la API de la Junta de Andalucía.

    Por defecto importa el año siguiente al actual con ámbito Cádiz capital.
    Ejecutar cada año en noviembre tras la publicación del BOJA de festivos.

    Ejemplos:\n
        flask inhabiles importar\n
        flask inhabiles importar --year 2027\n
        flask inhabiles importar --year 2027 --dry-run
    """
    from app import db
    from app.models.dias_inhabiles import DiaInhabil

    year_importar = year or (date.today().year + 1)
    click.echo(f'Importando año {year_importar} (province={province}, municipio={municipio})')
    if dry_run:
        click.echo('  [DRY RUN — no se modificará la BD]')

    try:
        registros = _fetch_inhabiles(year_importar, province, municipio)
    except Exception as exc:
        click.echo(f'ERROR al llamar a la API: {exc}', err=True)
        raise SystemExit(1)

    # Deduplicar por date (la API puede repetir autonómicos al consultar con municipio)
    vistos: set[int] = set()
    festivos = []
    for r in registros:
        d = r.get('date')
        if d in vistos:
            continue
        vistos.add(d)
        fecha = _parse_fecha(d)
        # Excluir sábados (5) y domingos (6) — el motor los trata aparte
        if fecha.weekday() >= 5:
            continue
        festivos.append((fecha, r.get('description', ''), r.get('province', ''), r.get('municipality', '')))

    click.echo(f'  {len(festivos)} festivos laborables recibidos (excluidos fines de semana)')

    if dry_run:
        for fecha, desc, prov, mun in sorted(festivos):
            codigo = _codigo_ambito(prov, mun, province, municipio)
            click.echo(f'    {fecha}  [{codigo}]  {desc}')
        return

    insertados = actualizados = 0
    for fecha, desc, prov, mun in festivos:
        codigo = _codigo_ambito(prov, mun, province, municipio)
        ambito = _obtener_o_crear_ambito(codigo, db)

        existente = DiaInhabil.query.filter_by(fecha=fecha, ambito_id=ambito.id).first()
        if existente:
            if existente.descripcion != desc:
                existente.descripcion = desc
                actualizados += 1
        else:
            db.session.add(DiaInhabil(fecha=fecha, descripcion=desc, ambito_id=ambito.id))
            insertados += 1

    db.session.commit()
    click.echo(f'  Insertados: {insertados}  Actualizados: {actualizados}')
    click.echo('Importación completada.')
