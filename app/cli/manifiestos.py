"""Comando CLI para rehacer los manifiestos de los expedientes (ADR-050 §H, #1007).

Uso:
    flask manifiestos            # todos
    flask manifiestos AT-123     # uno (vale también «123»)

Solo reescribe los que cambian. Es la forma de rehacerlos hasta que la fase 2b los
programe. Para reconstruir las carpetas a partir de ellos, sin BDDAT:
`python -m exportador --help`.
"""
import click
from flask.cli import with_appcontext


@click.command('manifiestos')
@click.argument('expediente', required=False)
@with_appcontext
def manifiestos(expediente):
    """Rehace el manifiesto de un expediente (AT-N) o, sin argumento, los de todos."""
    from app.models.expedientes import Expediente
    from app.services.almacenamiento.manifiestos import (
        ManifiestosNoDisponibles, Resultado, escribir, rehacer_todos,
    )

    try:
        if expediente:
            numero = expediente.upper().removeprefix('AT-')
            if not numero.isdigit():
                raise click.BadParameter(f'{expediente!r}: se espera AT-N o N')
            exp = Expediente.query.filter_by(numero_at=int(numero)).first()
            if exp is None:
                click.echo(f'No existe el expediente AT-{numero}.', err=True)
                raise SystemExit(1)
            resultados = [Resultado(f'AT-{exp.numero_at}', escribir(exp))]
        else:
            resultados = rehacer_todos()

        reescritos = sin_cambios = errores = 0
        for r in resultados:
            if r.error:
                errores += 1
                click.echo(f'{r.expediente}: ERROR {r.error}', err=True)
            elif r.reescrito:
                reescritos += 1
                click.echo(f'{r.expediente}: reescrito')
            else:
                sin_cambios += 1
    except ManifiestosNoDisponibles as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)

    click.echo(f'{reescritos} reescritos, {sin_cambios} sin cambios, {errores} con error.')
    if errores:
        raise SystemExit(1)
