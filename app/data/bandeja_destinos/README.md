# Destinos de comunicación (árbol de centros directivos) — Consejería de Industria, Energía y Minas

## Origen

Extraído el 2026-08-04 de BandeJA (`https://extranet.chie.junta-andalucia.es/bandeja/`),
endpoint `POST /bandeja/modulos/bandejaTrabajo/obtieneArbolCentrosDirectivos.action`,
invocado al abrir el modal "Alta de comunicación" (campo "Destinos de la comunicación").
Esa llamada trae el árbol completo de centros directivos de **toda** la Junta de Andalucía
(47 organismos raíz); `destinos_industria_energia_minas.csv` es el subárbol del nodo `CPIE`
("CONSEJERÍA DE INDUSTRIA, ENERGÍA Y MINAS (IND)"), 73 filas (raíz incluida): servicios
centrales (D.G. Minas, S.G. Energía, S.G. Industria y Minas, Secretaría General Técnica,
Viceconsejería) y servicios periféricos por provincia (las 8), cada uno con sus
departamentos internos.

## Uso previsto

Catálogo de partida para el destino de comunicaciones a Port@firmas vinculadas a
expedientes AT: según explica Carlos, cuando la comunicación va a un tercero externo a la
Junta, el destino que se usa es el propio servicio emisor (para que la respuesta vuelva
como entrada y sea asignable a cualquier compañero del servicio). El nodo relevante es por
tanto el del servicio/unidad emisora dentro de este árbol, no un destinatario externo.
Pendiente de asociar con el dominio de BDDAT — este CSV es el volcado íntegro para no
perder ningún candidato.

## Columnas

`id` (código interno BandeJA del nodo — puede venir vacío, ver nota), `text` (rótulo tal
cual lo muestra BandeJA), `nivel` (profundidad desde la raíz `CPIE`, que es nivel 0),
`padre_id`, `padre_text`, `ruta` (breadcrumb completo desde la raíz), `es_hoja` (True si no
tiene hijos en el árbol).

## Nota de calidad del dato

7 de los 73 nodos (uno por provincia excepto Sevilla) — todos con rótulo
`SV. INDUSTRIA, ENERGIA Y MINAS (<provincia>)` — llegan con `id` **vacío** en la respuesta
de BandeJA. No es un error de la extracción: el propio JSON de origen trae ese nodo sin
identificador. Mismo síntoma de fragilidad en los rótulos institucionales que ya describe
#728 — aquí afecta también al identificador, no solo al nombre.
