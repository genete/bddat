// Verificación en navegador en una sesión de Claude Code en la nube (#949, B).
//
// En el PC se usa el Playwright MCP (CLAUDE.md §Verificación). En la nube no
// hay MCP, pero el contenedor trae Playwright para Node y Chromium: esto hace
// login, abre una ruta y guarda una captura.
//
// Uso (con la app arrancada: bash scripts/nube/arrancar_app.sh):
//     node scripts/nube/captura.mjs <ruta> [opciones]
//
//     node scripts/nube/captura.mjs /seguimiento_y_huerfanos/
//     node scripts/nube/captura.mjs /expedientes/1/arbol --usuario TMUL --rol SUPERVISOR
//     node scripts/nube/captura.mjs /expedientes/ --salida .playwright-mcp/listado.png --alto 720
//
// Opciones:
//     --usuario SIGLAS   usuario de la semilla (defecto TTRA; contraseña «test»)
//     --rol NOMBRE       rol a elegir si el usuario tiene varios (defecto TRAMITADOR)
//     --salida FICHERO   defecto .playwright-mcp/nube-<fecha>.png (ignorado por git)
//     --ancho N --alto N viewport, defecto 1920x1080 (Full HD)
//     --pagina-entera    captura toda la página, no solo el viewport
//     --url BASE         defecto http://127.0.0.1:5000
//
// Login de dos pasos (receta que antes solo estaba en la memoria local
// `project_login_dos_pasos`): /auth/login pide `siglas` y `password`. Con un
// usuario de un solo rol (TTRA) basta ese envío. Con varios (TMUL), la página
// vuelve con un <select name="rol_id">: se elige el rol y se envía otra vez.
// En los dos casos se entra en /seguimiento_y_huerfanos/.
//
// Además de la captura, informa de lo que suele explicar una pantalla rota:
// errores de consola, peticiones fallidas (agrupadas por host: los CDN
// bloqueados salen aquí) y respuestas 4xx/5xx de la propia app.
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright');

