from app import db


class ConsejeriaDelegacionTerritorial(db.Model):
    """
    Composición de Consejerías de la Delegación Territorial propia.

    PROPÓSITO:
        Fija qué Consejería(s) componen la Delegación Territorial bajo la que
        tramita BDDAT, según el decreto de organización territorial vigente
        (Decreto 190/2026, de 30 de julio — BOJA extraordinario núm. 15).
        Alimenta el rótulo "Delegación Territorial de X y de Y" que aparece
        en la cabecera de los escritos generados (ADR-039 §1).

    FILOSOFÍA:
        - Dato del TIPO de delegación, no de la provincia: la composición de
          consejerías es la misma en las 8 provincias (mismo decreto), solo
          cambian la sede y el rótulo de BandeJA (ver UnidadOrganoPropio).
          Separarla evita duplicarla y desincronizarla en cada fila de
          provincia (ADR-039 §1, alternativa F descartada).
        - Hoy una sola fila (la nuestra); preparada para más si algún día
          hiciera falta.
        - CONSEJERIA_1/CONSEJERIA_2 son posicionales (el orden que trae el
          decreto), no roles con nombre semántico (orgánica/competencial):
          si la delegación deja de ser dual, basta actualizar el nombre y
          poner CONSEJERIA_2_NOMBRE a NULL, sin decidir de nuevo "cuál es
          cuál" (ADR-039 §1, alternativa C descartada).

    CAMPO CONSEJERIA_1_NOMBRE / CONSEJERIA_2_NOMBRE:
        - Nombre completo tal cual figura en el decreto vigente, con el
          prefijo "Consejería de " incluido.
        - CONSEJERIA_2_NOMBRE es NULL cuando la delegación agrupa una sola
          Consejería.

    RELACIONES:
        - unidades_organo_propio (1:N) ← UNIDADES_ORGANO_PROPIO.consejerias_delegacion_id

    REGLAS DE NEGOCIO:
        El rótulo "Delegación Territorial de X y de Y en <provincia>" no se
        guarda como texto: se compone en UnidadOrganoPropio.delegacion_territorial_nombre
        (propiedad computada) a partir de estos dos campos + la provincia.
    """
    __tablename__ = 'consejerias_delegaciones_territoriales'
    __table_args__ = {'schema': 'public'}

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    consejeria_1_nombre = db.Column(
        db.String(200),
        nullable=False,
        comment='Nombre completo de la primera Consejería, tal cual figura en el decreto vigente'
    )

    consejeria_2_nombre = db.Column(
        db.String(200),
        nullable=True,
        comment='Nombre completo de la segunda Consejería, si la delegación agrupa dos. NULL si agrupa solo una'
    )

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<ConsejeriaDelegacionTerritorial {self.id}: {self.consejeria_1_nombre!r}, {self.consejeria_2_nombre!r}>'

    def __str__(self):
        """Representación legible para interfaz."""
        if self.consejeria_2_nombre:
            return f'{self.consejeria_1_nombre} y {self.consejeria_2_nombre}'
        return self.consejeria_1_nombre


def _materia(nombre_consejeria):
    """Quita el prefijo 'Consejería de ' de un nombre de Consejería, si lo lleva."""
    prefijo = 'Consejería de '
    if nombre_consejeria and nombre_consejeria.startswith(prefijo):
        return nombre_consejeria[len(prefijo):]
    return nombre_consejeria


