"""
Tests issue #192 — RequisitoDocumental, CondicionRequisito, DocumentoRequisito
y el helper evaluar_requisitos.

Sin BD ni app context. Valida lógica con stubs.
"""
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

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


def _requisito(tipo_doc_id=1, condiciones=None, orden=1, req_id=None):
    r = MagicMock()
    r.id = req_id or tipo_doc_id
    r.tipo_documento_id = tipo_doc_id
    r.condiciones = condiciones or []
    r.orden = orden
    return r


def _doc_requisito(requisito_id, solicitud_id, documento_id=99):
    dr = MagicMock()
    dr.requisito_id = requisito_id
    dr.solicitud_id = solicitud_id
    dr.documento_id = documento_id
    dr.documento = MagicMock()
    dr.documento.id = documento_id
    return dr


def _solicitud(sol_id=1):
    s = MagicMock()
    s.id = sol_id
    return s


# ---------------------------------------------------------------------------
# Helper para importar evaluar_requisitos parchando las queries
# ---------------------------------------------------------------------------

def _evaluar(requisitos, vinculaciones, sol_id=1):
    """
    Llama a evaluar_requisitos con las tablas parchadas por mocks.

    requisitos:    lista de objetos _requisito()
    vinculaciones: lista de objetos _doc_requisito()
    """
    from app.services.requisitos import evaluar_requisitos

    solicitud = _solicitud(sol_id)

    mock_req_query = MagicMock()
    mock_req_query.filter_by.return_value.order_by.return_value.all.return_value = requisitos

    mock_dr_query = MagicMock()
    mock_dr_query.filter_by.return_value.all.return_value = vinculaciones

    with patch('app.services.requisitos.RequisitoDocumental') as MockReq, \
         patch('app.services.requisitos.DocumentoRequisito') as MockDR:
        MockReq.query = mock_req_query
        MockDR.query = mock_dr_query
        return evaluar_requisitos(solicitud, {})


# ---------------------------------------------------------------------------
# A) Modelos — estructura básica
# ---------------------------------------------------------------------------

class TestModelosRequisitosDocumentales:

    def test_repr_requisito(self):
        from app.models.requisitos_documentales import RequisitoDocumental
        r = MagicMock(spec=RequisitoDocumental)
        r.id = 1
        r.tipo_documento_id = 3
        assert RequisitoDocumental.__repr__(r) == '<RequisitoDocumental id=1 tipo_doc=3>'

    def test_repr_condicion(self):
        from app.models.requisitos_documentales import CondicionRequisito
        c = MagicMock(spec=CondicionRequisito)
        c.id = 5
        c.requisito_id = 2
        c.variable = _variable_stub('tipo_solicitud')
        c.operador = 'EQ'
        c.valor = 'AAP'
        assert 'tipo_solicitud' in CondicionRequisito.__repr__(c)
        assert 'EQ' in CondicionRequisito.__repr__(c)

    def test_repr_documento_requisito(self):
        from app.models.requisitos_documentales import DocumentoRequisito
        dr = MagicMock(spec=DocumentoRequisito)
        dr.id = 7
        dr.requisito_id = 1
        dr.solicitud_id = 2
        dr.documento_id = 99
        assert 'req=1' in DocumentoRequisito.__repr__(dr)
        assert 'sol=2' in DocumentoRequisito.__repr__(dr)


# ---------------------------------------------------------------------------
# B) Variable tipo_expediente
# ---------------------------------------------------------------------------

def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no registrada'
    return fn


class _StubTipoExpediente:
    def __init__(self, tipo): self.tipo = tipo


class _StubExpediente:
    def __init__(self, tipo_exp): self.tipo_expediente = tipo_exp


class _StubCtx:
    def __init__(self, tipo_exp_str=None):
        te = _StubTipoExpediente(tipo_exp_str) if tipo_exp_str else None
        self.expediente = _StubExpediente(te)


class TestVariableTipoExpediente:

    def test_registrada(self):
        _get_variable('tipo_expediente')

    def test_distribucion(self):
        fn = _get_variable('tipo_expediente')
        assert fn(_StubCtx('Distribucion')) == 'Distribucion'

    def test_renovable(self):
        fn = _get_variable('tipo_expediente')
        assert fn(_StubCtx('Renovable')) == 'Renovable'

    def test_sin_tipo_expediente(self):
        fn = _get_variable('tipo_expediente')
        assert fn(_StubCtx(None)) is None

    def test_expediente_none(self):
        fn = _get_variable('tipo_expediente')
        ctx = MagicMock()
        ctx.expediente = None
        assert fn(ctx) is None


# ---------------------------------------------------------------------------
# C) evaluar_requisitos — catálogo vacío
# ---------------------------------------------------------------------------

