# DISEÑO — Numeración AT sin huecos (contador con UPDATE…RETURNING)

> **Issue relacionado:** #120
> **Implementado en:** migración `606202414595`
> **Fecha implementación:** 2026-02-21

---

## El problema

El número de expediente (`numero_at`, mostrado como `AT-XXXX`) es un identificador
administrativo que aparece en documentos oficiales, notificaciones y resoluciones
firmadas. Tiene dos requisitos estrictos:

1. **Sin huecos** — La secuencia debe ser consecutiva. Un hueco implica un expediente
   "fantasma" que genera dudas legales y de auditoría.
2. **Sin race condition** — Si dos tramitadores crean un expediente al mismo tiempo,
   cada uno debe obtener un número distinto sin errores.

---

## Por qué el mecanismo original fallaba

El wizard calculaba el número con `MAX+1`. Con dos transacciones concurrentes:

```
A lee  MAX = 42  →  calcula 43
B lee  MAX = 42  →  calcula 43   ← mismo número
A commit  →  AT-43 guardado
B flush   →  UNIQUE violation  →  error críptico para el usuario
```

La restricción `UNIQUE` en `numero_at` evitaba corrupción, pero el tramitador B
recibía un error SQL incomprensible.

## Por qué una secuencia PostgreSQL tampoco funciona

`nextval()` resuelve la race condition pero introduce huecos: el incremento es
**irreversible por diseño** — en caso de ROLLBACK el número se pierde para siempre.

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

**Por qué funciona:**
- **Sin race condition:** PostgreSQL aplica un lock de fila en el `UPDATE`. B espera a que A confirme o cancele. Nunca devuelve el mismo valor a dos sesiones.
- **Sin huecos:** El `UPDATE` forma parte de la transacción. Si el wizard falla después de obtener el número, la transacción hace rollback y el contador revierte. La siguiente transacción obtiene el mismo número: ningún hueco.

### Comparativa

| Mecanismo              | Race condition | Hueco en rollback | Hueco en cancel |
|------------------------|:--------------:|:-----------------:|:---------------:|
| `MAX+1` (original)     | posible        | no                | no              |
| `nextval()` secuencia  | no             | sí                | sí              |
| `UPDATE … RETURNING`   | no             | no                | no              |

---

## Ajuste antes del go-live (issue #120)

Cuando se conozca el volumen de expedientes legacy (migración desde Access 2000),
ejecutar **una sola vez** en producción:

```sql
-- Sustituir <techo_legacy> por el número AT más alto de los expedientes migrados.
-- Los nuevos expedientes BDDAT empezarán desde techo_legacy + 1.
UPDATE public.contador_numero_at SET valor = <techo_legacy>;
```

**Esta decisión es efectivamente de una sola vez:** subir la base es posible pero
tiene implicaciones legales si los expedientes ya aparecen en documentos firmados.
Bajar la base es imposible sin renumerar (viola restricción `UNIQUE`).

---

## Ficheros implicados

| Fichero | Cambio |
|---------|--------|
| `migrations/versions/606202414595_contador_gapless_numero_at.py` | Crea tabla `contador_numero_at` |
| `app/routes/wizard_expediente.py` | Sustituye `MAX+1` por `UPDATE … RETURNING` |
