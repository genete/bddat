# Procedimiento: generación de diagrama Mermaid desde imagen

**Contexto:** ver [GUIA_DIAGRAMAS_ESFTT.md](GUIA_DIAGRAMAS_ESFTT.md) para decisiones de diseño, estructura en capas y convenciones de color.

## Orientación
Antes de empezar, fijar UNA referencia de orientación (N/S/E/O respecto a la imagen
tal como se entrega) y mantenerla durante todo el análisis. No corregir la rotación
mentalmente — genera referencias contradictorias.

---

## PASO 1 — Inventario de bloques

Para cada bloque identificado, registrar:

| ID | Forma | Color relleno | Texto |
|----|-------|--------------|-------|

**Formas a distinguir:**
- Rectángulo → `[texto]`
- Rombo/diamante → `{texto}`
- Óvalo/elipse → `([texto])`
- Círculo → `((texto))`

**Colores:** nombrar con un único término consistente (Amarillo, Rojo, Azul...).
Si hay duda entre dos tonos similares, elegir el más próximo y mantenerlo.
No usar variantes del mismo color (Rojo / Rojo-naranja / Rojo-anaranjado).

---

## PASO 2 — Conteo de líneas por bloque (ANTES de rastrear)

Para cada bloque, contar visualmente cuántas líneas tocan ese bloque.
Registrar el total. Este paso es **obligatorio** antes del rastreo.

| ID | Bloque | Total líneas |
|----|--------|-------------|

**Por qué es crítico:** si al final del rastreo el número de conectores
asignados a un bloque no coincide con el conteo, falta o sobra una conexión.
Detectarlo aquí evita inventar conectores o perderlos.

---

## PASO 3 — Rastreo de conectores

Con el conteo del paso 2 como referencia, rastrear cada línea de extremo a extremo:

| ID | Desde | Hacia | Label | Notas |
|----|-------|-------|-------|-------|

**Reglas:**
- Una línea conecta a un bloque solo si **termina en él** (con o sin flecha).
  Si pasa cerca sin terminar, no conecta.
- Para polilíneas: inventariar los tramos (cambios de dirección) para
  describir el recorrido. Formato: `[(x1,y1)→(x2,y2)→(x3,y3)]`
- Verificar que el total de conectores por bloque coincide con el conteo del Paso 2.
  Si no cuadra → revisar antes de continuar.

---

## PASO 4 — Inventario de textos

Para cada texto visible:

| Texto | ¿Dentro de bloque o sobre línea? | Asignado a |
|-------|----------------------------------|------------|

**Regla de asignación:**
- Calcular el centroide del texto.
- Si cae dentro de la forma → texto del bloque.
- Si cae fuera pero próximo a una línea (con tolerancia) → label del conector.
- En caso de duda: aislar visualmente esa zona y razonar. Si persiste la duda, preguntar.

---

## PASO 5 — Generación del mmd

Con el inventario completo y verificado:

```
flowchart TD
    [definición de nodos con forma y ID]
    [definición de conectores con labels]
    [classDef por color]
    [class asignaciones]
```

Convertir a SVG:
```bash
mmdc -i fichero.mmd -o fichero.svg
```

Correcciones estéticas menores → editar el SVG directamente si no son
posibles en mmd.

---

## Errores frecuentes a evitar

| Error | Causa | Prevención |
|-------|-------|-----------|
| Conector inventado o perdido | No hacer conteo cruzado | Paso 2 obligatorio |
| Texto de conector asignado a bloque | No verificar centroide | Paso 4 con centroide |
| Polilínea interpretada como contenedor | Asumir por forma sin rastrear | Rastrear siempre extremos |
| Referencias de dirección contradictorias | Corregir rotación mentalmente | Fijar orientación al inicio |