class TestEvaluarRequisitosVacio:

    def test_sin_requisitos_todos_cubiertos(self):
        """Sin requisitos en el catálogo → todos_cubiertos=True, items vacío."""
        resultado = _evaluar(requisitos=[], vinculaciones=[])
        assert resultado['todos_cubiertos'] is True
        assert resultado['items'] == []
        assert resultado['error'] is False


# ---------------------------------------------------------------------------
# D) evaluar_requisitos — requisito universal (sin condiciones)
# ---------------------------------------------------------------------------

class TestRequisitoUniversal:

    def test_universal_sin_cubrir(self):
        """Requisito sin condiciones, sin documento asignado → cubierto=False."""
        req = _requisito(tipo_doc_id=1, condiciones=[], req_id=10)
        resultado = _evaluar([req], [])
        assert resultado['todos_cubiertos'] is False
        assert len(resultado['items']) == 1
        item = resultado['items'][0]
        assert item['cubierto'] is False
        assert item['documento'] is None

    def test_universal_cubierto(self):
        """Requisito universal con documento asignado → cubierto=True."""
        req = _requisito(tipo_doc_id=1, condiciones=[], req_id=10)
        vl = _doc_requisito(requisito_id=10, solicitud_id=1)
        resultado = _evaluar([req], [vl])
        assert resultado['todos_cubiertos'] is True
        assert resultado['items'][0]['cubierto'] is True
        assert resultado['items'][0]['documento'] is not None


# ---------------------------------------------------------------------------
# E) evaluar_requisitos — condición EQ
# ---------------------------------------------------------------------------

class TestCondicionEQ:

    def test_condicion_eq_cumplida(self):
        """EQ con valor correcto → requisito aplica."""
        cond = _condicion('tipo_solicitud', 'EQ', 'AAP')
        req = _requisito(tipo_doc_id=2, condiciones=[cond], req_id=20)
        resultado = _evaluar([req], [], sol_id=1)
        # El dict de variables está vacío, pero parchamos evaluar_requisitos internamente
        # Necesitamos variables reales para que la condición evalúe
        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            res = evaluar_requisitos(solicitud, {'tipo_solicitud': 'AAP'})

        assert len(res['items']) == 1
        assert res['items'][0]['cubierto'] is False

    def test_condicion_eq_no_cumplida(self):
        """EQ con valor distinto → requisito no aplica → lista vacía."""
        cond = _condicion('tipo_solicitud', 'EQ', 'AAP')
        req = _requisito(tipo_doc_id=2, condiciones=[cond], req_id=20)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            res = evaluar_requisitos(solicitud, {'tipo_solicitud': 'AAC'})

        assert res['items'] == []
        assert res['todos_cubiertos'] is True


# ---------------------------------------------------------------------------
# F) evaluar_requisitos — condición IN
# ---------------------------------------------------------------------------

class TestCondicionIN:

    def _run(self, valor_var):
        cond = _condicion('tipo_solicitud', 'IN', ['AAP', 'AAC'])
        req = _requisito(tipo_doc_id=3, condiciones=[cond], req_id=30)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            return evaluar_requisitos(solicitud, {'tipo_solicitud': valor_var})

    def test_in_cumplido_aap(self):
        res = self._run('AAP')
        assert len(res['items']) == 1

    def test_in_cumplido_aac(self):
        res = self._run('AAC')
        assert len(res['items']) == 1

    def test_in_no_cumplido_dup(self):
        res = self._run('DUP')
        assert res['items'] == []


# ---------------------------------------------------------------------------
# G) evaluar_requisitos — AND de condiciones
# ---------------------------------------------------------------------------

class TestCondicionAND:

    def test_dos_condiciones_ambas_cumplidas(self):
        """AND: tipo_solicitud=AAP Y tipo_expediente=Renovable → aplica."""
        c1 = _condicion('tipo_solicitud', 'EQ', 'AAP', var_id=1)
        c2 = _condicion('tipo_expediente', 'EQ', 'Renovable', var_id=2)
        req = _requisito(tipo_doc_id=4, condiciones=[c1, c2], req_id=40)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            res = evaluar_requisitos(
                solicitud,
                {'tipo_solicitud': 'AAP', 'tipo_expediente': 'Renovable'}
            )
        assert len(res['items']) == 1

    def test_dos_condiciones_una_falla(self):
        """AND: tipo_solicitud=AAP OK pero tipo_expediente=Distribucion falla → no aplica."""
        c1 = _condicion('tipo_solicitud', 'EQ', 'AAP', var_id=1)
        c2 = _condicion('tipo_expediente', 'EQ', 'Renovable', var_id=2)
        req = _requisito(tipo_doc_id=4, condiciones=[c1, c2], req_id=40)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            res = evaluar_requisitos(
                solicitud,
                {'tipo_solicitud': 'AAP', 'tipo_expediente': 'Distribucion'}
            )
        assert res['items'] == []


# ---------------------------------------------------------------------------
# H) evaluar_requisitos — OR implícito (dos requisitos, mismo tipo_doc)
# ---------------------------------------------------------------------------

