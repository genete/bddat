"""Compila las fichas de fichas/ en un solo HTML: index.html.

Cada ficha sigue siendo un fichero independiente (se puede abrir sola). Aquí se
incrustan en un marco (iframe) cada una, para que su CSS y su JavaScript no se
mezclen. La página de fuera lleva la navegación: clic o teclas pasan de paso en
paso y, al acabar los pasos de una ficha, a la siguiente.

GitHub Pages no compila nada: sirve index.html tal cual. Por eso el index.html
generado se versiona; si se cambia una ficha, hay que volver a ejecutar esto.

Uso:  D:/BDDAT/venv/Scripts/python.exe presentaciones/fundamentos/compilar.py
Solo usa la biblioteca estándar.
"""
import json
import re
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
FICHAS = CARPETA / 'fichas'
SALIDA = CARPETA / 'index.html'

# El orden de la presentación. Una ficha que no esté aquí no se compila.
ORDEN = [
    'ficha_01_cliente_servidor.html',
    'ficha_02_frontend.html',
    'ficha_03_backend.html',
    'ficha_04_peticion_respuesta.html',
    'ficha_05_postgresql.html',
    'ficha_06_sqlalchemy_alembic.html',
    'ficha_06b_mapa_de_piezas.html',
    'ficha_07_fichero_y_base_de_datos.html',
    'ficha_08_donde_corre.html',
    'ficha_09_escalones.html',
    'ficha_10_linux.html',
    'ficha_11_contenedores.html',
    'ficha_12_procesos.html',
    'ficha_13_nada_que_instalar.html',
    'ficha_14_el_servidor_decide.html',
    'ficha_15_configuracion.html',
    'ficha_16_software_libre.html',
]

# Se inyecta en cada ficha, justo tras <body>, para que sus oyentes se registren
# antes que los de la propia ficha. La ficha deja de atender directamente el
# teclado y el ratón: los reenvía a la página de fuera, que decide.
PUENTE = """<script>
(function(){
  var st = document.createElement('style');
  st.textContent = '#ayuda{display:none!important}';
  document.head.appendChild(st);

  function conPaso(){ return [].slice.call(document.querySelectorAll('[data-paso]')); }
  function maximo(){
    return Math.max.apply(null, conPaso().map(function(e){ return +e.getAttribute('data-paso'); }));
  }
  function actual(){
    var v = conPaso().filter(function(e){ return e.classList.contains('on'); })
      .map(function(e){ return +e.getAttribute('data-paso'); });
    return Math.max.apply(null, [1].concat(v));
  }
  function tecla(k){ document.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true})); }

  window.addEventListener('message', function(ev){
    var m = ev.data || {};
    if (m.cmd === 'next') {
      if (actual() >= maximo()) parent.postMessage({fin: 'fin'}, '*'); else tecla('ArrowRight');
    } else if (m.cmd === 'prev') {
      if (actual() <= 1) parent.postMessage({fin: 'inicio'}, '*'); else tecla('ArrowLeft');
    } else if (m.cmd === 'ultimo') {
      tecla('End');
    }
  });

  var NAV = {ArrowRight:1, ArrowLeft:1, ArrowUp:1, ArrowDown:1, ' ':1, PageDown:1, PageUp:1,
             Enter:1, Backspace:1, Home:1, End:1, f:1, F:1};
  document.addEventListener('keydown', function(e){
    if (!e.isTrusted || !NAV[e.key]) return;
    e.stopImmediatePropagation(); e.preventDefault();
    parent.postMessage({tecla: e.key}, '*');
  }, true);
  document.addEventListener('click', function(e){
    if (!e.isTrusted) return;
    e.stopImmediatePropagation();
    parent.postMessage({cmd: 'next'}, '*');
  }, true);

  window.addEventListener('load', function(){
    setTimeout(function(){
      window.dispatchEvent(new Event('resize'));
      parent.postMessage({listo: true}, '*');
    }, 60);
  });
})();
</script>"""

PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fundamentos tecnológicos</title>
<style>
html,body{margin:0;height:100%;background:#fff;overflow:hidden;font-family:"Segoe UI",Roboto,Arial,sans-serif}
#marco{position:fixed;top:0;left:0;width:100%;height:100%;border:0;background:#fff}
#capa{position:fixed;top:0;left:0;width:100%;height:100%}
#info{position:fixed;right:14px;bottom:10px;font-size:13px;color:#B4B2A9;opacity:0;transition:opacity .4s;
  pointer-events:none}
#info.ver{opacity:1}
</style>
</head>
<body>
<iframe id="marco" title="Ficha"></iframe>
<div id="capa"></div>
<div id="info"></div>
<script>
var FICHAS = __FICHAS__;

(function(){
  var marco = document.getElementById('marco');
  var capa = document.getElementById('capa');
  var info = document.getElementById('info');
  var idx = 0, listo = false, alUltimo = false, aviso = null;

  function avisar(texto){
    info.textContent = texto;
    info.classList.add('ver');
    clearTimeout(aviso);
    aviso = setTimeout(function(){ info.classList.remove('ver'); }, 2600);
  }

  function mostrar(i, ultimo){
    idx = i; listo = false; alUltimo = !!ultimo;
    marco.srcdoc = FICHAS[i].html;
    document.title = FICHAS[i].titulo;
    try { history.replaceState(null, '', '#' + (i + 1)); } catch (e) {}
    avisar((i + 1) + ' / ' + FICHAS.length + '  ·  ' + FICHAS[i].titulo);
  }

  function enviar(cmd){ if (listo) marco.contentWindow.postMessage({cmd: cmd}, '*'); }
  function siguiente(){ enviar('next'); }
  function anterior(){ enviar('prev'); }

  function pantallaCompleta(){
    if (document.fullscreenElement) document.exitFullscreen();
    else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
  }

  function tecla(k){
    if (k === 'ArrowRight' || k === 'ArrowDown' || k === ' ' || k === 'PageDown' || k === 'Enter') siguiente();
    else if (k === 'ArrowLeft' || k === 'ArrowUp' || k === 'PageUp' || k === 'Backspace') anterior();
    else if (k === 'Home') mostrar(0, false);
    else if (k === 'End') mostrar(FICHAS.length - 1, true);
    else if (k === 'f' || k === 'F') pantallaCompleta();
    else return false;
    return true;
  }

  window.addEventListener('message', function(ev){
    if (ev.source !== marco.contentWindow) return;
    var m = ev.data || {};
    if (m.listo) {
      listo = true;
      if (alUltimo) { alUltimo = false; enviar('ultimo'); }
    } else if (m.fin === 'fin') {
      if (idx < FICHAS.length - 1) mostrar(idx + 1, false); else avisar('fin de la presentación');
    } else if (m.fin === 'inicio') {
      if (idx > 0) mostrar(idx - 1, true);
    } else if (m.cmd === 'next') {
      siguiente();
    } else if (m.tecla) {
      tecla(m.tecla);
    }
  });

  document.addEventListener('keydown', function(e){
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (tecla(e.key)) e.preventDefault();
  });
  capa.addEventListener('click', siguiente);

  /* #N empieza en la ficha N (empezando por 1) */
  var n = parseInt(location.hash.slice(1), 10);
  mostrar(n >= 1 && n <= FICHAS.length ? n - 1 : 0, false);
  window.__ficha = function(){ return idx; };
})();
</script>
</body>
</html>
"""


def main():
    fichas = []
    for nombre in ORDEN:
        html = (FICHAS / nombre).read_text(encoding='utf-8')
        assert html.count('<body>') == 1, f'{nombre}: no tiene exactamente un <body>'
        titulo = re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()
        html = html.replace('<body>', '<body>\n' + PUENTE, 1)
        fichas.append({'titulo': titulo, 'html': html})

    # '</' se escribe '<\/' para que ninguna ficha cierre el <script> de fuera
    datos = json.dumps(fichas, ensure_ascii=False).replace('</', '<\\/')
    with open(SALIDA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(PAGINA.replace('__FICHAS__', datos))
    print(f'{len(fichas)} fichas -> {SALIDA.name} ({SALIDA.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
