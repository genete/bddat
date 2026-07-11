"""Tabla genérica de configuración del sistema (issue #323)."""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db

log = logging.getLogger(__name__)


class ConfiguracionSistema(db.Model):
    __tablename__ = 'configuracion_sistema'
    __table_args__ = {'schema': 'public'}

    clave     = db.Column(db.String(80),  primary_key=True)
    valor     = db.Column(db.Text(),      nullable=False)
    tipo_dato = db.Column(db.String(20),  nullable=False)
    etiqueta  = db.Column(db.String(200), nullable=True)

    @classmethod
    def get(cls, clave: str, default: Optional[str] = None) -> Optional[str]:
        """Devuelve el valor de la clave o `default` si no existe o BD no disponible."""
        try:
            row = cls.query.filter_by(clave=clave).first()
            return row.valor if row is not None else default
        except (OperationalError, ProgrammingError):
            log.warning('configuracion_sistema: tabla no disponible, devolviendo default para %s', clave)
            return default

    @classmethod
    def set(cls, clave: str, valor: str, *, tipo_dato: str = 'texto', etiqueta: Optional[str] = None) -> None:
        """Actualiza el valor de una clave existente, o la crea si no existe.

        No hace commit — responsabilidad del llamador (mismo criterio que bitacora_svc.registrar).
        """
        row = cls.query.filter_by(clave=clave).first()
        if row is None:
            row = cls(clave=clave, valor=valor, tipo_dato=tipo_dato, etiqueta=etiqueta)
            db.session.add(row)
        else:
            row.valor = valor
