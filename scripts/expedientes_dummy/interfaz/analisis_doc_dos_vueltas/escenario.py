"""Expediente-tipo ANALISIS_DOC_DOS_VUELTAS, tramitado por la INTERFAZ (#1106).

Es el mismo escenario que `scripts/expedientes_dummy/analisis_doc_dos_vueltas.py` construye por la API (#814): análisis
documental con dos vueltas de subsanación y respuesta del titular siempre dentro de plazo, sin fase de Información
Pública / Consultas ni figura ambiental (AAP+AAC, proyecto EXENTO de instrumento ambiental). Termina con
ANALISIS_SOLICITUD completa y pendiente de cierre. Aquí, en cambio, se hace como lo haría una persona: rellenar el
alta, crear cada nodo desde el árbol, subir y vincular documentos, notificar, mover el reloj de desarrollo y
responder como el titular.

Recorrido: alta → campos técnicos del proyecto → fase ANALISIS_SOLICITUD → ANALISIS_DOCUMENTAL (checklist y
diagnóstico desfavorable) → dos vueltas de REQUERIMIENTO_SUBSANACION (ELABORAR con escrito generado, NOTIFICAR,
ESPERAR_PLAZO, respuesta del titular y un nuevo ANALIZAR; el diagnóstico de la 1.ª sale desfavorable y el de la 2.ª,
favorable) → COMUNICACION_INICIO_ADMISION (ELABORAR y NOTIFICAR).

Se ejecuta desde la raíz del repositorio:

    venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas --lista
    venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas --nuevo --usuario <SIGLAS> --password <CLAVE>

CREA DATOS REALES en la BD a la que apunte la aplicación y DEJA FIJADO el reloj de desarrollo en la fecha de la
última respuesta del titular («Usar fecha real» en la barra superior lo quita). Necesita la BD con las migraciones al
día y las plantillas DEMO de REQUERIMIENTO_SUBSANACION y COMUNICACION_INICIO_ADMISION
(`scripts/plantillas_demo.py --claves REQUERIMIENTO_SUBSANACION COMUNICACION_INICIO_ADMISION`).
"""
from ..lib import pasos
from ..lib.alta import DatosAlta
from ..lib.arbol import fecha_reloj, subir_al_pool
from ..lib.documentos import TipoDummy as T

CODIGO = 'ANALISIS_DOC_DOS_VUELTAS_UI'
CARPETA = 'analisis_doc_dos_vueltas'

# La marca que identifica este expediente en `Solicitud.observaciones`. NO es la del script de la API
# (`[DUMMY:ANALISIS_DOC_DOS_VUELTAS]`): la semilla de tests busca el suyo por `LIKE '[DUMMY:<CODIGO>]%'` y, con la
# misma marca, creería que ya existe y no lo construiría. El `]` hace que esta no case con aquella.
MARCA = f'[DUMMY:{CODIGO}]'
PROPOSITO = 'Expediente tramitado por la interfaz: análisis documental con respuesta dentro de plazo y dos vueltas.'

# Días naturales que dura el escenario completo: dos vueltas de requerimiento (10 días hábiles de plazo, respondidas 3
# hábiles antes de vencer) son unos 20; el resto es holgura. Solo tiene que ser suficiente: la base del calendario es
# hoy menos esto, y quedarse corto empujaría la última respuesta más allá de hoy (una fecha administrativa futura es
# un invariante del modelo desde #824).
DIAS_ESCENARIO = 45

# Días hábiles ANTES del vencimiento en que responde el titular. Es lo único fijo: la fecha sale de la «Fecha límite»
# que enseña el inspector, no de un número de días escrito a mano.
MARGEN_RESPUESTA_HABILES = 3

# Los tipos de documento que se suben: código (da el nombre del fichero), NOMBRE (el del catálogo, que es el que
# ofrecen los desplegables y el título de los requisitos del checklist) y origen (solo cambia el texto del PDF dummy).
TIPOS = {t.codigo: t for t in (
    T('MODELO_SOLICITUD', 'Modelo de solicitud de autorización de instalación', 'EXTERNO'),
    T('DOC_PROYECTO', 'Proyecto técnico del titular', 'EXTERNO'),
    T('JUSTIFICANTE_PAGO_TASA', 'Justificante de pago de la tasa', 'EXTERNO'),
    T('NIF_TITULAR', 'NIF del titular', 'EXTERNO'),
    T('ESCRITURAS_SOCIEDAD', 'Escrituras de constitución de la sociedad', 'EXTERNO'),
    T('PODER_REPRESENTACION', 'Poder de representación', 'EXTERNO'),
    T('MODELO_046', 'Modelo 046 de autoliquidación de tasa', 'EXTERNO'),
    T('MODELO_909', 'Modelo 909 carta de pago tasa', 'EXTERNO'),
    T('DR_NO_DUP', 'Declaración Responsable de No solicitud de Declaración de Utilidad Pública', 'EXTERNO'),
    T('OFICIO_REQUERIMIENTO', 'Oficio de requerimiento de subsanación', 'INTERNO'),
    T('SUBSANACION', 'Documentación de subsanación del titular', 'EXTERNO'),
    T('OFICIO_INICIO_ADMISION', 'Oficio de comunicación de inicio y admisión a trámite', 'INTERNO'),
    T('JUSTIFICANTE_NOTIFICA', 'Justificante Notifica-PNT', 'EXTERNO'),
)}
POR_TITULO = {t.nombre: t for t in TIPOS.values()}

