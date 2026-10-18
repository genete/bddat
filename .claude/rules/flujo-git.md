# Flujo git: los fallos que ya se repitieron

Detalle en `docs/guias/REGLAS_DESARROLLO.md` (§Ramas, §Commits, §Issues y pull requests).

- **Rama antes de la primera edición.** Tras leer el issue y antes de cualquier `Edit`/`Write` sobre código: `git checkout -b feature/issue-NN-descripcion`. También al reanudar un issue tras mergear su fase anterior (la rama activa vuelve a ser `develop`). Los documentos de diseño vivos (ADRs, `docs/diseño/`) van por commit directo a `develop`.
- **Sesiones en la nube: ignorar la rama `claude/*`.** La plataforma asigna una rama con nombre aleatorio; Carlos autoriza expresamente no usarla (2026-10-18). Antes de la primera edición, crear desde `develop` la rama con el nombre que Carlos indique en el primer mensaje, o `feature/issue-NN-descripcion` si hay issue; sin nombre ni issue, preguntarlo antes de editar. Push solo a esa rama; nunca commitear en la `claude/*`. Si no llega a tener commits ni push, no existe en origin y no hay nada que borrar. Recordatorio automático en `.claude/hooks/session-start.sh`.
- **Verificar la rama con una llamada real antes de commitear o pushear.** El `gitStatus` del inicio de la sesión caduca: Carlos puede trabajar en paralelo en el mismo directorio. Si la rama no es la esperada, no tocar la del usuario: crear una de seguridad desde `develop` y devolver el repo a su rama al terminar.
- **`Refs #N`, no `Closes #N`, en issues de varias fases.** El skill `/pr` añade `Closes #XX` por defecto: sustituirlo hasta el PR de cierre.
