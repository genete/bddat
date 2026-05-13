# Guía de administración — BDDAT

Procedimientos operativos para el administrador del sistema.

---

## 1. Carga anual del calendario de días inhábiles

### Cuándo ejecutar

Cada año en **noviembre**, tras la publicación de la Orden de la Junta de Andalucía
que fija el calendario de festivos del año siguiente (BOJA, habitualmente en octubre-noviembre).

Si el sistema detecta que no hay datos para el año siguiente, mostrará un banner de aviso
visible solo para usuarios con rol ADMIN en todas las páginas.

### Comando

```bash
# En el servidor (desde el directorio raíz del proyecto):
source venv/Scripts/activate   # Windows
# source venv/bin/activate     # Linux/Mac

flask inhabiles importar --year 2027
```

El año por defecto es el siguiente al actual, por lo que en noviembre de 2026 basta con:

```bash
flask inhabiles importar
```

### Verificar disponibilidad de datos antes de importar

```bash
flask inhabiles importar --year 2027 --dry-run
```

Muestra los festivos que se importarían sin modificar la base de datos.

### Opciones

| Opción | Defecto | Descripción |
|--------|---------|-------------|
| `--year` | año siguiente | Año a importar |
| `--province` | `CÁDIZ` | Provincia (mayúsculas exactas de la API) |
| `--municipio` | `CÁDIZ` | Municipio (mayúsculas exactas de la API) |
| `--dry-run` | desactivado | Solo muestra sin insertar |

### Fuente de datos

API pública de la Junta de Andalucía, sin autenticación:

```
https://www.juntadeandalucia.es/ssdigitales/datasets/work-calendar/
  work-calendar/get/search_calendar_weekends?province=CÁDIZ&municipality=CÁDIZ&year=2027
```

Los festivos autonómicos y nacionales se identifican porque `province` y `municipality`
llegan vacíos en la respuesta. Los locales llevan la provincia/municipio rellenos.

### Qué importa exactamente

El comando importa todos los días inhábiles **laborables** del año para el ámbito
provincia+municipio configurado (por defecto Cádiz capital):

- Festivos nacionales
- Festivos autonómicos andaluces
- Festivos provinciales de Cádiz
- Festivos locales de Cádiz capital

Los sábados y domingos se descartan: el motor de plazos ya los excluye por cálculo.

### Si la API no está disponible

Usar los JSON estáticos de respaldo en `app/data/dias_inhabiles/` como referencia
para carga manual. Son festivos autonómicos sin locales de Cádiz, válidos como
aproximación hasta que la API vuelva a estar operativa.

---

## 2. Verificar el estado del calendario

```sql
-- En psql o flask shell:
SELECT EXTRACT(year FROM fecha) AS anyo, COUNT(*) AS festivos
FROM dias_inhabiles
GROUP BY anyo
ORDER BY anyo;
```

Un año típico de Andalucía (provincia Cádiz) tiene entre 12 y 14 festivos laborables.
