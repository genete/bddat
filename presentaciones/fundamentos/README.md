# Presentación «Fundamentos tecnológicos»

Diecisiete fichas, cada una un HTML autónomo en `fichas/`, compiladas en un solo
`index.html` que es lo que se publica en GitHub Pages.

## Manejo

- **Avanzar:** clic, `→`, espacio, `Av Pág` o `Intro`. **Retroceder:** `←`, `Re Pág` o `Retroceso`.
- Al terminar los pasos de una ficha pasa a la siguiente; al retroceder desde el primer paso,
  vuelve al último de la anterior.
- `Inicio` y `Fin`: primera ficha y último paso de la última. `f`: pantalla completa.
- Una dirección acabada en `#7` empieza en la ficha 7.

## Cómo se edita

La fuente de verdad son las fichas de `fichas/` (una ficha se puede abrir sola en el
navegador). GitHub Pages no compila: si se cambia una ficha, hay que regenerar `index.html`
y versionarlo.

```
D:/BDDAT/venv/Scripts/python.exe presentaciones/fundamentos/compilar.py
```

El orden de la presentación está en la lista `ORDEN` de `compilar.py`.

## Convenciones de las fichas

- Un bloque de estilos común y un lienzo fijo de 1280x720 que se escala a la ventana.
- Cada elemento lleva `data-paso="N"` y aparece al llegar al paso N.
- Azul: petición, lo que va. Verde: respuesta, lo que vuelve. Ámbar con etiqueta: lo que aún
  es plan o está por decidir.
