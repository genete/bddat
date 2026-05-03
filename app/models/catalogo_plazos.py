"""Modelo CatalogoPlazo — catálogo de plazos legales por tipo de elemento ESFTT.

Referencia: DISEÑO_FECHAS_PLAZOS.md §3.2
"""
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class CatalogoPlazo(db.Model):
    """Plazo legal asociado a un tipo de elemento ESFTT.

    PROPÓSITO: tabla maestra administrable por el Supervisor que vincula un
    tipo de Solicitud/Fase/Trámite/Tarea con su plazo legal y el efecto del
    vencimiento. Permite histórico de cambios normativos sin alterar el
    catálogo de tipos ESFTT.

    CAMPO tipo_elemento: nivel ESFTT ('SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA').
    CAMPO tipo_elemento_id: ID en la tabla tipos_* correspondiente.
        FK polimórfica sin constraint BD (como motor_reglas).
    CAMPO campo_fecha: JSONB que indica qué Documento.fecha_administrativa
        es el inicio del cómputo. Formato:
            {'fk': 'documento_solicitud_id'}           -- caso directo
            {'via_tarea_tipo': 'ESPERAR_PLAZO',
             'fk': 'documento_usado_id'}               -- vía tarea hija
    CAMPO plazo_unidad: 'DIAS_HABILES' | 'DIAS_NATURALES' | 'MESES' | 'ANOS'
    CAMPO efecto_vencimiento_id: FK a efectos_plazo.
    CAMPO vigencia_desde / vigencia_hasta: rango de vigencia. NULL = sin límite.
    CAMPO activo: TRUE para la entrada vigente; permite desactivar sin borrar.
    """
    __tablename__ = 'catalogo_plazos'
    __table_args__ = (
        db.Index('idx_catalogo_plazos_tipo_elem',        'tipo_elemento', 'tipo_elemento_id'),
        db.Index('idx_catalogo_plazos_tipo_orden',       'tipo_elemento', 'tipo_elemento_id', 'orden'),
        db.Index('idx_catalogo_plazos_tipo_codigo',      'tipo_elemento', 'tipo_elemento_codigo'),
        db.Index('idx_catalogo_plazos_tipo_codigo_orden','tipo_elemento', 'tipo_elemento_codigo', 'orden'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_elemento = db.Column(
        db.String(20), nullable=False,
        comment='Nivel ESFTT: SOLICITUD | FASE | TRAMITE | TAREA',
    )
    tipo_elemento_id = db.Column(
        db.Integer, nullable=False,
        comment='DEPRECATED — usar tipo_elemento_codigo. Se eliminará en issue posterior.',
    )
    tipo_elemento_codigo = db.Column(
        db.String(60), nullable=False,
        comment='Código estable del tipo (reemplaza tipo_elemento_id — polimorfismo seguro)',
    )
    campo_fecha = db.Column(
        JSONB, nullable=True,
        comment='Referencia al Documento.fecha_administrativa de inicio: {"fk":"..."} o {"via_tarea_tipo":"...","fk":"..."}',
    )
    plazo_valor = db.Column(
        db.Integer, nullable=False,
        comment='Valor numérico del plazo (días, meses o años)',
    )
    plazo_unidad = db.Column(
        db.String(20), nullable=False,
        comment='Unidad: DIAS_HABILES | DIAS_NATURALES | MESES | ANOS',
    )
    efecto_vencimiento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.efectos_plazo.id', ondelete='RESTRICT'),
        nullable=False,
        comment='FK a efectos_plazo — efecto del vencimiento',
    )
    norma_origen = db.Column(
        db.Text, nullable=True,
        comment='Cita de la norma que fija el plazo (art. 21.3 LPACAP, art. 128 RD 1955/2000, etc.)',
    )
    vigencia_desde = db.Column(
        db.Date, nullable=True,
        comment='Inicio de vigencia de este plazo. NULL = desde siempre',
    )
    vigencia_hasta = db.Column(
        db.Date, nullable=True,
        comment='Fin de vigencia de este plazo. NULL = indefinido',
    )
    activo = db.Column(
        db.Boolean, nullable=False, default=True, server_default='TRUE',
        comment='FALSE para entradas desactivadas sin borrar',
    )
    orden = db.Column(
        db.Integer, nullable=False, default=100, server_default='100',
        comment='Prioridad de selección: menor → se evalúa primero. '
                'Fallback sin condiciones: orden alto (100). No unique.',
    )

    efecto_plazo = db.relationship(
        'EfectoPlazo',
        foreign_keys=[efecto_vencimiento_id],
        back_populates='plazos',
    )
    condiciones = db.relationship(
        'CondicionPlazo',
        backref='catalogo_plazo',
        cascade='all, delete-orphan',
        order_by='CondicionPlazo.orden',
    )

    def __repr__(self):
        return f'<CatalogoPlazo {self.tipo_elemento}:{self.tipo_elemento_id} {self.plazo_valor}{self.plazo_unidad}>'
