# Presentación «Cómo funciona BDDAT»

Los principios de funcionamiento de BDDAT para el personal técnico de la ADA: el
procedimiento y cómo lo resuelve BDDAT, sin entrar en la tecnología (que está en
`../fundamentos/`). Veintinueve fichas en ocho bloques; el guion, con lo que se dice en
cada una, está en [`GUION.md`](GUION.md).

## Manejo

El de `../fundamentos/`:

- **Avanzar:** clic, `→`, espacio, `Av Pág` o `Intro`. **Retroceder:** `←`, `Re Pág` o `Retroceso`.
- Al terminar los pasos de una ficha pasa a la siguiente; al retroceder desde el primer paso,
  vuelve al último de la anterior.
- `Inicio` y `Fin`: primera ficha y último paso de la última. `f`: pantalla completa.
- Una dirección acabada en `#7` empieza en la ficha 7 (la portada es la 1).

Cada ficha se puede abrir sola: `#todo` la muestra completa y `#paso=N` empieza en el paso N.

## Cómo se edita

La fuente de verdad son las fichas de `fichas/`. GitHub Pages no compila: si se cambia una
ficha, hay que regenerar `index.html` y versionarlo.

```
D:/BDDAT/venv/Scripts/python.exe presentaciones/principios/compilar.py
```

El orden es el alfabético de los ficheros (`ficha_00_…` a `ficha_28_…`).

## Convenciones de las fichas

- Un bloque de estilos común y un lienzo fijo de 1280×720 que se escala a la ventana.
- `data-paso="N"`: aparece al llegar al paso N; `data-hasta="M"`: se oculta al llegar a M;
  `data-solo`: solo se ve en su paso.
- Arriba a la izquierda, en gris claro, el bloque del índice al que pertenece la ficha
  (`.bloque-tag`, sin paso: se ve siempre).
- Azul: lo que va. Verde: lo que vuelve. Morado: el tiempo. Sin ámbar (en `fundamentos`
  significa «plan»). Principales en recuadro, secundarios en píldora.