class TestOR:

    def test_or_solo_uno_aplica(self):
        """
        Dos filas para el mismo tipo_doc con condiciones distintas (OR).
        La solicitud cumple solo la condición de la fila B.
        El técnico ve solo 1 requisito.
        """
        c_a = _condicion('tipo_solicitud', 'EQ', 'AAP', var_id=1)
        req_a = _requisito(tipo_doc_id=5, condiciones=[c_a], req_id=50)

        c_b = _condicion('tipo_solicitud', 'EQ', 'AAC', var_id=1)
        req_b = _requisito(tipo_doc_id=5, condiciones=[c_b], req_id=51)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req_a, req_b]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            res = evaluar_requisitos(solicitud, {'tipo_solicitud': 'AAC'})

        assert len(res['items']) == 1
        assert res['items'][0]['requisito'] is req_b


# ---------------------------------------------------------------------------
# I) evaluar_requisitos — error de BD → degradado permisivo
# ---------------------------------------------------------------------------

class TestErrorBD:

    def test_tabla_no_disponible_devuelve_degradado(self):
        """OperationalError en la query → todos_cubiertos=True, error=True."""
        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch
        from sqlalchemy.exc import OperationalError

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.side_effect = OperationalError(
            'stmt', 'params', Exception('tabla no existe')
        )

        with patch('app.services.requisitos.RequisitoDocumental') as MR:
            MR.query = mock_req_q
            res = evaluar_requisitos(solicitud, {})

        assert res['todos_cubiertos'] is True
        assert res['error'] is True
        assert res['items'] == []


# ---------------------------------------------------------------------------
# J) evaluar_requisitos — operadores numéricos y de rango (#601)
# ---------------------------------------------------------------------------

class TestOperadoresNumericos:
    """Antes de #601, GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN no estaban soportados
    y _evaluar_condicion caía al operador desconocido (ver TestOperadorDesconocido)."""

    def _run(self, operador, valor_ref, valor_var):
        cond = _condicion('tension_nominal_kv', operador, valor_ref)
        req = _requisito(tipo_doc_id=6, condiciones=[cond], req_id=60)

        from app.services.requisitos import evaluar_requisitos
        from unittest.mock import MagicMock, patch

        solicitud = _solicitud(1)
        mock_req_q = MagicMock()
        mock_req_q.filter_by.return_value.order_by.return_value.all.return_value = [req]
        mock_dr_q = MagicMock()
        mock_dr_q.filter_by.return_value.all.return_value = []

        with patch('app.services.requisitos.RequisitoDocumental') as MR, \
             patch('app.services.requisitos.DocumentoRequisito') as MDR:
            MR.query = mock_req_q
            MDR.query = mock_dr_q
            return evaluar_requisitos(solicitud, {'tension_nominal_kv': valor_var})

    def test_gt_cumplido(self):
        assert len(self._run('GT', 30, 45)['items']) == 1

    def test_gt_no_cumplido(self):
        assert self._run('GT', 30, 30)['items'] == []

    def test_gte_cumplido_igual(self):
        assert len(self._run('GTE', 30, 30)['items']) == 1

    def test_gte_no_cumplido(self):
        assert self._run('GTE', 30, 29)['items'] == []

    def test_lt_cumplido(self):
        assert len(self._run('LT', 30, 15)['items']) == 1

    def test_lt_no_cumplido(self):
        assert self._run('LT', 30, 30)['items'] == []

    def test_lte_cumplido_igual(self):
        assert len(self._run('LTE', 30, 30)['items']) == 1

    def test_lte_no_cumplido(self):
        assert self._run('LTE', 30, 31)['items'] == []

    def test_between_cumplido(self):
        assert len(self._run('BETWEEN', [10, 50], 30)['items']) == 1

    def test_between_no_cumplido(self):
        assert self._run('BETWEEN', [10, 50], 60)['items'] == []

    def test_not_between_cumplido(self):
        assert len(self._run('NOT_BETWEEN', [10, 50], 60)['items']) == 1

    def test_not_between_no_cumplido(self):
        assert self._run('NOT_BETWEEN', [10, 50], 30)['items'] == []


# ---------------------------------------------------------------------------
# K) evaluar_requisitos — operador desconocido (#601, regresión)
# ---------------------------------------------------------------------------

class TestOperadorDesconocido:

    def test_operador_desconocido_no_aplica(self):
        """
        Antes de #601, un operador desconocido hacía que _evaluar_condicion
        devolviera True (bug: la condición se daba por cumplida). Ahora debe
        tratarse como no cumplida — el requisito no aparece en el checklist
        en vez de aparecer siempre.
        """
        cond = _condicion('tension_nominal_kv', 'OPERADOR_INVENTADO', 30)
        req = _requisito(tipo_doc_id=7, condiciones=[cond], req_id=70)
        resultado = _evaluar([req], [])
        assert resultado['items'] == []
