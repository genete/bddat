"""Modelo CatalogoPlazo — catálogo de plazos legales por tipo de elemento ESFTT.

Referencia: DISEÑO_FECHAS_PLAZOS.md §3.2
"""
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class CatalogoPlazo(db.Model):
    """Plazo legal asociado a un tipo de elemento ESFTT.

    PROPÓSITO: tabla maestra administrable por el Supervisor que vincula un
    tipo de acto o de Tarea con su plazo legal y el efecto del vencimiento.
    Permite histórico de cambios normativos sin alterar el catálogo de tipos
    ESFTT.

    CAMPO tipo_elemento: nivel de la FILA ('ACTO' | 'TAREA'), con
        CheckConstraint. Redundante con la longitud de `camino`, pero se
        conserva como prefiltro SQL barato — filtrar por número de segmentos de
        un string no es viable.
        ACTO es el plazo máximo de resolver de cada tipo atómico de solicitud
        (#930, ADR-049 §E). Se llamó SOLICITUD hasta #931, que lo renombró
        porque esas filas nunca fueron el plazo de la solicitud entera: una
        AAP+AAC+DUP tiene tres. No confundir con el nivel del NODO del árbol
        (Solicitud, Fase, Trámite, Tarea), que es el de cada segmento del camino.
        TRAMITE queda prohibido desde #788: un plazo necesita fecha de inicio,
        y el Trámite no porta ninguna — es taxonomía ESFTT, no figura jurídica.
        FASE lo estuvo con #788, volvió con ADR-048 para las fases
        finalizadoras y se retiró de nuevo en #931: el plazo de resolver es del
        acto, no de la fase que lo resuelve, que ni existe mientras corre.
    CAMPO camino: patrón calificado ESFTT con comodín posicional 'ANY' (#785).
        Mismo formato y mismo matcher (motor_reglas._sujeto_casa) que
        ReglaMotor.sujeto, con un nivel más de profundidad. La longitud codifica
        el nivel, y el último segmento NUNCA es 'ANY' (es el tipo del elemento
        evaluado, siempre conocido):
            ACTO   2 segmentos   <expediente>/<siglas del acto>
            TAREA  5             <expediente>/<siglas>/<fase>/<tramite>/<tarea>
        La hoja de una fila ACTO es un tipo atómico (AAP, no AAP+AAC): el camino
        del acto lleva siempre el suyo, así que una combinación no casaría nunca
        — lo valida el CRUD (#931). En una TAREA, en cambio, el segundo segmento
        son las siglas reales de la solicitud y sí puede ser una combinación.
        Sustituye a tipo_elemento_codigo, que no distinguía dos puntos distintos
        del árbol con el mismo literal (ESPERAR_PLAZO, RESOLUCION). Antes de #785
        esa distinción la hacían condiciones_plazo sobre variables que reexponían
        posición en el árbol — FK disfrazada, retirada en la misma migración.
    CAMPO campo_fecha: JSONB que indica qué Documento.fecha_administrativa
        es el inicio del cómputo. Vocabulario cerrado (#788):
            {'fk': 'documento_solicitud_id'}                 -- nivel ACTO: el acto no tiene esa FK
                                                                 y se resuelve subiendo a su solicitud
            {'rol': 'CONSUMIDO'}                             -- nivel TAREA
            {'rol': 'PRODUCIDO'}                             -- nivel TAREA, caso retroactivo (#416)
            {'rol': 'CONSUMIDO',
             'tipo_documento': 'ANUNCIO_PUBLICADO'}          -- ídem, con el tipo declarado
        `tipo_documento` es opcional y desempata cuando dos tareas del mismo tipo
        conviven en un trámite (las dos esperas de los ANUNCIO_*): comparten
        camino, así que sin él ganaría siempre la de menor orden. Se omite cuando
        el documento de entrada es polimórfico por diseño — el justificante de
        CONSULTA_SEPARATA depende del canal (BANDEJA / NOTIFICA / POSTAL / SIR).
    CAMPO campo_fecha_cumplimiento: JSONB con el MISMO vocabulario cerrado que
        `campo_fecha` más un tercer portador, apuntando al documento que acredita
        el cumplimiento (ADR-041 §D). Cada plazo se abre y se cierra en el mismo
        sitio, así que para una tarea es casi siempre `{'rol': 'PRODUCIDO'}`.
        Para las filas ACTO —ADR-049 §E, #930— es
        `{'calculado': 'documento_cumplimiento'}`: la propiedad del acto que
        devuelve el documento que acredita la notificación al titular en la fase
        que lo resuelve (arts. 21.2 y 40.4 LPACAP); solo nombres de
        `plazos.CALCULADOS`. (Hasta #931 las filas de combinación cerraban con
        `{'fk': 'documento_cierre_id'}`, y las de FASE con NULL.)
        `JSONB` igual que su gemela `campo_fecha` (#802): nació como `db.JSON`
        en `778a_plazos_medida_unica.py` por una portabilidad que no sostiene la
        decisión —ni `json` ni `jsonb` existen fuera de PostgreSQL entre los
        motores considerados, y de sobrevenir esa migración el obstáculo real
        serían las 29 columnas `boolean` y las decenas de migraciones con SQL
        crudo de Postgres, no esta columna—. Dos columnas hermanas con idéntica
        semántica y el mismo algoritmo no deben divergir de tipo por un
        argumento que no aplica; `json` tampoco soporta el operador `=` en
        PostgreSQL, y `campo_fecha` ya se filtra así en `788a`.
        NULL es un valor legítimo, no un hueco por rellenar: sin señalador el
        plazo nunca alcanza CUMPLIDO y sólo puede estar corriendo o vencido. Es
        el caso de TABLON_AYUNTAMIENTOS, donde el disparo y el único candidato a
        cierre son el mismo documento (#416) y `VENCIDO` ya se lee como «la
        exposición se completó».
    CAMPO suspende_plazo_solicitud: TRUE si este plazo suspende el plazo de la
        solicitud (art. 22.1.a y 22.1.d LPACAP). Sustituye a la lista
        `_TRAMITES_SUSPENSION` que vivía en plazos.py: que la petición de un
        informe preceptivo suspenda el plazo para resolver cambia cuando cambia
        la ley y es citable a artículo concreto, luego es dato normativo y va
        donde ya viven el valor del plazo y su efecto (test de ADR-037).
        CheckConstraint al nivel TAREA: el art. 22 suspende «el plazo máximo
        legal para resolver un procedimiento y notificar la resolución», que es
        el de la solicitud — marcarla a ella significaría que se suspende a sí
        misma. Corolario buscado: un plazo sin fila en el catálogo no suspende
        nada. (El nombre conserva «solicitud» por historia: lo que se suspende
        es el plazo de resolver de sus actos, #930.)
    CAMPO plazo_unidad: 'DIAS_HABILES' | 'DIAS_NATURALES' | 'MESES' | 'ANOS'
    CAMPO efecto_vencimiento_id: FK a efectos_plazo.
    CAMPO vigencia_desde / vigencia_hasta: rango de vigencia. NULL = sin límite.
    CAMPO activo: TRUE para la entrada vigente; permite desactivar sin borrar.
    """
    __tablename__ = 'catalogo_plazos'
    __table_args__ = (
        db.CheckConstraint("tipo_elemento IN ('ACTO', 'TAREA')",
                           name='ck_catalogo_plazos_tipo_elemento'),
        db.CheckConstraint("NOT suspende_plazo_solicitud OR tipo_elemento = 'TAREA'",
                           name='ck_catalogo_plazos_suspende_solo_tarea'),
        db.Index('idx_catalogo_plazos_tipo_orden', 'tipo_elemento', 'orden'),
        db.Index('idx_catalogo_plazos_camino',     'camino'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_elemento = db.Column(
        db.String(20), nullable=False,
        # Mismo texto que el COMMENT ON COLUMN de 931_nivel_acto
        comment='Nivel de la fila del catálogo: ACTO | TAREA (#931)',
    )
    camino = db.Column(
        db.String(250), nullable=False,
        comment='Patrón calificado ESFTT con comodín ANY: '
                'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO. '
                'La hoja (último segmento) nunca es ANY.',
    )
    campo_fecha = db.Column(
        JSONB, nullable=True,
        comment='Referencia al Documento.fecha_administrativa de inicio: '
                '{"fk":"documento_solicitud_id"} (nivel ACTO, resuelto vía la '
                'solicitud del acto) o '
                '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (nivel TAREA)',
    )
    campo_fecha_cumplimiento = db.Column(
        JSONB, nullable=True,
        # Mismo texto que el COMMENT ON COLUMN de 931_nivel_acto (antes, 930 D8)
        comment='Referencia al Documento.fecha_administrativa que acredita el cumplimiento: '
                '{"calculado":"documento_cumplimiento"} (ACTO: documento que acredita la '
                'notificación al titular en la fase que resuelve el acto, ADR-049) o '
                '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
                'NULL = el plazo nunca alcanza CUMPLIDO (#778)',
    )
    suspende_plazo_solicitud = db.Column(
        db.Boolean, nullable=False, default=False, server_default='FALSE',
        comment='TRUE si este plazo suspende el plazo de la solicitud (art. 22.1 LPACAP)',
    )
    plazo_valor = db.Column(
        db.Integer, nullable=False,
        comment='Valor numérico del plazo (días, meses o años). Entero positivo: '
                '0 no es un valor válido (#789, "plazo indefinido" se representa '
                'con ausencia de fila, no con plazo_valor=0 — ver plazos.py)',
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

    @property
    def hoja(self) -> str:
        """Último segmento del camino — el tipo del elemento evaluado.

        Solo para presentación (plantillas, JSON del listado). No es filtrable en
        SQL: para eso está `camino`. Deliberadamente NO se llama
        `tipo_elemento_codigo`: ese nombre invitaba a usarlo en queries como si
        siguiera siendo columna, y falla en runtime al no serlo.
        """
        return (self.camino or '').rsplit('/', 1)[-1]

    def __repr__(self):
        return f'<CatalogoPlazo {self.camino} {self.plazo_valor}{self.plazo_unidad}>'