class UnidadOrganoPropio(db.Model):
    """
    Unidad territorial propia (una fila por provincia, más servicios centrales).

    PROPÓSITO:
        Dato de "dónde tramita" cada usuario: provincia, sede y rótulo de
        BandeJA de la Delegación Territorial correspondiente. Alimenta el
        destino real usado al enviar comunicaciones a Port@firmas (#758) y
        el token de cabecera de los escritos generados (ADR-039 §1).

    FILOSOFÍA:
        - Lo que varía por provincia (a diferencia de ConsejeriaDelegacionTerritorial,
          que fija la composición de consejerías, constante en las 8).
        - Se puebla con las 8 provincias desde el principio: aunque BDDAT es
          hoy mono-provincial, USUARIOS.unidad_organo_id resuelve la unidad
          por usuario, no por instancia global — el día que haya un usuario
          de otra provincia, solo hace falta asignarle la fila que le
          corresponde, sin migración de repoblado (ADR-039 §1).
        - No atada a EXPEDIENTE/PROYECTO: el destino real en BandeJA es el
          puesto del usuario que envía, no la provincia de la instalación
          (ADR-039 §1, alternativa B descartada; confirmado en estudio de
          campo, ver ESTUDIO_DOM_BANDEJA.md).

    CAMPO PROVINCIA:
        - Nombre de provincia (mismo formato que MUNICIPIOS.provincia).
        - NULL reservado para una futura fila de servicios centrales — no
          poblada en el alcance mínimo de #728.

    CAMPO CODIGO_BANDEJA_TEXTO:
        - Rótulo tal cual aparece en BandeJA (árbol de destinos), para
          localizar el nodo por texto en la automatización de #758.
        - NO se deriva de CONSEJERIA_1/CONSEJERIA_2: BandeJA puede ir a
          rebufo de la reorganización real, así que es dato explícito
          mantenido a mano, no derivado de la fuente institucional
          (ADR-039 §1).
        - Fuente de partida: app/data/bandeja_destinos/destinos_industria_energia_minas.csv,
          nodo "SV. ENERGIA (IND) (<PROVINCIA>)" por provincia.

    RELACIONES:
        - consejerias_delegacion (N:1) → CONSEJERIAS_DELEGACIONES_TERRITORIALES
        - usuarios (1:N) ← USUARIOS.unidad_organo_id
        - firmantes_portafirmas (1:N) ← FIRMANTES_PORTAFIRMAS.unidad_organo_id

    REGLAS DE NEGOCIO:
        delegacion_territorial_nombre (propiedad computada, no columna):
        "Delegación Territorial de {materia(consejeria_1)}[ y de
        {materia(consejeria_2)}] en {provincia}" — nunca se guarda como
        texto suelto (ADR-039 §1).
    """
    __tablename__ = 'unidades_organo_propio'
    __table_args__ = {'schema': 'public'}

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    consejerias_delegacion_id = db.Column(
        db.Integer,
        db.ForeignKey('public.consejerias_delegaciones_territoriales.id'),
        nullable=False,
        comment='FK a CONSEJERIAS_DELEGACIONES_TERRITORIALES. Composición de consejerías de esta unidad'
    )

    provincia = db.Column(
        db.String(100),
        nullable=True,
        comment='Provincia de la unidad. NULL reservado para servicios centrales'
    )

    sede_direccion = db.Column(
        db.String(300),
        nullable=True,
        comment='Dirección postal de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'
    )

    sede_telefono = db.Column(
        db.String(30),
        nullable=True,
        comment='Teléfono de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'
    )

    sede_correo = db.Column(
        db.String(150),
        nullable=True,
        comment='Correo de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'
    )

    codigo_bandeja_texto = db.Column(
        db.String(200),
        nullable=True,
        comment='Rótulo tal cual aparece en BandeJA, para localizar el nodo por texto en la automatización de #758'
    )

    consejerias_delegacion = db.relationship(
        'ConsejeriaDelegacionTerritorial',
        backref=db.backref('unidades_organo_propio', lazy='dynamic')
    )

    @property
    def delegacion_territorial_nombre(self):
        """Rótulo computado de cabecera: 'Delegación Territorial de X y de Y en <provincia>'."""
        consejeria = self.consejerias_delegacion
        if consejeria is None:
            return None
        nombre = f'Delegación Territorial de {_materia(consejeria.consejeria_1_nombre)}'
        if consejeria.consejeria_2_nombre:
            nombre += f' y de {_materia(consejeria.consejeria_2_nombre)}'
        if self.provincia:
            nombre += f' en {self.provincia}'
        return nombre

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<UnidadOrganoPropio {self.id}: {self.provincia!r}>'

    def __str__(self):
        """Representación legible para interfaz."""
        return self.delegacion_territorial_nombre or f'Unidad {self.id}'


