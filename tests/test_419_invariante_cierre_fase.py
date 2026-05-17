"""Tests de _check_cierre_fase — invariante #419.

Cubre los tres casos del check:
  - Resultado DESFAVORABLE → siempre permitido (sin consulta BD)
  - Resultado no-desfavorable + diagnóstico sin consumir → bloqueo
  - Resultado no-desfavorable + sin diagnósticos sin consumir → paso limpio
"""
from unittest.mock import MagicMock, patch


def _make_query_chain(first_returns):
    q = MagicMock()
    q.join.return_value = q
    q.filter.return_value = q
    q.exists.return_value = MagicMock()
    q.first.side_effect = list(first_returns)
    return q


class TestCheckCierreFase:

    def test_resultado_desfavorable_nunca_bloquea(self, app):
        """Con resultado DESFAVORABLE no se ejecuta la query y nunca bloquea."""
        from app.services.invariantes_esftt import _check_cierre_fase
        with app.app_context():
            resultado = _check_cierre_fase(fase_id=99, codigo_resultado='DESFAVORABLE')
        assert resultado is None

    def test_diagnostico_sin_consumir_bloquea(self, app):
        """La query encuentra diagnóstico desfavorable sin consumir → bloqueo."""
        from app.services.invariantes_esftt import _check_cierre_fase
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                mock_db.aliased.return_value = MagicMock()
                mock_db.and_.return_value = MagicMock()
                q = _make_query_chain([MagicMock()])
                mock_db.session.query.return_value = q
                resultado = _check_cierre_fase(fase_id=99, codigo_resultado='FAVORABLE')
        assert resultado is not None
        assert resultado.permitido is False
        assert 'desfavorable' in resultado.norma_compilada.lower()

    def test_diagnostico_consumido_no_bloquea(self, app):
        """La query no encuentra diagnóstico sin consumir → paso limpio."""
        from app.services.invariantes_esftt import _check_cierre_fase
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                mock_db.aliased.return_value = MagicMock()
                mock_db.and_.return_value = MagicMock()
                q = _make_query_chain([None])
                mock_db.session.query.return_value = q
                resultado = _check_cierre_fase(fase_id=99, codigo_resultado='FAVORABLE')
        assert resultado is None

    def test_cualquier_resultado_no_desfavorable_bloquea(self, app):
        """FAVORABLE_CONDICIONADO, NO_PROCEDE, DESISTIDA y ARCHIVADA también bloquean."""
        from app.services.invariantes_esftt import _check_cierre_fase
        for codigo in ('FAVORABLE_CONDICIONADO', 'NO_PROCEDE', 'DESISTIDA', 'ARCHIVADA'):
            with app.app_context():
                with patch('app.services.invariantes_esftt.db') as mock_db:
                    mock_db.aliased.return_value = MagicMock()
                    mock_db.and_.return_value = MagicMock()
                    q = _make_query_chain([MagicMock()])
                    mock_db.session.query.return_value = q
                    resultado = _check_cierre_fase(fase_id=99, codigo_resultado=codigo)
            assert resultado is not None, f'Debería bloquear con resultado {codigo}'
            assert resultado.permitido is False
