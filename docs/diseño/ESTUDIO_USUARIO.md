# Estudio de usuario — Fase 2

> Insumo neutro para el revamping. Recopila perfiles, contexto, flujo operativo real, dolor y aspiraciones del servicio. **No contiene conclusiones de diseño** — esas vienen en fase 4 tras cruzar con la auditoría UI y el inventario de backend.
> Fecha del corte: 2026-05-28.

---

## 1. Perfiles y escala

| Perfil | Nº usuarios (provincial) | Notas |
|---|---|---|
| ADMIN | 1 | administrador del sistema |
| SUPERVISOR | 2-3 | jefatura de servicio + usuario avanzado (impulsor) |
| TRAMITADOR | 10-12 (<20) | **perfil dominante** — la UI se optimiza para él |
| ADMINISTRATIVO | 4-6 | notificaciones, publicaciones |

- **Escala provincial:** ~20 usuarios.
- **Escala potencial (multi-provincia + servicios centrales):** ~500. La arquitectura debe aguantarla sin reescritura.
- **Formación tecnológica:** mix realista. Ofimática + apps corporativas vía web; no power users pero no se asustan. Resistencia al cambio variable; predominan ganas de cambio.
- **No hay perfil "ocasional"** — todos uso diario intenso. Eso autoriza densidad y atajos.
- **Subgrupos funcionales:** Distribución y Transporte (DyT) — trabajo por lotes, alta rotación. Renovables — pocos expedientes, larga duración, trabajo pausado. Mismo flujo, distinta velocidad.

---

## 2. Entorno técnico

- **Dispositivo:** PC sobremesa o portátil acoplado a monitor. Mínimo 1080p garantizado.
- **Pantallas:** dual-monitor frecuente. BDDAT en la principal; secundaria para correo/ofimática.
- **Sin móvil ni tablet.** Desktop-first. Pero la ventana no es siempre maximizada → debe verse decente a 1280-1400 cuando se reduce.
- **SO:** Windows 11 mayoritario (Win 10 en transición).
- **Navegador:** Chrome dominante, Edge como fallback. Sin restricciones legacy.
- **Convivencia con otras apps:** Notifica, BandeJA, PortaFirmas, PTWANDA, Outlook, explorador de archivos, PDF, navegador con BOJA. **BDDAT no es kiosko** — debe convivir.
- **Contexto físico:** oficina abierta y silenciosa, concentración, interrupciones moderadas, **mentoría informal** (veteranos ayudando). La UI tiene que ser **explicable a otro de un vistazo**.

---

## 3. Volumen y ritmos

### 3.1 Carga por tramitador

| Subgrupo | Asignados | Vivos | Activos |
|---|---|---|---|
| DyT | 50-80 | 15-20 (rotación alta, "zombies que despiertan") | grueso |
| Renovables | 15-20 | ~50% activos | larga duración (años) |

### 3.2 Vida media de expediente

- **60%** corta duración (2-3 semanas).
- **40%** larga (meses-años).
- Complejidad correlacionada con longevidad.

### 3.3 Entradas anuales (servicio entero)

| Año | Expedientes |
|---|---|
| 2022 | 441 |
| 2023 | 317 |
| 2024 | 277 |
| 2025 | 365 |
| 2026 (parcial) | 145 |

Volumen acumulado legacy: 15.000+ filas (activación a demanda).

### 3.4 Cadencia diaria (tramitador DyT típico)

- 4-5 escritos generados.
- 5-8 entradas procesadas.
- 1-2 lotes de revisión de plazos/pendientes.

### 3.5 Picos estacionales

- DyT: cierre de año (autorizaciones de explotación).
- Renovables: sin picos claros (proyectos largos, ritmo constante).

---

## 4. Ecosistema de herramientas — flujo operativo real

### 4.1 Inventario y sustitución

| Herramienta | Función | ¿BDDAT la sustituye? |
|---|---|---|
| BandeJA | comunicaciones in/out oficiales, ruta de firma | **NO** — oficial. Solo integrar/enlazar |
| PTWANDA | entrada externa | **NO** — externo |
| Notifica | notificación oficial | **NO** — oficial |
| PortaFirmas | firma | **NO** — oficial |
| Carpetas del servidor | verdad documental | **NO sustituir** — indexar/enlazar |
| Access (DyT) | registro de expediente + plantillas básicas | **SÍ** — parcial ya |
| Hoja Calc "pendiente de *" | seguimiento operativo | **SÍ** — el núcleo |
| Hoja Renovables (control ad hoc) | seguimiento alternativo | **SÍ** |

### 4.2 Ciclo típico

1. Entrada por BandeJA o PTWANDA.
2. Encaje en carpeta del servidor + anotación en Calc.
3. Si nuevo expediente, alta en Access.
4. Revisión reactiva de plazos, pendientes, notificaciones.
5. Generación de escritos (Access plantillas o redacción a mano).
6. Subida a BandeJA → firma → vuelta firmado → reasignación a administrativo.
7. Notificación oficial (administrativo) + verificación visual en carpeta.
8. Anotación en Calc del cambio de estado.
9. Bucle.

---

## 5. Dolor del flujo actual

- **Dato escrito en N sitios** (Calc + Access + nombre fichero + asunto BandeJA).
- **Navegación tortuosa** en carpetas del servidor para encontrar documentos.
- **Copy/paste constante** para rellenar plantillas.
- **Nombrar ficheros y redactar asuntos BandeJA a mano.**
- **Actualizar Calc reactivamente** cuando cambia algo.
- **Buscar info de notificación/publicación** en carpetas para volcarla a Calc.
- **"Rehacer el estado del expediente"** al retomarlo: releer documentos, reconstruir contexto. Tiempo perdido cada vez.
- **Memoria frágil sin recordatorios** del propio sistema → tareas olvidadas hasta que duelen.
- **50% del tiempo del técnico** se va en mover datos, no en decidir/analizar.

