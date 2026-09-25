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
import { mkdirSync } from 'node:fs';
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

async function login(page, opts) {
  await page.goto(`${opts.url}/auth/login`);
  await page.fill('input[name="siglas"]', opts.usuario);
  await page.fill('input[name="password"]', 'test');
  await Promise.all([page.waitForLoadState('load'), page.press('input[name="password"]', 'Enter')]);

  const selectorRol = page.locator('select[name="rol_id"]');
  if (await selectorRol.count()) {
    const opciones = await selectorRol.locator('option').allTextContents();
    const elegida = opciones.find(t => t.toUpperCase().includes(opts.rol.toUpperCase()));
    if (!elegida) throw new Error(`${opts.usuario} no tiene el rol ${opts.rol}: ${opciones.join(', ')}`);
    await selectorRol.selectOption({ label: elegida.trim() });
    // El formulario pide otra vez la contraseña junto al rol.
    const pass = page.locator('input[name="password"]');
    if (await pass.count() && !(await pass.inputValue())) await pass.fill('test');
    await Promise.all([page.waitForLoadState('load'), selectorRol.evaluate(s => s.form.requestSubmit())]);
  }
  if (page.url().includes('/auth/login')) {
    throw new Error(`login fallido para ${opts.usuario}: sigue en ${page.url()}`);
  }
}

const opts = argumentos(process.argv.slice(2));
const navegador = await chromium.launch();
const page = await navegador.newPage({ viewport: { width: opts.ancho, height: opts.alto } });

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
