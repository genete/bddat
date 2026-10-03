"""
Tests #1014 — `.claude/hooks/reglas_asserts_guard.py`: el commit que cambia un
`assert` de un test de otro issue nombra la decisión que cambia.

Se ejecuta el hook como lo ejecuta Claude Code (JSON por stdin, decisión por
stdout) contra un repositorio git temporal con cambios preparados: no se hace
ningún commit, el hook solo lee el diff.

Fallo silencioso que evita: el guard está hecho para dejar pasar ante cualquier
error propio, así que si cambia la salida de `git diff` o se rompe el análisis
del comando, deja pasar todo; los asserts vuelven a adaptarse sin decir qué
decisión cambió y nadie se entera de que el hook ya no vigila.
"""
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[1] / '.claude' / 'hooks' / 'reglas_asserts_guard.py'

TEST_100 = '''def test_suma():
    assert suma(1, 1) == 2
    assert resta(2, 1) == 1
'''
SMOKE = '''def test_smoke_listado(client):
    assert client.get('/listado').status_code == 200
'''
RETIRADO = ('Test retirado: no vigila nada de la lista «Sí» del README §3, '
            'solo repetía el texto del aviso')


def _git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


def _escribir(repo, cambios):
    for ruta, contenido in cambios.items():
        fichero = repo / ruta
        if contenido is None:
            fichero.unlink()
        else:
            fichero.parent.mkdir(parents=True, exist_ok=True)
            fichero.write_text(contenido, encoding='utf-8')


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    _git(repo, 'init', '-q')
    _git(repo, 'config', 'user.email', 'test@bddat')
    _git(repo, 'config', 'user.name', 'test')
    _escribir(repo, {'tests/test_100_suma.py': TEST_100,
                     'tests/smoke/test_smoke_listado.py': SMOKE})
    _git(repo, 'add', '-A')
    _git(repo, 'commit', '-q', '-m', 'inicial')
    return repo


def _preparar(repo, cambios):
    _escribir(repo, cambios)
    _git(repo, 'add', '-A')


def _guard(repo, comando):
    """Razón de la denegación, o None si el hook deja pasar.

    Lo lanza como Claude Code en Windows: JSON en UTF-8 sin escapar por stdin y el
    stdin/stdout del hook en cp1252 (la codificación de una consola de Windows). Se
    fuerza con PYTHONIOENCODING —que gana al modo UTF-8 de Python— para que el
    entorno sea el mismo en Linux y en el PC.
    """
    payload = {'tool_name': 'Bash', 'tool_input': {'command': comando}, 'cwd': str(repo)}
    entorno = {**os.environ, 'PYTHONIOENCODING': 'cp1252'}
    r = subprocess.run([sys.executable, str(GUARD)], env=entorno, check=True,
                       input=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                       capture_output=True)
    salida = r.stdout.decode('utf-8')
    if not salida.strip():
        return None
    return json.loads(salida)['hookSpecificOutput']['permissionDecisionReason']


def _commit(repo, mensaje, opciones=''):
    return _guard(repo, f'git -C {shlex.quote(str(repo))} commit {opciones} -m {shlex.quote(mensaje)}')


@pytest.mark.parametrize('mensaje, deniega', [
    ('[TEST] #200 Ajusta la suma', True),
    ('[TEST] #200 Ajusta la suma\n\nDecisión que cambia: ADR-050 §M', False),
    ('[TEST] #200 Ajusta la suma\n\nDecisión que cambia: #931', False),
    ('[TEST] #200 Ajusta la suma\n\nDecisión que cambia: porque sí', True),
    ('[TEST] #100 Ajusta la suma', False),
    # citar el issue del fichero solo en el cuerpo no lo hace suyo (bc301dca y test_885)
    ('[MODELO] #200 Generaliza la guarda\n\nAntes solo la tenía #100.', True),
    # «Á» en UTF-8 (C3 81) lleva un byte que cp1252 no define: leído con la consola, el
    # hook no podía ni decodificar la entrada y dejaba pasar el commit sin mirarlo
    ('[TEST] #200 Ángel ajusta la suma', True),
])
def test_assert_cambiado_exige_nombrar_la_decision(repo, mensaje, deniega):
    _preparar(repo, {'tests/test_100_suma.py': TEST_100.replace('== 2', '== 3')})
    razon = _commit(repo, mensaje)
    assert (razon is not None) == deniega
    if deniega:
        assert 'tests/test_100_suma.py' in razon


def test_lee_el_mensaje_de_un_fichero(repo, tmp_path):
    """Es el patrón que exige REGLAS_BASH (`commit -F fichero`)."""
    _preparar(repo, {'tests/test_100_suma.py': TEST_100.replace('== 2', '== 3')})
    fichero = tmp_path / 'msg.txt'
    fichero.write_text('[TEST] #200 Ajusta\n\nDecisión que cambia: ADR-050 §M\n', encoding='utf-8')
    comando = f'git -C {shlex.quote(str(repo))} add -A && git -C {shlex.quote(str(repo))} commit -F {shlex.quote(str(fichero))}'
    assert _guard(repo, comando) is None


def test_smoke_incluidos(repo):
    _preparar(repo, {'tests/smoke/test_smoke_listado.py': SMOKE.replace('200', '403')})
    assert _commit(repo, '[TEST] #200 El listado pide rol') is not None


def test_borrar_un_fichero_de_test_exige_decir_por_que(repo):
    _preparar(repo, {'tests/test_100_suma.py': None})
    assert _commit(repo, '[TEST] #200 Retira test_100') is not None
    assert _commit(repo, f'[TEST] #200 Retira test_100\n\n{RETIRADO}') is None


@pytest.mark.parametrize('cambios', [
    # reformateado: mismas líneas salvo espacios
    {'tests/test_100_suma.py': TEST_100.replace('suma(1, 1) == 2', 'suma(1,1)==2')},
    # movido a otro fichero (el de origen sigue vivo: no es un renombrado)
    {'tests/test_100_suma.py': 'def test_otra():\n    assert cero() == 0\n',
     'tests/test_300_aritmetica.py': TEST_100},
    # test nuevo en un fichero nuevo
    {'tests/test_300_resta.py': 'def test_resta():\n    assert resta(3, 1) == 2\n'},
], ids=['reformateado', 'movido', 'nuevo'])
def test_sin_cambio_de_expectativa_no_pide_nada(repo, cambios):
    _preparar(repo, cambios)
    assert _commit(repo, '[TEST] #200 Ordena tests') is None


def test_con_a_mira_tambien_lo_no_preparado(repo):
    _escribir(repo, {'tests/test_100_suma.py': TEST_100.replace('== 2', '== 3')})
    assert _commit(repo, '[TEST] #200 Ajusta') is None  # nada preparado
    assert _commit(repo, '[TEST] #200 Ajusta', opciones='-a') is not None
    assert _guard(repo, f'git -C {shlex.quote(str(repo))} commit -am "[TEST] #200 Ajusta"') is not None


def test_al_cerrar_un_merge_no_pide_nada(repo):
    _preparar(repo, {'tests/test_100_suma.py': TEST_100.replace('== 2', '== 3')})
    cabeza = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True, check=True).stdout
    (repo / '.git' / 'MERGE_HEAD').write_text(cabeza, encoding='utf-8')
    assert _commit(repo, "Merge branch 'develop'") is None


def test_otros_comandos_no_se_miran(repo):
    _preparar(repo, {'tests/test_100_suma.py': TEST_100.replace('== 2', '== 3')})
    assert _guard(repo, f'git -C {shlex.quote(str(repo))} status') is None
