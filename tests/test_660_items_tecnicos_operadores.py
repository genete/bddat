"""
Tests #660 — items_tecnicos.py soporta los 12 operadores del catálogo compartido.

Sin BD ni app context. Valida lógica con stubs — mismo patrón que
test_192_requisitos_documentales.py (evaluar_requisitos), aplicado aquí a
evaluar_items_tecnicos. Cubre solo lo que #660 corrige: antes de este fix,
_evaluar_condicion en items_tecnicos.py reimplementaba su propio evaluador
(copia exacta del bug de #601 en requisitos.py) y solo soportaba
EQ/NEQ/IN/NOT_IN/IS_NULL/NOT_NULL — GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN se
daban por cumplidos en vez de evaluarse.
"""
from unittest.mock import MagicMock, patch


def _variable_stub(nombre, id=1):
    v = MagicMock()
    v.nombre = nombre
    v.id = id
    return v


def _condicion(variable_nombre, operador, valor, orden=1, var_id=1):
    c = MagicMock()
    c.variable = _variable_stub(variable_nombre, id=var_id)
    c.operador = operador
    c.valor = valor
    c.orden = orden
    c.id = var_id
    return c


def _item(condiciones=None, orden=1, item_id=1):
    i = MagicMock()
    i.id = item_id
    i.condiciones = condiciones or []
    i.orden = orden
    return i


def _solicitud(sol_id=1):
    s = MagicMock()
    s.id = sol_id
    return s


def _run(operador, valor_ref, valor_var, nombre_var='tension_nominal_kv'):
    """Evalúa evaluar_items_tecnicos con un único ítem con una condición."""
    from app.services.items_tecnicos import evaluar_items_tecnicos

    cond = _condicion(nombre_var, operador, valor_ref)
    item = _item(condiciones=[cond], item_id=1)
    solicitud = _solicitud(1)

    mock_item_q = MagicMock()
    mock_item_q.filter_by.return_value.order_by.return_value.all.return_value = [item]
    mock_cob_q = MagicMock()
    mock_cob_q.filter_by.return_value.all.return_value = []

    with patch('app.services.items_tecnicos.ItemTecnico') as MI, \
         patch('app.services.items_tecnicos.CoberturaItemTecnico') as MC:
        MI.query = mock_item_q
        MC.query = mock_cob_q
        return evaluar_items_tecnicos(solicitud, {nombre_var: valor_var})


# ---------------------------------------------------------------------------
# A) evaluar_items_tecnicos — operadores numéricos y de rango
# ---------------------------------------------------------------------------

class TestOperadoresNumericos:

    def test_gt_cumplido(self):
        assert len(_run('GT', 30, 45)['items']) == 1

    def test_gt_no_cumplido(self):
        assert _run('GT', 30, 30)['items'] == []

    def test_gte_cumplido_igual(self):
        assert len(_run('GTE', 30, 30)['items']) == 1

    def test_gte_no_cumplido(self):
        assert _run('GTE', 30, 29)['items'] == []

    def test_lt_cumplido(self):
        assert len(_run('LT', 30, 15)['items']) == 1

    def test_lt_no_cumplido(self):
        assert _run('LT', 30, 30)['items'] == []

    def test_lte_cumplido_igual(self):
        assert len(_run('LTE', 30, 30)['items']) == 1

    def test_lte_no_cumplido(self):
        assert _run('LTE', 30, 31)['items'] == []

    def test_between_cumplido(self):
        assert len(_run('BETWEEN', [10, 50], 30)['items']) == 1

    def test_between_no_cumplido(self):
        assert _run('BETWEEN', [10, 50], 60)['items'] == []

    def test_not_between_cumplido(self):
        assert len(_run('NOT_BETWEEN', [10, 50], 60)['items']) == 1

    def test_not_between_no_cumplido(self):
        assert _run('NOT_BETWEEN', [10, 50], 30)['items'] == []


# ---------------------------------------------------------------------------
# B) evaluar_items_tecnicos — operador desconocido (regresión)
# ---------------------------------------------------------------------------

class TestOperadorDesconocido:

    def test_operador_desconocido_no_aplica(self):
        """
        Antes de #660, un operador desconocido hacía que _evaluar_condicion
        devolviera True (bug: la condición se daba por cumplida). Ahora debe
        tratarse como no cumplida — el ítem no aparece en el checklist en vez
        de aparecer siempre.
        """
        resultado = _run('OPERADOR_INVENTADO', 30, 30)
        assert resultado['items'] == []
