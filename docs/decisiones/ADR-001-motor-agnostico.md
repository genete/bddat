---
id: ADR-001
título: Motor de reglas agnóstico de dominio
fecha: 2026-04-21
estado: implementado
---

## Decisión
El motor de reglas no conoce el dominio BDDAT. No importa modelos. No hace queries.
Recibe `(accion, sujeto, variables: dict)` y evalúa reglas en BD contra ese dict.
El ContextAssembler (BDDAT-aware) ensambla el dict antes de llamar al motor.

## Por qué
El motor anterior mezclaba evaluación con conocimiento del dominio: cada variable nueva
requería tocar el motor. Con BD de reglas aún vacía, el coste de refactorizar era mínimo.

## Cómo está implementado
- `app/services/motor_reglas.py` — motor agnóstico
- `app/services/assembler.py` — ContextAssembler + evaluar_multi()
- `app/services/variables/` — Variable Registry (@variable decorator)
- Tablas: reglas_motor, condiciones_regla, catalogo_variables, normas

## Alternativa descartada
Añadir VARIABLE_SOLICITUD/VARIABLE_TRAMITE como criterios genéricos al motor anterior.
Habría dado el 80% del beneficio con el 20% del trabajo, pero dejaba lógica de dominio
hardcodeada en el motor para siempre.
