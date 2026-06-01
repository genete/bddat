// main.jsx — entry SOLO para `npm run dev` standalone (no se compila ni se envía a Flask).
//
// Preinyecta el mock en el store y monta App sin backend: como no hay
// [data-react-island] con data-expediente-id, App no dispara fetch y usa el mock.
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { useArbolStore } from './store.js'
import { ARBOL_MOCK } from './mock/arbolMock.js'

useArbolStore.setState({ arbol: ARBOL_MOCK, cargando: false, error: null })

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
