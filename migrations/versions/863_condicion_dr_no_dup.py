"""863_condicion_dr_no_dup

Revision ID: 863_condicion_dr_no_dup
Revises: 849_catalogo_replicado
Create Date: 2026-09-06

Issue #863 — la condición del requisito documental `DR_NO_DUP` estaba invertida.

`849_seed_catalogo_pendiente` (paso 3) la sembró como «solo se exige si la
solicitud incluye DUP»: `solicitud_incluye_dup EQ true`. Es justo al revés. La
declaración responsable de **no** necesidad de solicitar Declaración de Utilidad
Pública (DF 4ª del DL 26/2021) no tiene sentido en una solicitud que sí pide
DUP; se presenta precisamente cuando **no** se pide, que es cuando sirve para lo
que sirve — evitar la información pública si se cumple el resto de requisitos,
como dice la descripción del propio tipo de documento.

Efecto del error: en un expediente sin DUP el requisito no salía en el checklist
documental, de modo que la declaración que el titular presenta se quedaba en el
pool sin requisito al que casar; y en uno con DUP se pedía un documento que no
procede. Detectado al construir el expediente-tipo CONSULTAS_VARIOS_ESTADOS
(#862), un AAP+AAC sin DUP.

Por clave natural y no por `id` (REGLAS_DESARROLLO.md, §"reglas que solo se
notan instalando desde cero"): la fila se localiza por el código del tipo de
documento y el nombre de la variable, que son los mismos en cualquier base.
Idempotente por el filtro sobre el valor actual.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '863_condicion_dr_no_dup'
down_revision = '849_catalogo_replicado'
branch_labels = None
depends_on = None


# `CAST(... AS json)` y no `::json`: en un `sa.text()` los dos puntos abren un
# parámetro con nombre, y `:valor::json` se rompe al compilar.
_CONDICION_DR_NO_DUP = """
    UPDATE public.condiciones_requisito c
    SET valor = CAST(:valor AS json)
    FROM public.requisitos_documentales r
    JOIN public.tipos_documentos td ON td.id = r.tipo_documento_id
    JOIN public.catalogo_variables v ON v.nombre = 'solicitud_incluye_dup'
    WHERE c.requisito_id = r.id
      AND c.variable_id = v.id
      AND td.codigo = 'DR_NO_DUP'
      AND c.operador = 'EQ'
      AND CAST(c.valor AS text) = :valor_actual
"""


def upgrade():
    conn = op.get_bind()
    resultado = conn.execute(sa.text(_CONDICION_DR_NO_DUP),
                             {'valor': 'false', 'valor_actual': 'true'})
    print(f"[863] condición DR_NO_DUP corregida a 'solicitud_incluye_dup EQ false' "
          f"({resultado.rowcount} fila(s))")


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(_CONDICION_DR_NO_DUP),
                 {'valor': 'true', 'valor_actual': 'false'})