class FirmantePortafirmas(db.Model):
    """
    Catálogo de firmantes de escritos, para el cuadro de firma de Port@firmas.

    PROPÓSITO:
        Quién puede figurar como firmante de un oficio/resolución: cargo,
        DNI (campo de búsqueda en Port@firmas) y unidad territorial. Consumido
        por la automatización de envío a Port@firmas (#758) y por el pie de
        firma de los escritos generados (ADR-039 §2).

    FILOSOFÍA:
        - Desacoplado de USUARIOS a propósito: el firmante real de un
          oficio/resolución (Delegado/a Territorial, Consejero/a) con
          frecuencia no tiene cuenta BDDAT — BDDAT lo usan tramitadores y
          técnicos, no necesariamente la autoridad firmante. Un checkbox en
          USUARIOS no tiene dónde colgar ese caso, que es el habitual para
          la firma final (ADR-039 §2, alternativa A descartada).
        - USUARIO_ID es nullable y se rellena solo si el firmante también es
          usuario BDDAT; no es requisito.
        - DNI es el campo de búsqueda a exponer en cualquier automatización:
          verificado en vivo en BandeJA que buscar por nombre da homónimos,
          por DNI es unívoco (ADR-039, Contexto).
        - Sin histórico de quién ocupó cada cargo cuándo (bajado de alcance,
          ver ADR-039 §Pendiente): VIGENTE/FECHA_BAJA son un estado simple,
          no una serie temporal.

    CAMPO DNI:
        - Documento de identidad del firmante. Campo de búsqueda principal.

    CAMPO VIGENTE / FECHA_BAJA:
        - VIGENTE=True mientras ejerce el cargo. FECHA_BAJA se rellena al
          desactivar, se mantiene el histórico de la fila (no se elimina).

    RELACIONES:
        - unidad_organo (N:1) → UNIDADES_ORGANO_PROPIO
        - usuario (N:1, opcional) → USUARIOS.usuario_id

    REGLAS DE NEGOCIO:
        La automatización de #758 hace lookup directo sobre esta tabla
        (DNI + cargo + unidad), no pasa por tokens de escrito — es un
        consumo distinto del mismo dato que el de Capa 1 (ADR-039 §4).
    """
    __tablename__ = 'firmantes_portafirmas'
    __table_args__ = (
        db.Index('idx_firmante_portafirmas_dni', 'dni'),
        {'schema': 'public'},
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    cargo = db.Column(
        db.String(200),
        nullable=False,
        comment='Cargo del firmante (p.ej. Delegado/a Territorial, Consejero/a)'
    )

    dni = db.Column(
        db.String(15),
        nullable=False,
        comment='Documento de identidad del firmante. Campo de búsqueda principal en Port@firmas'
    )

    nombre = db.Column(
        db.String(200),
        nullable=False,
        comment='Nombre completo del firmante'
    )

    unidad_organo_id = db.Column(
        db.Integer,
        db.ForeignKey('public.unidades_organo_propio.id'),
        nullable=False,
        comment='FK a UNIDADES_ORGANO_PROPIO. Unidad territorial del firmante'
    )

    vigente = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='TRUE mientras ejerce el cargo. FALSE tras causar baja (histórico, no se elimina la fila)'
    )

    fecha_baja = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha en la que dejó de ejercer el cargo. NULL mientras VIGENTE=True'
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('public.usuarios.id'),
        nullable=True,
        comment='FK a USUARIOS. Solo si el firmante también tiene cuenta BDDAT; no es requisito'
    )

    unidad_organo = db.relationship(
        'UnidadOrganoPropio',
        backref=db.backref('firmantes_portafirmas', lazy='dynamic')
    )

    usuario = db.relationship(
        'Usuario',
        backref=db.backref('firmante_portafirmas', lazy='dynamic')
    )

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<FirmantePortafirmas {self.id}: {self.nombre!r} ({self.cargo!r})>'

    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.nombre} — {self.cargo}'