# Lo presentado con la solicitud: cubre estos requisitos; el resto queda sin casar y son los defectos del primer
# diagnóstico.
PRESENTADOS = ('MODELO_SOLICITUD', 'DOC_PROYECTO', 'JUSTIFICANTE_PAGO_TASA')
# Lo que aporta el titular en la 1.ª vuelta, que deja el checklist aún incompleto. La 2.ª aporta todo lo que quede
# «Pendiente» (como el script de la API): así un requisito nuevo del catálogo —o cuya condición cambia, como
# DR_NO_DUP en #863— no deja un defecto de más en el diagnóstico final.
APORTES_VUELTA_1 = ('NIF_TITULAR', 'ESCRITURAS_SOCIEDAD', 'PODER_REPRESENTACION')


def datos_alta(fecha_base, opts):
    """Los datos del formulario: los mismos que usa el script de la API."""
    return DatosAlta(
        titulo='Línea subterránea 20 kV Ronda Sur — CT asociado',
        descripcion=('Nueva línea subterránea de distribución 20 kV y centro de transformación asociado, '
                     'íntegramente en suelo urbano.'),
        finalidad='Distribución de energía eléctrica en baja/media tensión',
        emplazamiento='T.M. de Mairena del Aljarafe (Sevilla)',
        proyecto=TIPOS['DOC_PROYECTO'], fecha_proyecto=fecha_base,
        escrito_solicitud=TIPOS['MODELO_SOLICITUD'], fecha_registro=fecha_base,
        observaciones=f'{MARCA} {PROPOSITO}',
        responsable=opts.responsable, titular=opts.titular)


# ---------------------------------------------------------------------------------------------------------
# Pasos
# ---------------------------------------------------------------------------------------------------------

def paso_proyecto(c):
    # Sin línea aérea y en suelo urbano es lo que lo deja EXENTO de instrumento ambiental (como en el script de la API).
    pasos.marcar_campos_proyecto(c, ('Sin línea aérea', 'Solo suelo urbano/urbanizable'), tension_kv=20)


def paso_fase(c):
    pasos.crear_fase(c, 'ANALISIS_SOLICITUD')


def paso_tramite_analisis(c):
    pasos.crear_en(c, 'fase', 'ANALISIS_DOCUMENTAL', 'el trámite ANALISIS_DOCUMENTAL', 'tramite_analisis')


def paso_tarea_analizar(c):
    pasos.crear_en(c, 'tramite_analisis', 'ANALIZAR', 'la tarea ANALIZAR', 'analizar')


def paso_subir_tasa(c):
    """El justificante de pago de la tasa se aporta aparte del alta: sube al pool con la fecha del reloj."""
    with c.s.paso('subir el justificante de pago de la tasa', 'pool: Subir fichero → Siguiente → tipo + fecha'):
        subir_al_pool(c.page, c.url, c.id, [(TIPOS['JUSTIFICANTE_PAGO_TASA'], fecha_reloj(c.page))])


def paso_vincular_presentacion(c):
    pasos.vincular_presentacion(c, 'analizar', [TIPOS[k] for k in PRESENTADOS])


def paso_diagnostico(c):
    pasos.producir_diagnostico(c, 'analizar', 'Desfavorable')


