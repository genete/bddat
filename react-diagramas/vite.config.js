import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ command }) => {
  if (command === 'serve') {
    // Modo desarrollo: SPA normal con HMR
    return { plugins: [react()] }
  }

  // Modo build: library IIFE para Flask
  // El bundle expone window.DiagramaEsftt = { mount }
  return {
    plugins: [react()],
    build: {
      lib: {
        entry:    resolve(__dirname, 'src/main.lib.jsx'),
        name:     'DiagramaEsftt',
        formats:  ['iife'],
        fileName: () => 'diagrama-esftt.iife.js',
      },
      outDir:      resolve(__dirname, '../app/static/js/react'),
      emptyOutDir: true,
    },
  }
})
