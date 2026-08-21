"""
Tests issue #173 — aritmética de los intervalos de suspensión (art. 22 LPACAP).

Reescrito en #778. Lo que este fichero cubre ahora son las funciones puras que
sobrevivieron al rediseño: fundir intervalos y convertirlos en días que empujan
la fecha límite. De DÓNDE salen esos intervalos —la medida única y el recorrido
de las tareas suspensoras— es cosa de `test_778_medida_unica.py`.

Historia de lo que se cayó, para que no vuelva:

  - #788 corrigió el ámbito (la SOLICITUD, no «el elemento evaluado»: un Trámite
    se encontraba a sí mismo entre sus hermanos y cada CONSULTA_SEPARATA se
    suspendía a sí misma), la fusión y el cómputo (A, B].
  - #778 quitó el segundo motor entero: la lista de trámites suspensores
    escrita en el código, el rescate que buscaba el documento de cierre en un
    trámite hermano y las tres tentativas encadenadas de cierre. Una suspensión
    no es un mecanismo aparte: es el plazo de un tercero visto desde la
    solicitud, y su intervalo va del disparo a la parada de esa misma medida.
  - El flag `abierto` guardado como dato pasó a ser `vivo`, derivado del estado
    de la espera. No es un renombre: antes «abierto» significaba «no encontré
    documento de cierre», que es justo lo que hacía crecer la suspensión sin
    límite; ahora significa «la espera sigue corriendo», y una espera vencida
    sin respuesta no lo está.
"""
from datetime import date


HOY = date(2026, 5, 13)


def _bloque(inicio, fin, vivo=False):
    return {'inicio': inicio, 'fin': fin, 'vivo': vivo}


# ---------------------------------------------------------------------------
# A) Fusión de intervalos — un reloj no se para dos veces
# ---------------------------------------------------------------------------

class TestFusionIntervalos:

    def test_vacio(self):
        from app.services.plazos import _fusionar_intervalos
        assert _fusionar_intervalos([]) == []

    def test_disjuntos_no_se_funden(self):
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            _bloque(date(2026, 1, 1), date(2026, 1, 10)),
            _bloque(date(2026, 2, 1), date(2026, 2, 10)),
        ])
        assert len(resultado) == 2

    def test_solapados_se_funden(self):
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            _bloque(date(2026, 1, 1), date(2026, 2, 15)),
            _bloque(date(2026, 2, 1), date(2026, 3, 1)),
        ])
        assert resultado == [_bloque(date(2026, 1, 1), date(2026, 3, 1))]

    def test_contiguos_se_funden(self):
        """Entre el cierre de uno y el día siguiente no corre plazo ninguno."""
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            _bloque(date(2026, 1, 1), date(2026, 1, 31)),
            _bloque(date(2026, 2, 1), date(2026, 2, 10)),
        ])
        assert len(resultado) == 1
        assert resultado[0]['fin'] == date(2026, 2, 10)

    def test_contenido_no_alarga_el_bloque(self):
        """Un intervalo dentro de otro no debe acortar el fin del que lo contiene."""
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            _bloque(date(2026, 1, 1), date(2026, 6, 1)),
            _bloque(date(2026, 2, 1), date(2026, 3, 1)),
        ])
        assert resultado == [_bloque(date(2026, 1, 1), date(2026, 6, 1))]

    def test_cerrado_y_vivo_se_funden_juntos(self):
        """Separata cerrada + requerimiento vivo.

        Separata notificada el 1-feb y contestada el 1-abr; requerimiento
        notificado el 1-mar y aún corriendo. En dos bolsas separadas serían
        2 + 2 = 4 meses; la verdad es la unión: 1-feb → hoy. Y el plazo lleva
        parado de forma continua desde el 1-feb, aunque la causa viva sea del
        1-mar.
        """
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            _bloque(date(2026, 2, 1), date(2026, 4, 1)),
            _bloque(date(2026, 3, 1), HOY, vivo=True),
        ])
        assert len(resultado) == 1
        assert resultado[0]['inicio'] == date(2026, 2, 1)
        assert resultado[0]['fin'] == HOY
        assert resultado[0]['vivo'] is True


# ---------------------------------------------------------------------------
# B) De intervalos a días, y de días a fecha límite
# ---------------------------------------------------------------------------

class TestDiasSuspendidos:

    def test_intervalo_cerrado_cuenta_como_A_B(self):
        """(A, B]: del día 1 al 10 median 9 días, no 10 (arts. 22.1.a / 22.1.d)."""
        from app.services.plazos import _dias_suspendidos
        # lun 19 ene → lun 26 ene: hábiles del 20 al 26 = 5
        dias = _dias_suspendidos(
            [_bloque(date(2026, 1, 19), date(2026, 1, 26))], frozenset()
        )
        assert dias == 5

    def test_cierre_el_mismo_dia_son_cero_dias(self):
        """A == B: no medió nada entre los dos actos."""
        from app.services.plazos import _dias_suspendidos
        assert _dias_suspendidos(
            [_bloque(date(2026, 1, 8), date(2026, 1, 8))], frozenset()
        ) == 0


class TestAplicarSuspensiones:

    def test_suspension_extiende_fecha_limite(self):
        """
        Plazo: 20 días hábiles desde 2026-01-12 → fecha_base = 2026-02-09.
        Suspensión: lun 2026-01-19 al lun 2026-01-26 → 5 días hábiles (A, B].
        Fecha efectiva: 2026-02-09 + 5 hábiles = 2026-02-16.
        """
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 12), 20, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 2, 9)

        bloques = [_bloque(date(2026, 1, 19), date(2026, 1, 26))]
        assert _aplicar_suspensiones(fecha_base, bloques, inhabiles) == date(2026, 2, 16)

    def test_sin_suspensiones_no_cambia_fecha(self):
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 3, 1), 10, 'DIAS_HABILES', inhabiles)
        assert _aplicar_suspensiones(fecha_base, [], inhabiles) == fecha_base

    def test_bloques_disjuntos_acumulan_sus_dias(self):
        """Dos bloques que la fusión dejó separados suman por separado."""
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 5), 5, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 1, 12)  # 5 hábiles: 6,7,8,9,12

        bloques = [
            _bloque(date(2026, 1, 7), date(2026, 1, 8)),    # (7,8]  → 1 hábil
            _bloque(date(2026, 1, 13), date(2026, 1, 15)),  # (13,15] → 2 hábiles
        ]
        # lun 12 + 3 hábiles = jue 15
        assert _aplicar_suspensiones(fecha_base, bloques, inhabiles) == date(2026, 1, 15)