def vuelta(n):
    """Los pasos de la vuelta `n` de REQUERIMIENTO_SUBSANACION, con las claves `v<n>_…` para los ids de lo que crean."""
    k = f'v{n}'
    oficio, justificante = TIPOS['OFICIO_REQUERIMIENTO'], TIPOS['JUSTIFICANTE_NOTIFICA']

    def requerimiento(c):
        pasos.crear_en(c, 'fase', 'REQUERIMIENTO_SUBSANACION', f'el trámite REQUERIMIENTO_SUBSANACION #{n}',
                       f'{k}_tramite')
        pasos.crear_en(c, f'{k}_tramite', 'ELABORAR', 'la tarea ELABORAR', f'{k}_elaborar')

    def generar(c):
        pasos.generar_escrito(c, f'{k}_elaborar', esperados=('Pie de demostración',))

    def elaborar(c):
        pasos.elaborar_oficio(c, f'{k}_elaborar', oficio, f'Requerimiento de subsanación #{n}')

    def notificar(c):
        pasos.crear_en(c, f'{k}_tramite', 'NOTIFICAR', 'la tarea NOTIFICAR', f'{k}_notificar')
        pasos.notificar(c, f'{k}_notificar', oficio, justificante)

    def esperar(c):
        pasos.crear_en(c, f'{k}_tramite', 'ESPERAR_PLAZO', 'la tarea ESPERAR_PLAZO', f'{k}_esperar')
        pasos.disparar_plazo(c, f'{k}_esperar', oficio)

    def subsanacion(c):
        pasos.responder_en_plazo(c, f'{k}_esperar', TIPOS['SUBSANACION'], f'Respuesta a requerimiento #{n}',
                                 MARGEN_RESPUESTA_HABILES)

    def analizar(c):
        pasos.crear_en(c, f'{k}_tramite', 'ANALIZAR', f'la tarea ANALIZAR #{n}', f'{k}_analizar')
        pendientes = pasos.pendientes(c, f'{k}_analizar')
        sin_tipo = [t for t in pendientes if t not in POR_TITULO]
        if sin_tipo:
            raise RuntimeError(f'requisito del checklist sin tipo de documento en TIPOS (¿nuevo en el catálogo?): {sin_tipo}')
        aporta = list(APORTES_VUELTA_1) if n == 1 else [POR_TITULO[t].codigo for t in pendientes]
        ya_cubiertos = [a for a in aporta if TIPOS[a].nombre not in pendientes]
        if ya_cubiertos:
            raise RuntimeError(f'la vuelta {n} aporta algo que ya no está pendiente: {ya_cubiertos}')
        pasos.aportar_y_vincular(c, f'{k}_analizar', [TIPOS[a] for a in aporta])
        pasos.producir_diagnostico(c, f'{k}_analizar', 'Desfavorable' if n == 1 else 'Favorable')

    return [(f'{k}_requerimiento', requerimiento), (f'{k}_generar', generar), (f'{k}_oficio', elaborar),
            (f'{k}_notificar', notificar), (f'{k}_esperar', esperar), (f'{k}_subsanacion', subsanacion),
            (f'{k}_analizar', analizar)]


def paso_adm_tramite(c):
    pasos.crear_en(c, 'fase', 'COMUNICACION_INICIO_ADMISION', 'el trámite COMUNICACION_INICIO_ADMISION', 'adm_tramite')
    pasos.crear_en(c, 'adm_tramite', 'ELABORAR', 'la tarea ELABORAR', 'adm_elaborar')


def paso_adm_generar(c):
    pasos.generar_escrito(c, 'adm_elaborar', esperados=('Pie de demostración',))


def paso_adm_oficio(c):
    pasos.elaborar_oficio(c, 'adm_elaborar', TIPOS['OFICIO_INICIO_ADMISION'], 'Comunicación de inicio y admisión a trámite')


def paso_adm_notificar(c):
    pasos.crear_en(c, 'adm_tramite', 'NOTIFICAR', 'la tarea NOTIFICAR', 'adm_notificar')
    pasos.notificar(c, 'adm_notificar', TIPOS['OFICIO_INICIO_ADMISION'], TIPOS['JUSTIFICANTE_NOTIFICA'])


def paso_fin(c):
    """Solo lectura: vuelca el inspector de la fase, que ha de quedar completa y pendiente de cierre."""
    with c.s.paso('comprobar que la fase queda pendiente de cierre', 'ir + texto del inspector'):
        c.ir('fase')
        texto = ' '.join(c.insp.inner_text().split())
        c.s.aria('fase-final', c.insp)
        if 'PDTE_CIERRE' not in texto:
            raise RuntimeError(f'la fase no está pendiente de cierre: «{texto[:160]}»')


PASOS = [
    ('proyecto', paso_proyecto),
    ('fase', paso_fase),
    ('tramite_analisis', paso_tramite_analisis),
    ('tarea_analizar', paso_tarea_analizar),
    ('subir_tasa', paso_subir_tasa),
    ('vincular_presentacion', paso_vincular_presentacion),
    ('diagnostico', paso_diagnostico),
    *vuelta(1),
    *vuelta(2),
    ('adm_tramite', paso_adm_tramite),
    ('adm_generar', paso_adm_generar),
    ('adm_oficio', paso_adm_oficio),
    ('adm_notificar', paso_adm_notificar),
    ('fin', paso_fin),
]
