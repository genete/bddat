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
