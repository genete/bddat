"""Añadir arquitectura ENTIDADES polimórfica (Issue #62)

Revision ID: c21871f08bb2
Revises: 51fcf34d6955
Create Date: 2026-02-02 17:10:44.946360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c21871f08bb2'
down_revision = '51fcf34d6955'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Crear tabla TIPOS_ENTIDADES en estructura (catálogo maestro)
    op.create_table(
        'tipos_entidades',
        sa.Column('id', sa.Integer(), nullable=False, comment='Identificador único del tipo de entidad'),
        sa.Column('codigo', sa.String(length=50), nullable=False, comment='Código único del tipo (ADMINISTRADO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION, EMPRESA_SERVICIO_PUBLICO)'),
        sa.Column('nombre', sa.String(length=100), nullable=False, comment='Nombre descriptivo del tipo de entidad'),
        sa.Column('tabla_metadatos', sa.String(length=100), nullable=False, comment='Nombre de la tabla entidades_* donde se almacenan los metadatos específicos (ej: entidades_administrados)'),
        sa.Column('puede_ser_solicitante', sa.Boolean(), nullable=False, server_default='false', comment='Indica si este tipo puede actuar como solicitante de solicitudes'),
        sa.Column('puede_ser_consultado', sa.Boolean(), nullable=False, server_default='false', comment='Indica si este tipo puede emitir informes como organismo consultado'),
        sa.Column('puede_publicar', sa.Boolean(), nullable=False, server_default='false', comment='Indica si este tipo puede publicar edictos (tablón ayuntamiento o BOP diputación)'),
        sa.Column('descripcion', sa.Text(), nullable=True, comment='Descripción detallada del tipo de entidad, roles y características'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
        schema='estructura'
    )
    op.create_index('ix_estructura_tipos_entidades_codigo', 'tipos_entidades', ['codigo'], unique=False, schema='estructura')
    
    # 2. Crear tabla ENTIDADES en public (tabla base polimórfica)
    op.create_table(
        'entidades',
        sa.Column('id', sa.Integer(), nullable=False, comment='Identificador único de la entidad'),
        sa.Column('tipo_entidad_id', sa.Integer(), nullable=False, comment='Tipo de entidad que determina tabla de metadatos. Define qué tabla entidades_* usar'),
        sa.Column('cif_nif', sa.String(length=20), nullable=True, comment='CIF/NIF/NIE normalizado. Mayúsculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos históricos'),
        sa.Column('nombre_completo', sa.String(length=200), nullable=False, comment='Razón social, nombre completo o nombre oficial. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial'),
        sa.Column('email', sa.String(length=120), nullable=True, comment='Email general de contacto. NO es el email de notificaciones (va en entidades_administrados)'),
        sa.Column('telefono', sa.String(length=20), nullable=True, comment='Teléfono de contacto general. Formato libre'),
        sa.Column('direccion', sa.Text(), nullable=True, comment='Calle, número, piso, puerta. Usar junto con codigo_postal y municipio_id (preferente para España)'),
        sa.Column('codigo_postal', sa.String(length=10), nullable=True, comment='Código postal. Texto libre. Futuro: sugerencias desde tabla codigos_postales'),
        sa.Column('municipio_id', sa.Integer(), nullable=True, comment='Municipio de la dirección. Preferente sobre direccion_fallback'),
        sa.Column('direccion_fallback', sa.Text(), nullable=True, comment='Dirección completa en texto libre. Para casos excepcionales (extranjero, datos históricos). Ej: "23, Peny Lane, St, 34523, London, England"'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true', comment='Indica si la entidad está activa. Borrado lógico'),
        sa.Column('notas', sa.Text(), nullable=True, comment='Observaciones generales sobre la entidad. Campo libre para anotaciones'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Fecha y hora de creación del registro'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Fecha y hora de última actualización'),
        sa.ForeignKeyConstraint(['municipio_id'], ['estructura.municipios.id'], ),
        sa.ForeignKeyConstraint(['tipo_entidad_id'], ['estructura.tipos_entidades.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cif_nif'),
        schema='public'
    )
    op.create_index('ix_public_entidades_activo', 'entidades', ['activo'], unique=False, schema='public')
    op.create_index('ix_public_entidades_cif_nif', 'entidades', ['cif_nif'], unique=False, schema='public')
    op.create_index('ix_public_entidades_municipio_id', 'entidades', ['municipio_id'], unique=False, schema='public')
    op.create_index('ix_public_entidades_nombre_completo', 'entidades', ['nombre_completo'], unique=False, schema='public')
    op.create_index('ix_public_entidades_tipo_entidad_id', 'entidades', ['tipo_entidad_id'], unique=False, schema='public')
    
    # 3. Crear tabla ENTIDADES_ADMINISTRADOS en public (metadatos específicos)
    op.create_table(
        'entidades_administrados',
        sa.Column('entidad_id', sa.Integer(), nullable=False, comment='Referencia a entidad base (PK y FK con CASCADE)'),
        sa.Column('email_notificaciones', sa.String(length=120), nullable=False, comment='Email oficial para sistema Notifica. Puede ser personal o corporativo donde se reciben notificaciones electrónicas oficiales'),
        sa.Column('representante_nif_cif', sa.String(length=20), nullable=True, comment='NIF/CIF de quien representa/gestiona. NULL si autorepresentado (persona física) o gestión corporativa directa. Normalizado como CIF/NIF'),
        sa.Column('representante_nombre', sa.String(length=200), nullable=True, comment='Nombre completo del representante. NULL si autorepresentado. Puede ser persona física (administrador único) o jurídica (consultora contratada)'),
        sa.Column('representante_telefono', sa.String(length=20), nullable=True, comment='Teléfono del representante. Contacto directo con quien gestiona'),
        sa.Column('representante_email', sa.String(length=120), nullable=True, comment='Email del representante. Email de contacto (NO oficial para notificaciones, solo coordinación)'),
        sa.Column('notas_representacion', sa.Text(), nullable=True, comment='Observaciones sobre la representación. Tipo de cargo o relación: "Administrador único", "Consultora ACME SL contratada", "Apoderado con poder notarial", etc.'),
        sa.CheckConstraint(
            "(representante_nif_cif IS NULL AND representante_nombre IS NULL) OR (representante_nif_cif IS NOT NULL AND representante_nombre IS NOT NULL)",
            name='chk_representante_coherente'
        ),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entidad_id'),
        schema='public'
    )
    op.create_index('ix_public_entidades_administrados_email_notificaciones', 'entidades_administrados', ['email_notificaciones'], unique=False, schema='public')
    op.create_index('ix_public_entidades_administrados_representante_nif_cif', 'entidades_administrados', ['representante_nif_cif'], unique=False, schema='public')
    
    # 4. Crear tabla ENTIDADES_EMPRESAS_SERVICIO_PUBLICO en public
    op.create_table(
        'entidades_empresas_servicio_publico',
        sa.Column('entidad_id', sa.Integer(), nullable=False, comment='Referencia a entidad base (PK y FK con CASCADE)'),
        sa.Column('nombre_comercial', sa.String(length=200), nullable=True, comment='Nombre comercial o marca si difiere de razón social. Ej: "Endesa Distribución" vs "Endesa Distribución Eléctrica S.L."'),
        sa.Column('sector', sa.String(length=100), nullable=True, comment='Sector de actividad. Ej: "Distribución eléctrica", "Telecomunicaciones", "Transporte ferroviario"'),
        sa.Column('codigo_cnae', sa.String(length=10), nullable=True, comment='Código CNAE de actividad económica. 4 dígitos. Ej: "3511" (Producción de energía eléctrica)'),
        sa.Column('observaciones', sa.Text(), nullable=True, comment='Notas adicionales sobre la empresa. Relaciones con otras operadoras, particularidades técnicas, histórico de incidencias'),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entidad_id'),
        schema='public'
    )
    
    # 5. Crear tabla ENTIDADES_ORGANISMOS_PUBLICOS en public
    op.create_table(
        'entidades_organismos_publicos',
        sa.Column('entidad_id', sa.Integer(), nullable=False, comment='Referencia a entidad base (PK y FK con CASCADE)'),
        sa.Column('codigo_dir3', sa.String(length=20), nullable=False, comment='Código DIR3 oficial (directorio común de unidades orgánicas). Identificador único de organismo público. Obligatorio'),
        sa.Column('ambito', sa.String(length=50), nullable=False, comment='Ámbito administrativo. Valores: "ESTATAL", "AUTONOMICO", "LOCAL", "EUROPEO"'),
        sa.Column('tipo_organismo', sa.String(length=100), nullable=True, comment='Clasificación del organismo. Ej: "Ministerio", "Consejería", "Dirección General", "Agencia", "Organismo Autónomo"'),
        sa.Column('url_sede_electronica', sa.String(length=255), nullable=True, comment='URL de la sede electrónica del organismo. Para envíos telemáticos y consulta de servicios'),
        sa.Column('observaciones', sa.Text(), nullable=True, comment='Notas adicionales sobre el organismo. Competencias específicas, particularidades procedimentales, contactos alternativos'),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entidad_id'),
        schema='public'
    )
    op.create_index('ix_public_entidades_organismos_publicos_codigo_dir3', 'entidades_organismos_publicos', ['codigo_dir3'], unique=True, schema='public')
    
    # 6. Crear tabla ENTIDADES_AYUNTAMIENTOS en public
    op.create_table(
        'entidades_ayuntamientos',
        sa.Column('entidad_id', sa.Integer(), nullable=False, comment='Referencia a entidad base (PK y FK con CASCADE)'),
        sa.Column('codigo_dir3', sa.String(length=20), nullable=False, comment='Código DIR3 oficial del ayuntamiento. Obligatorio para identificación única en sistemas oficiales'),
        sa.Column('codigo_ine_municipio', sa.String(length=5), nullable=False, comment='Código INE de 5 dígitos del municipio. Relaciona con estructura.municipios'),
        sa.Column('url_tablon_edictos', sa.String(length=255), nullable=True, comment='URL del tablón de anuncios/edictos electrónico. Para verificar publicaciones obligatorias'),
        sa.Column('observaciones', sa.Text(), nullable=True, comment='Notas adicionales sobre el ayuntamiento. Horarios especiales, contactos técnicos, particularidades de publicación'),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entidad_id'),
        schema='public'
    )
    op.create_index('ix_public_entidades_ayuntamientos_codigo_dir3', 'entidades_ayuntamientos', ['codigo_dir3'], unique=True, schema='public')
    op.create_index('ix_public_entidades_ayuntamientos_codigo_ine_municipio', 'entidades_ayuntamientos', ['codigo_ine_municipio'], unique=False, schema='public')
    
    # 7. Crear tabla ENTIDADES_DIPUTACIONES en public
    op.create_table(
        'entidades_diputaciones',
        sa.Column('entidad_id', sa.Integer(), nullable=False, comment='Referencia a entidad base (PK y FK con CASCADE)'),
        sa.Column('codigo_dir3', sa.String(length=20), nullable=False, comment='Código DIR3 oficial de la diputación. Obligatorio'),
        sa.Column('codigo_ine_municipio_sede', sa.String(length=5), nullable=False, comment='Código INE del municipio donde tiene sede (capital provincial). 5 dígitos'),
        sa.Column('url_bop', sa.String(length=255), nullable=True, comment='URL del Boletín Oficial de la Provincia (BOP) electrónico. Para consulta de publicaciones'),
        sa.Column('email_publicacion_bop', sa.String(length=255), nullable=True, comment='Email para envío de solicitudes de publicación en BOP. Dirección de contacto del servicio de publicaciones'),
        sa.Column('observaciones', sa.Text(), nullable=True, comment='Notas adicionales sobre la diputación. Procedimientos de publicación, plazos, contactos específicos'),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entidad_id'),
        schema='public'
    )
    op.create_index('ix_public_entidades_diputaciones_codigo_dir3', 'entidades_diputaciones', ['codigo_dir3'], unique=True, schema='public')
    op.create_index('ix_public_entidades_diputaciones_codigo_ine_municipio_sede', 'entidades_diputaciones', ['codigo_ine_municipio_sede'], unique=False, schema='public')


def downgrade():
    # Borrar en orden inverso (de dependientes a independientes)
    op.drop_table('entidades_diputaciones', schema='public')
    op.drop_table('entidades_ayuntamientos', schema='public')
    op.drop_table('entidades_organismos_publicos', schema='public')
    op.drop_table('entidades_empresas_servicio_publico', schema='public')
    op.drop_table('entidades_administrados', schema='public')
    op.drop_table('entidades', schema='public')
    op.drop_table('tipos_entidades', schema='estructura')
