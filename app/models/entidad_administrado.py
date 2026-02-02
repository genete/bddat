# app/models/entidad_administrado.py
"""
Modelo EntidadAdministrado - Metadatos específicos de personas físicas/jurídicas privadas.

Tabla: ENTIDADES_ADMINISTRADOS (O_015)
Descripción: Metadatos de administrados (titulares, solicitantes, autorizados).
             Incluye datos para sistema Notifica y representación.
"""

from app import db


class EntidadAdministrado(db.Model):
    """
    Metadatos específicos para administrados (personas físicas/jurídicas privadas).
    
    Roles que puede desempeñar:
    - Titular de expediente
    - Solicitante de solicitud
    - Autorizado en solicitud (representante del titular)
    
    Sistema de notificaciones: Notifica (par CIF/NIF + email_notificaciones)
    Regla: Si hay representante_nif_cif, se notifica al representante. Si no, al titular.
    """
    
    __tablename__ = 'entidades_administrados'
    
    # Campos
    entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('entidades.id', ondelete='CASCADE'), 
        primary_key=True,
        comment='Referencia a entidad base (PK y FK con CASCADE)'
    )
    
    email_notificaciones = db.Column(
        db.String(120), 
        nullable=False, 
        index=True,
        comment='Email oficial para sistema Notifica. Puede ser personal o corporativo donde se reciben notificaciones electrónicas oficiales'
    )
    
    representante_nif_cif = db.Column(
        db.String(20), 
        nullable=True, 
        index=True,
        comment='NIF/CIF de quien representa/gestiona. NULL si autorepresentado (persona física) o gestión corporativa directa. Normalizado como CIF/NIF'
    )
    
    representante_nombre = db.Column(
        db.String(200), 
        nullable=True,
        comment='Nombre completo del representante. NULL si autorepresentado. Puede ser persona física (administrador único) o jurídica (consultora contratada)'
    )
    
    representante_telefono = db.Column(
        db.String(20), 
        nullable=True,
        comment='Teléfono del representante. Contacto directo con quien gestiona'
    )
    
    representante_email = db.Column(
        db.String(120), 
        nullable=True,
        comment='Email del representante. Email de contacto (NO oficial para notificaciones, solo coordinación)'
    )
    
    notas_representacion = db.Column(
        db.Text, 
        nullable=True,
        comment='Observaciones sobre la representación. Tipo de cargo o relación: "Administrador único", "Consultora ACME SL contratada", "Apoderado con poder notarial", etc.'
    )
    
    # Constraint CHECK: coherencia representante (si hay CIF, debe haber nombre)
    __table_args__ = (
        db.CheckConstraint(
            """(representante_nif_cif IS NULL AND representante_nombre IS NULL)
               OR
               (representante_nif_cif IS NOT NULL AND representante_nombre IS NOT NULL)""",
            name='chk_representante_coherente'
        ),
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_administrado')
    
    def __repr__(self):
        rep = 'CON repr.' if self.tiene_representante else 'SIN repr.'
        return f'<EntidadAdministrado {self.entidad_id}: {rep}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'email_notificaciones': self.email_notificaciones,
            'representante_nif_cif': self.representante_nif_cif,
            'representante_nombre': self.representante_nombre,
            'representante_telefono': self.representante_telefono,
            'representante_email': self.representante_email,
            'notas_representacion': self.notas_representacion
        }
    
    @property
    def tiene_representante(self):
        """Indica si tiene representante definido."""
        return bool(self.representante_nif_cif and self.representante_nombre)
    
    @property
    def es_autorepresentado(self):
        """Indica si el titular se representa a sí mismo."""
        return not self.tiene_representante
    
    def obtener_cif_notifica(self):
        """
        Devuelve el CIF/NIF que debe usarse para notificar.
        
        Regla:
        - Si hay representante_nif_cif → usar ese (quien gestiona)
        - Si representante_nif_cif es NULL → usar entidades.cif_nif (titular)
        """
        if self.representante_nif_cif:
            return self.representante_nif_cif
        else:
            return self.entidad.cif_nif if self.entidad else None
    
    def obtener_par_notifica(self):
        """
        Devuelve el par (CIF/NIF, EMAIL) para sistema Notifica.
        
        Returns:
            tuple: (cif_nif, email_notificaciones)
        """
        return (
            self.obtener_cif_notifica(),
            self.email_notificaciones
        )
    
    def validar_datos_notifica(self):
        """
        Valida que tenga los datos mínimos para notificaciones Notifica.
        
        Notifica requiere par completo: (CIF/NIF, EMAIL_NOTIFICACIONES)
        
        Returns:
            tuple: (bool, str) - (es_valido, mensaje)
        """
        if not self.email_notificaciones:
            return False, "Email de notificaciones requerido para sistema Notifica"
        
        cif_notifica = self.obtener_cif_notifica()
        if not cif_notifica:
            return False, "CIF/NIF requerido (titular o representante) para sistema Notifica"
        
        return True, f"Datos válidos para Notifica: {cif_notifica}"
    
    @staticmethod
    def buscar_por_representante_nif(nif):
        """Buscar administrados por NIF/CIF del representante."""
        from app.models.entidad import Entidad
        nif_norm = Entidad.normalizar_cif_nif(nif)
        return EntidadAdministrado.query.filter_by(representante_nif_cif=nif_norm).all()
    
    @staticmethod
    def buscar_por_email_notificaciones(email):
        """Buscar administrados por email de notificaciones."""
        return EntidadAdministrado.query.filter(
            EntidadAdministrado.email_notificaciones.ilike(f'%{email}%')
        ).all()