function argumentos(argv) {
  const opts = { usuario: 'TTRA', rol: 'TRAMITADOR', ancho: 1920, alto: 1080,
                 url: 'http://127.0.0.1:5000', paginaEntera: false };
  const libres = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const valor = () => argv[++i];
    if (a === '--usuario') opts.usuario = valor();
    else if (a === '--rol') opts.rol = valor();
    else if (a === '--salida') opts.salida = valor();
    else if (a === '--ancho') opts.ancho = Number(valor());
    else if (a === '--alto') opts.alto = Number(valor());
    else if (a === '--url') opts.url = valor();
    else if (a === '--pagina-entera') opts.paginaEntera = true;
    else libres.push(a);
  }
  opts.ruta = libres[0] || '/seguimiento_y_huerfanos/';
  opts.salida ||= `.playwright-mcp/nube-${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
  return opts;
}

// Espera a la respuesta del POST del login y a que la página resultante cargue.
// No vale waitForLoadState a secas: la página del formulario ya está cargada y
// se resuelve al instante, antes de que llegue la navegación (carrera real:
// según lo que tarden los recursos, el login parecía fallar o no).
async function enviar(page, accion) {
  await Promise.all([
    page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/auth/login')),
    accion(),
  ]);
  await page.waitForLoadState('load');
}

async function login(page, opts) {
  await page.goto(`${opts.url}/auth/login`);
  await page.fill('input[name="siglas"]', opts.usuario);
  await page.fill('input[name="password"]', 'test');
  await enviar(page, () => page.press('input[name="password"]', 'Enter'));

  // Segunda pasada (varios roles): la misma página vuelve solo con el selector.
  const selectorRol = page.locator('select[name="rol_id"]');
  if (await selectorRol.count()) {
    const opciones = await selectorRol.locator('option').allTextContents();
    const elegida = opciones.find(t => t.toUpperCase().includes(opts.rol.toUpperCase()));
    if (!elegida) throw new Error(`${opts.usuario} no tiene el rol ${opts.rol}: ${opciones.join(', ')}`);
    await selectorRol.selectOption({ label: elegida.trim() });
    await enviar(page, () => selectorRol.evaluate(s => s.form.requestSubmit()));
  }
  await page.waitForURL(u => !u.pathname.startsWith('/auth/login'), { timeout: 10000 })
    .catch(() => { throw new Error(`login fallido para ${opts.usuario}: sigue en ${page.url()}`); });
}

// Sustitución de los CDN bloqueados (ver scripts/nube/README.md §CDN). Con una
// copia local en ~/.cache/bddat-cdn (la descarga arrancar_app.sh desde npm,
// que sí es accesible), las peticiones al CDN se sirven desde ella:
//   - bootstrap-icons: el mismo paquete y versión que el CDN → idéntico;
//   - bootstrap.bundle.min.js de la Junta → el de Bootstrap 5.3.3;
//   - custom-jda-bootstrap.css → bootstrap.min.css estándar: SIN la identidad
//     visual de la Junta (ni sus colores ni sus fuentes), que no está en npm;
//   - fonts.css y all.css de la Junta → vacíos.
// La captura queda legible pero APROXIMADA; con los CDN permitidos no se usa.
const CACHE_CDN = process.env.BDDAT_CDN_LOCAL || `${process.env.HOME}/.cache/bddat-cdn`;
const aproximadas = new Set();

async function sustituirCdn(page) {
  if (!existsSync(`${CACHE_CDN}/bootstrap/dist/css/bootstrap.min.css`)) return false;
  const servir = (route, fichero, tipo) => {
    aproximadas.add(new URL(route.request().url()).pathname.split('/').pop());
    return route.fulfill({ path: fichero, contentType: tipo });
  };
  await page.route('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/**', route => {
    const resto = new URL(route.request().url()).pathname.split('bootstrap-icons@1.11.1/')[1];
    const tipo = resto.endsWith('.css') ? 'text/css' : resto.endsWith('.woff2') ? 'font/woff2' : 'font/woff';
    return route.fulfill({ path: `${CACHE_CDN}/bootstrap-icons/${resto}`, contentType: tipo });
  });
  await page.route('https://cdn.juntadeandalucia.es/**', route => {
    const url = route.request().url();
    if (url.endsWith('bootstrap.bundle.min.js')) {
      return servir(route, `${CACHE_CDN}/bootstrap/dist/js/bootstrap.bundle.min.js`, 'application/javascript');
    }
    if (url.endsWith('custom-jda-bootstrap.css')) {
      return servir(route, `${CACHE_CDN}/bootstrap/dist/css/bootstrap.min.css`, 'text/css');
    }
    aproximadas.add(new URL(url).pathname.split('/').pop());
    return route.fulfill({ body: '', contentType: url.endsWith('.css') ? 'text/css' : 'text/plain' });
  });
  return true;
}

// Con curl y no con fetch: curl sale por el proxy del entorno igual que
// Chromium; el fetch de Node no lo usa y daría el CDN por bloqueado siempre.
function cdnAccesible() {
  try {
    const codigo = execFileSync('curl', ['-s', '-o', '/dev/null', '--max-time', '5', '-w', '%{http_code}',
      'https://cdn.juntadeandalucia.es/'], { encoding: 'utf8' });
    return codigo !== '000';
  } catch {
    return false;
  }
}

const opts = argumentos(process.argv.slice(2));
const navegador = await chromium.launch();
const page = await navegador.newPage({ viewport: { width: opts.ancho, height: opts.alto } });
const sustituido = !cdnAccesible() && await sustituirCdn(page);

const consola = [];
const fallidas = new Map();
const erroresApp = [];
page.on('console', m => { if (m.type() === 'error') consola.push(m.text()); });
page.on('pageerror', e => consola.push(e.message));
page.on('requestfailed', r => {
  const motivo = r.failure()?.errorText || '';
  if (process.env.CAPTURA_DEBUG) console.log('fallida:', motivo, r.url());
  // ERR_ABORTED: peticiones que la propia navegación cancela al cambiar de
  // página (las del formulario de login, por ejemplo). No son un fallo.
  if (motivo.includes('ERR_ABORTED')) return;
  const host = new URL(r.url()).host;
  fallidas.set(host, (fallidas.get(host) || 0) + 1);
});
page.on('response', r => {
  if (r.status() >= 400 && r.url().startsWith(opts.url)) erroresApp.push(`${r.status()} ${r.url().slice(opts.url.length)}`);
});

let codigo = 0;
try {
  await login(page, opts);
  const resp = await page.goto(`${opts.url}${opts.ruta}`, { waitUntil: 'networkidle' });
  mkdirSync(dirname(opts.salida), { recursive: true });
  await page.screenshot({ path: opts.salida, fullPage: opts.paginaEntera });
  console.log(`captura: ${opts.salida}`);
  console.log(`página: ${opts.ruta} → HTTP ${resp.status()} · «${await page.title()}» · usuario ${opts.usuario}`);
  if (resp.status() >= 400) codigo = 1;
} catch (e) {
  console.error(`ERROR: ${e.message}`);
  codigo = 1;
} finally {
  if (sustituido) {
    console.log('AVISO: CDN bloqueado; estilos APROXIMADOS con Bootstrap estándar desde copia local '
      + `(sin la identidad visual de la Junta). Sustituidos: ${[...aproximadas].join(', ') || '—'}`);
  }
  if (fallidas.size) {
    console.log('peticiones fallidas por host:', [...fallidas].map(([h, n]) => `${h} (${n})`).join(', '));
    if ([...fallidas.keys()].some(h => h.startsWith('cdn.'))) {
      console.log('  → CDN bloqueado: la captura sale sin estilos. Permitirlo en claude.ai → entorno → Network access.');
    }
  }
  if (erroresApp.length) console.log('respuestas de error de la app:', erroresApp.join(' · '));
  if (consola.length) console.log(`errores de consola (${consola.length}):`, consola.slice(0, 5).join(' | '));
  await navegador.close();
}
process.exit(codigo);