---

## 6. Hacks personales y trabajo invisible

- Hojas propias paralelas a la oficial ("no me gusta la que propone la jefatura").
- Estadísticas para jefatura **calculadas a mano** sobre hojas propias.
- Anotaciones a mano que luego se reescriben en el ordenador.
- Macro personal en Calc para abrir carpeta del expediente.
- "Confío en mi memoria" → reportes no se hacen, estadísticas inexistentes.

> *"El conocimiento y la falta de disciplina es la peor mezcla."*

Cada usuario tiene su forma de trabajar. La existencia misma de los hacks delata que el sistema oficial es insuficiente — **BDDAT sirve cuando los hacks desaparecen, no cuando convive con ellos**.

---

## 7. Operaciones críticas (hoy, fuera de BDDAT)

### 7.1 Búsqueda

- Identificador primario: **número de expediente**.
- Secundarios: peticionario, municipio, nombre proyecto, dirección.
- Filtros sobre vista única (cultura Calc) > múltiples vistas predefinidas.
- Filtros típicos: tipo titular (Edistribución/otras/resto), estado pendiente, etiqueta FIN para ocultar cerrados.

### 7.2 Generación de escritos

- **Oficios simples:** cubiertos razonablemente bien por plantillas Access.
- **Requerimientos:** se redactan en Access antes de combinar.
- **Resoluciones:** retoque manual frecuente — listado de alegaciones, listado de organismos + estado, condicionados alternativos según contexto. **Frontera donde BDDAT debe superar a Access.**

### 7.3 Verificación de estados externos

- Notificación/publicación se verifica abriendo la carpeta del servidor.
- Si los administrativos actúan directamente en BDDAT al notificar/publicar, ese estado fluye automáticamente.
- Necesidad acotada de UI: **atajo "abrir carpeta del expediente" omnipresente** (la macro de Calc actual, pero accesible desde cualquier pantalla).

### 7.4 Acciones masivas

- **No prioritarias.** Diversidad de expedientes impide acciones masivas operativas.
- Excepciones: asignación de expedientes a usuario desde supervisor; migración legacy en lote.

### 7.5 Caso de uso descubierto — compilación de expediente

- Recurso de alzada o contencioso requiere **compilar el expediente completo** (documentos + bitácora + estado) en un paquete exportable.
- No es generación de un documento, es generación de un dossier.
- No detectado en la auditoría UI ni mencionado en bloques previos.

---

## 8. Aspiraciones

### 8.1 Top 3 "varita mágica"

1. **Estadísticas automáticas** para supervisor y servicios centrales.
2. **Estado del expediente accesible de un vistazo** para el tramitador (memoria externa fiable).
3. **Compilación de expediente** para recurso de alzada / contencioso.

### 8.2 Métricas de éxito a 6-12 meses

- **No hay marcha atrás:** la adopción es de facto obligada — jefatura percibirá la no-evolución de expedientes.
- **Riesgo principal a controlar:** retraso en tramitación por curva de aprendizaje.
- **Indicador implícito de éxito:** desaparición de hojas Excel personales y de la dependencia de Access.

### 8.3 Lo que no debe ser

- **No "interfaz para tontos".** La facilidad debe venir de **limpieza y organización**, no de simplismo. Densidad sí, condescendencia no.
- **No replicar a Chrono:** buen backend mal expresado en UI. Es el fallo más común y el más caro.

---

## 9. Fuera de alcance

- **Notifica, login con certificado, integración con BandeJA**: requieren ADA. BDDAT no aspira a absorberlos.
- Si la ADA adoptase BDDAT en el futuro, los cambios de interfaz con esos sistemas serán problema suyo, no del proyecto actual.

---

## 10. Hipótesis de principios de diseño (a validar en fase 4)

No son decisiones — son patrones que emergen del estudio y que el plan de diseño debe contrastar contra la auditoría UI y el inventario de backend:

- Densidad sí, simplismo no.
- Una vista única + filtros potentes y guardables > muchas vistas predefinidas.
- Estructura discreta e indexable > campos libres genéricos. Bitácora datada con autor donde haga falta narrativa.
- Sistema empuja con semáforos y alertas; no espera disciplina del usuario.
- Mismo flujo DyT/Renovables, distinta velocidad → no bifurcar UI.
- Convivencia con otras apps, no kiosko. Atajo a carpeta del servidor omnipresente.
- Búsqueda global por número de expediente como operación de localización primaria.
- BDDAT como **fuente única de verdad** para lo que reemplaza (Calc + Access); enlaza pero no duplica lo oficial (BandeJA, Notifica, carpetas).
- El perfil ADMINISTRATIVO probablemente necesita su propia vista enfocada (registrar notificación/publicación rápido), no una versión reducida de la del tramitador.

---

## 11. Limitaciones del estudio

- **No cubre el backend.** Varias preguntas (estadísticas, compilación de expediente, modelo de estado, validaciones, motor) se formularon sin conocer modelos ni servicios actuales, lo cual puede haber sesgado las respuestas.
- **Pendiente fase intermedia (2.5):** inventario de backend — modelos, motor, servicios, presentación del POC, documentación MD del proyecto, issues abiertos. Sin esto, las conclusiones de fase 3-4 llegarían incompletas.
- **Referencias modernas de UI ausentes del lado del usuario.** Las que conoce son corporativas (PTWANDA, BandeJA, PortaFirmas, Chrono). Las referencias modernas (Linear, Stripe, Sentry…) las traerá la fase 3 desde fuera y habrá que validar su encaje cultural con el servicio.
