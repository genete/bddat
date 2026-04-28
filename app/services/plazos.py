"""
Servicio de plazos administrativos — BDDAT.

Calcula el estado del plazo legal asociado a un elemento ESFTT
(Solicitud, Fase, Trámite, Tarea) y devuelve un EstadoPlazo.

Arquitectura (DISEÑO_FECHAS_PLAZOS.md §4):
    ContextAssembler llama a obtener_estado_plazo() para poblar las variables
    'estado_plazo' y 'efecto_plazo' que el motor agnóstico evalúa con operadores
    estándar (EQ/IN/etc.). El motor no conoce este servicio.

Stub Fase 2 (#190):
    Devuelve SIN_PLAZO/NINGUNO siempre. Ninguna regla del motor dispara por plazo.
    La lógica real (catalogo_plazos, dias_inhabiles, suspensiones) se implementa en #172.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class EstadoPlazo:
    estado: str                    # 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO'
    efecto: str                    # 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA'
                                   # | 'SILENCIO_DESESTIMATORIO' | 'CADUCIDAD_PROCEDIMIENTO'
                                   # | 'PERDIDA_TRAMITE' | 'APERTURA_RECURSO'
                                   # | 'PRESCRIPCION_CONDICIONADO' | 'CONFORMIDAD_PRESUNTA'
                                   # | 'SIN_EFECTO_AUTOMATICO'
    fecha_limite: Optional[date]   # None si SIN_PLAZO
    dias_restantes: Optional[int]  # None si SIN_PLAZO; negativo si VENCIDO


def obtener_estado_plazo(elemento, tipo_elemento: str) -> EstadoPlazo:
    """
    Devuelve el estado del plazo legal asociado a un elemento ESFTT.

    Args:
        elemento:      Instancia ORM del elemento evaluado
                       (Solicitud, Fase, Tramite o Tarea).
        tipo_elemento: Literal del tipo: 'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA'.

    Returns:
        EstadoPlazo con estado, efecto, fecha_limite y dias_restantes.

    Stub (#190 Fase 2):
        Siempre devuelve SIN_PLAZO/NINGUNO. Seguro: no bloquea ningún flujo.

    M3 (#172):
        1. Buscar en catalogo_plazos el plazo aplicable a (tipo_elemento, tipo_elemento_id).
        2. Resolver campo_fecha JSONB → Documento.fecha_administrativa.
        3. calcular_fecha_fin(fecha_administrativa, plazo, dias_inhabiles, suspensiones).
        4. Derivar estado según (fecha_limite, hoy(), umbral_alerta=5 días hábiles).
        5. Leer efecto_vencimiento del catalogo_plazos.
    """
    return EstadoPlazo(
        estado='SIN_PLAZO',
        efecto='NINGUNO',
        fecha_limite=None,
        dias_restantes=None,
    )
