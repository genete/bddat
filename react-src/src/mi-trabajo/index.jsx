// Entry de la isla "mi-trabajo" (#501, ADR-017).
// Auto-montaje: busca [data-react-island="mi-trabajo"] y renderiza App ahí.
import { mountIsland } from '../shared/mountIsland.js'
import App from './App.jsx'

mountIsland('mi-trabajo', App)
