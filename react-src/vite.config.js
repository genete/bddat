import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// ---------------------------------------------------------------------------
// Registro de islas React (#499 — scaffolding multi-bundle, ADR-015).
//
// Cada entrada = una isla independiente. Para crear una isla nueva:
//   1. Crear src/<nombre-isla>/index.jsx (auto-montaje con mountIsland).
//   2. Añadir aquí la línea '<nombre-isla>': resolve(__dirname, 'src/<nombre>/index.jsx').
//   3. Montarla en un template con {{ react_bundle('<nombre-isla>') }}.
//
// El build genera un bundle ES por isla + un chunk compartido (React, etc.)
// y un manifest.json (nombre con hash) que lee el helper Jinja react_bundle().
// ---------------------------------------------------------------------------
const ISLANDS = {
  'diagrama-esftt':   resolve(__dirname, 'src/diagrama-esftt/index.jsx'),
  'expediente-arbol': resolve(__dirname, 'src/expediente-arbol/index.jsx'),
  'command-palette':  resolve(__dirname, 'src/command-palette/index.jsx'),
  'mi-trabajo':       resolve(__dirname, 'src/mi-trabajo/index.jsx'),
  'estadisticas':     resolve(__dirname, 'src/estadisticas/index.jsx'),
}

export default defineConfig(({ command }) => {
  if (command === 'serve') {
    // Dev standalone (npm run dev): sirve index.html montando una isla suelta
    // para iteración visual rápida. El flujo de desarrollo real sobre Flask es
    // "editar → Build React → recargar" (rebuild). HMR integrado en Flask se
    // pospone a #500 (árbol del expediente), donde la iteración lo justifica.
    return { plugins: [react()] }
  }

  // Modo build: un bundle ES por isla, servido estático por Flask.
  return {
    plugins: [react()],
    // React lee process.env.NODE_ENV — no existe en el navegador; se reemplaza.
    define: {
      'process.env.NODE_ENV': JSON.stringify('production'),
    },
    build: {
      outDir:      resolve(__dirname, '../app/static/js/react'),
      emptyOutDir: true,
      // Vite escribe el manifest en <outDir>/manifest.json (nombre → fichero+hash).
      manifest: 'manifest.json',
      rollupOptions: {
        input: ISLANDS,
        output: {
          // Hash en el nombre = cache busting. El manifest resuelve el hash actual.
          entryFileNames: 'bundle.[name].[hash].js',
          chunkFileNames: 'chunk.[name].[hash].js',
          assetFileNames: 'asset.[name].[hash][extname]',
        },
      },
    },
  }
})
