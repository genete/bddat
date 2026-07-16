import os

from sqlalchemy.orm import validates

from app import db

class Documento(db.Model):
    """
    Pool puro de archivos físicos asociados a expedientes.
    
    PROPÓSITO:
        Almacena metadatos de documentos físicos pertenecientes a expedientes.
        Tabla agnóstica: solo conoce su expediente, todas las demás relaciones
        (proyectos, tareas) se definen externamente apuntando hacia aquí.
    
    FILOSOFÍA:
        - El documento es una entidad pura del expediente
        - Solo tiene UN FK: expediente_id
        - Es completamente agnóstico respecto a:
          * Qué tarea lo produjo (se define en DOCUMENTOS_TAREA, rol PRODUCIDO)
          * Qué tareas lo consumen (se define en DOCUMENTOS_TAREA, rol CONSUMIDO)
          * Si es parte de un proyecto (se define en DOCUMENTOS_PROYECTO)
        - Pool único de documentos por expediente, relaciones viven fuera
    
    CAMPO EXPEDIENTE_ID:
        - ÚNICO FK del documento
        - NOT NULL: Todo documento pertenece a un expediente

    CAMPO TIPO_DOC_ID:
        - FK a TIPOS_DOCUMENTOS. Clasificación semántica de negocio del documento.
        - Distinta del tipo MIME (tipo_contenido): indica qué ES el documento, no su formato.
        - Ejemplos: INFORME_ORGANISMO, RESOLUCION, PODER_REPRESENTACION, ALEGACION…
        - OTROS (id=1) es el cajón de sastre por defecto (server_default='1').
        - Usado por el motor de reglas con el criterio EXISTE_DOCUMENTO_TIPO.
        - NOT NULL: todo documento tiene al menos tipo OTROS.

    CAMPO FECHA_ADMINISTRATIVA:
        - NO es la fecha del archivo físico (metadatos filesystem)
        - ES la fecha con efectos administrativos y legales
        - Ejemplos: fecha registro entrada, firma, notificación, publicación
        - Determina plazos, efectos jurídicos y secuencia administrativa
        - NULLABLE: dos casos legítimos de NULL:
          1. Documento cargado al pool pendiente de revisión posterior.
          2. Documento sin valor jurídico propio (informe ANALIZAR): el efecto
             jurídico lo tiene el documento producido por ELABORAR.
        - La API de asignación a tareas debe rechazar documentos con NULL
          cuando el tipo de tarea lo requiera (validación de negocio, no de BD).

    CAMPO URL:
        Admite tres esquemas:
        - Ruta local (sin '://'): fichero en el servidor de archivos, SIEMPRE
          relativa a FILESYSTEM_BASE, nunca absoluta (ADR-032, corrección de
          la regresión de #180). @validates('url') rechaza ruta absoluta o
          que escape de FILESYSTEM_BASE. ruta_absoluta() resuelve al momento
          de uso.
        - 'http://' / 'https://': recurso externo.
        - 'bddat://<recurso>/<id>': registro interno de BD sin fichero físico.
          Tablas activas: diagnosticos, certificados.
          fecha_administrativa es independiente del esquema de url: la fija
          la naturaleza jurídica del documento, no el mecanismo de
          almacenamiento (#574).
        El helper resolver_url() despacha al mecanismo correcto según el esquema.
        El nombre a mostrar en interfaz se deduce del último segmento de la URL.

    CAMPO HASH_MD5:
        - Verificación de integridad del archivo
        - Detección de duplicados
        - NULLABLE: Se calcula tras almacenamiento

    CAMPO PRIORIDAD:
        - 0 = no prioritario (defecto)
        - >0 = prioritario (recurso de alzada, respuesta desfavorable, alegación urgente…)
        - Pseudo-booleano que deja margen para escalas futuras sin cambio de modelo.
        - Validación de rango solo en frontend; sin constraint de BD.
        - Permite al administrativo señalar documentos relevantes antes de que
          el técnico los incorpore al flujo de tramitación.

    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - tipo_doc → TIPOS_DOCUMENTOS.id (FK, clasificación semántica)
        - documentos_proyecto ← DOCUMENTOS_PROYECTO.documento_id (tabla puente con proyectos)
        - vinculos_tarea ← DOCUMENTOS_TAREA (vínculos con tareas, con rol)

    PROCEDENCIA DEL EMISOR:
        No existe campo origen en esta tabla (eliminado en #191).
        La identificación del emisor concreto (organismo, BOE, Notifica, portafirmas…)
        se registra en las columnas propias de cada tabla cualificadora
        (ej: documentos_proyecto puede añadir entidad_emisora_id si lo necesita).

    REGLAS DE NEGOCIO:
        - Un documento pertenece a UN expediente
        - Un documento puede estar en N proyectos (vía DOCUMENTOS_PROYECTO)
        - Un documento puede ser producido por UNA tarea (índice parcial único en documentos_tarea)
        - Un documento puede ser usado por N tareas

    NOTAS DE VERSIÓN:
        v3.0: RENOMBRADO fecha_documento → fecha_administrativa.
              ELIMINADOS: tarea_origen_id, tarea_destino_id, proyecto_id.
        v4.0: AÑADIDO tipo_doc_id FK → tipos_documentos (#188).
        v4.1: ELIMINADOS origen, nombre_display. fecha_administrativa → nullable (#191).
    """
    __tablename__ = 'documentos'
    __table_args__ = (
        db.Index('idx_documentos_expediente', 'expediente_id'),
        db.Index('idx_documentos_fecha_administrativa', 'fecha_administrativa'),
        db.Index('idx_documentos_hash', 'hash_md5'),
        db.Index('idx_documentos_tipo_doc', 'tipo_doc_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del documento'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id'),
        nullable=False,
        comment='FK a EXPEDIENTES. ÚNCO FK del documento (tabla agnóstica)'
    )

    tipo_doc_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id'),
        nullable=False,
        default=1,
        server_default='1',
        comment='FK a TIPOS_DOCUMENTOS. Tipo semántico de negocio del documento'
    )

    url = db.Column(
        db.Text,
        nullable=False,
        comment='Ruta local, http(s):// o bddat://<recurso>/<id> (ADR-006)'
    )
    
    tipo_contenido = db.Column(
        db.String(50),
        nullable=True,
        comment='Tipo MIME del archivo (ej: application/pdf)'
    )

    fecha_administrativa = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha con efectos administrativos (firma, registro, publicación). NULL = pendiente o sin valor jurídico propio (borrador/informe interno)'
    )

    asunto = db.Column(
        db.String(500),
        nullable=True,
        comment='Descripción o asunto del documento'
    )

    prioridad = db.Column(
        db.Integer,
        default=0,
        nullable=True,
        comment='0 = no prioritario. >0 = prioritario (recurso, respuesta desfavorable, alegación urgente). Validación de rango solo en frontend.'
    )

    hash_md5 = db.Column(
        db.String(32),
        nullable=True,
        comment='Hash MD5 para verificación de integridad y detección de duplicados'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    expediente = db.relationship('Expediente', foreign_keys=[expediente_id], backref='documentos')
    tipo_doc = db.relationship('TipoDocumento', foreign_keys=[tipo_doc_id])

    @validates('url')
    def _validar_url(self, key, value):
        if value is None:
            return value
        if '://' in value:
            if not value.startswith(('http://', 'https://', 'bddat://')):
                raise ValueError(f'Esquema de URL no admitido: {value!r}')
            return value
        # Esquema local (ADR-032): siempre relativa a FILESYSTEM_BASE, nunca absoluta.
        if value.startswith(('/', '\\')) or os.path.isabs(value):
            raise ValueError(
                f'Ruta local debe ser relativa a FILESYSTEM_BASE, no absoluta: {value!r}'
            )
        normalizada = os.path.normpath(value)
        if normalizada == '..' or normalizada.startswith('..' + os.sep):
            raise ValueError(f'Ruta local no puede salir de FILESYSTEM_BASE: {value!r}')
        return value

    def ruta_absoluta(self) -> str:
        """Resuelve la ruta local (relativa a FILESYSTEM_BASE) en ruta absoluta (ADR-032).

        Solo válido para el esquema local (sin '://').
        """
        from flask import current_app
        base = current_app.config.get('FILESYSTEM_BASE', '')
        if not base:
            raise RuntimeError('FILESYSTEM_BASE no está configurado')
        base_norm = os.path.normpath(os.path.abspath(base))
        ruta_abs = os.path.normpath(os.path.join(base_norm, (self.url or '').replace('/', os.sep)))
        if ruta_abs != base_norm and not ruta_abs.startswith(base_norm + os.sep):
            raise ValueError(f'Ruta fuera de FILESYSTEM_BASE: {self.url!r}')
        return ruta_abs

    def resolver_url(self):
        """Despacha según el esquema de url (ADR-006).

        - Ruta local  → file object abierto en modo binario (ruta resuelta vía ruta_absoluta(), ADR-032)
        - http(s)://  → requests.Response
        - bddat://    → dict completo del registro ORM destino
        """
        url = self.url or ''
        if url.startswith('bddat://'):
            return self._resolver_bddat(url)
        if url.startswith(('http://', 'https://')):
            import urllib.request
            return urllib.request.urlopen(url)
        return open(self.ruta_absoluta(), 'rb')

    def _resolver_bddat(self, url: str) -> dict:
        partes = url[len('bddat://'):].split('/')
        if len(partes) != 2:
            raise ValueError(f'URI bddat:// malformada: {url!r}')
        recurso, id_str = partes
        try:
            registro_id = int(id_str)
        except ValueError:
            raise ValueError(f'ID no numérico en URI bddat://: {url!r}')
        if recurso == 'diagnosticos':
            from app.models.diagnosticos import Diagnostico
            diag = Diagnostico.query.get(registro_id)
            if diag is None:
                raise LookupError(f'Diagnostico id={registro_id} no encontrado')
            return {
                'id': diag.id,
                'documento_id': diag.documento_id,
                'resultado': diag.resultado,
                'defectos': diag.defectos or [],
            }
        if recurso == 'certificados':
            from app.models.certificados import Certificado
            cert = Certificado.query.get(registro_id)
            if cert is None:
                raise LookupError(f'Certificado id={registro_id} no encontrado')
            return {
                'id': cert.id,
                'generado_en': cert.generado_en.isoformat(),
                'datos': cert.datos,
            }
        raise NotImplementedError(f'Recurso bddat:// no implementado: {recurso!r}')

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Documento id={self.id} expediente={self.expediente_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return (self.url or '').rsplit('/', 1)[-1] or f'Documento {self.id}'
