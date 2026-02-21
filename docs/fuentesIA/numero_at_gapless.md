# Numeración AT sin huecos y sin race condition

**Issue relacionado:** #120
**Implementado en:** migración `606202414595`
**Fecha:** 2026-02-21

---

## El problema

El número de expediente (`numero_at`, mostrado como `AT-XXXX`) es un
identificador administrativo que aparece en documentos oficiales, notificaciones
y resoluciones firmadas. Por tanto tiene dos requisitos estrictos:

1. **Sin huecos** — La secuencia debe ser consecutiva. Un hueco implica que
   existe un expediente "fantasma" que nadie puede encontrar, lo que genera
   dudas legales y de auditoría.

2. **Sin race condition** — Si dos tramitadores crean un expediente al mismo
   tiempo, cada uno debe obtener un número distinto sin errores.

---

## Por qué el mecanismo original fallaba

El wizard calculaba el número así:

```python
ultimo_numero = db.session.query(db.func.max(Expediente.numero_at)).scalar() or 0
numero_at = ultimo_numero + 1
```

Con dos transacciones concurrentes (tramitador A y tramitador B):

```
A lee  MAX = 42  →  calcula 43
B lee  MAX = 42  →  calcula 43   ← mismo número
A hace flush y commit  →  AT-43 guardado
B hace flush          →  UNIQUE violation  →  error críptico para el usuario
```

La restricción `UNIQUE` en `numero_at` evitaba corrupción de datos, pero el
tramitador B recibía un mensaje de error SQL incomprensible y tenía que repetir
el proceso desde el paso 3.

---

## Por qué una secuencia PostgreSQL (`nextval`) tampoco funciona

Una secuencia PostgreSQL resuelve la race condition pero introduce huecos:

```sql
SELECT nextval('seq_numero_at');  -- devuelve 43
-- si la transacción hace ROLLBACK, el 43 se pierde para siempre
-- la siguiente transacción obtiene 44  →  hueco en 43
```

`nextval()` es **irreversible por diseño**: garantiza unicidad precisamente
porque nunca deshace el incremento, ni siquiera en rollback.

---

## La solución: tabla contador con `UPDATE … RETURNING`

```sql
CREATE TABLE public.contador_numero_at (valor INTEGER NOT NULL);
INSERT INTO public.contador_numero_at VALUES (<MAX actual>);
```

```python
numero_at = db.session.execute(
    db.text("UPDATE public.contador_numero_at SET valor = valor + 1 RETURNING valor")
).scalar()
```

### Por qué funciona

- **Sin race condition:** PostgreSQL aplica un lock de fila en el `UPDATE`.
  Si A y B llegan al mismo tiempo, B espera a que A confirme o cancele.
  Nunca devuelve el mismo valor a dos sesiones.

- **Sin huecos:** El `UPDATE` es parte de la transacción normal. Si el wizard
  falla después de obtener el número (error de validación, cancel del usuario,
  caída de red), la transacción hace rollback y el `UPDATE` también revierte.
  El contador vuelve al valor anterior y la siguiente transacción obtiene el
  mismo número: ningún hueco.

### Comparativa

| Mecanismo              | Race condition | Hueco en rollback | Hueco en cancel |
|------------------------|:--------------:|:-----------------:|:---------------:|
| `MAX+1` (original)     | ✅ posible     | ✅ no             | ✅ no           |
| `nextval()` secuencia  | ✅ no          | ❌ sí             | ❌ sí           |
| `UPDATE … RETURNING`   | ✅ no          | ✅ no             | ✅ no           |

---

## Ajuste antes del go-live (issue #120)

Cuando se conozca el volumen de expedientes legacy (migración desde Access
2000, schema `legacy`), ejecutar **una sola vez** en producción:

```sql
-- Sustituir <techo_legacy> por el número AT más alto de los expedientes
-- migrados desde el sistema legacy. Los nuevos expedientes BDDAT empezarán
-- desde techo_legacy + 1, separando claramente ambas series.
UPDATE public.contador_numero_at
SET valor = <techo_legacy>;
```

### Ejemplo

Si el legacy tiene expedientes hasta AT-4821:

```sql
UPDATE public.contador_numero_at SET valor = 4821;
-- El siguiente expediente BDDAT será AT-4822
```

### ¿Se puede cambiar después?

- **Subir la base** (ir a un número más alto): posible, pero los expedientes
  ya creados en BDDAT tendrán números en el rango anterior. Si aparecen en
  documentos oficiales firmados, cambiarlos tiene implicaciones legales.

- **Bajar la base**: imposible sin renumerar, ya que `numero_at` tiene
  restricción `UNIQUE`. Y renumerar expedientes que constan en documentos
  firmados es problemático legalmente.

**Conclusión:** la decisión del número base es efectivamente de una sola vez,
aunque técnicamente sea un simple `UPDATE` de una fila.

---

## Ficheros modificados

| Fichero | Cambio |
|---------|--------|
| `migrations/versions/606202414595_contador_gapless_numero_at.py` | Crea tabla `contador_numero_at` |
| `app/routes/wizard_expediente.py` | Sustituye `MAX+1` por `UPDATE … RETURNING` |
