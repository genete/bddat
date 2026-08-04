# RPS (Registro de Procedimientos y Servicios) — Consejería de Industria/Energía

## Origen

Extraído el 2026-08-04 de BandeJA (`https://extranet.chie.junta-andalucia.es/bandeja/`),
endpoint `POST /bandeja/modulos/bandejaTrabajo/cargarRPA.action`, invocado al abrir el
combo "Registro de Procedimientos y Servicios" del modal "Alta de comunicación". Esa
llamada trae el catálogo RPS completo (2.651 procedimientos en 19 grupos por consejería);
`rps_industria_energia_minas.csv` es el subconjunto del grupo que el JSON etiqueta como
**"Consejería de Política Industrial y Energía"** (`consejeriaDIR3: A01041433`), 205 filas.

El nombre de grupo es el rótulo **histórico** que usa BandeJA internamente, no el nombre
actual de la consejería ("Consejería de Industria, Energía y Minas"). El `codigoRPA` y el
`consejeriaDIR3` son los identificadores estables; el nombre de pantalla cambia con la
legislatura — ver #728 sobre este mismo problema con los rótulos institucionales.

## Uso previsto

Punto de partida para asociar `codigoRPA` con el dominio de expedientes de BDDAT
(autorización de instalaciones de alta tensión), de cara al autorrelleno del campo RPS al
enviar comunicaciones a BandeJA (issue gemelo de #659, sin crear todavía). Sin asociar aún
— este CSV es solo el volcado íntegro para no perder ningún candidato.

## Columnas

Tal cual las devuelve el JSON de BandeJA: `codigoRPA`, `codigoSIA`, `nombre`,
`nombrePantalla`, `codigoFamilia`, `familia`, `codigoMateria`, `materia`, `consejeria`
(rótulo histórico), `consejeriaDIR3`, `estado`, `vigente`, `fechaAlta`, `fechaBaja`.
