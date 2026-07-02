// Entry de la isla "estadisticas" (#579, ADR-028 §2).
// Auto-montaje: busca [data-react-island="estadisticas"] y renderiza App ahí.
import { mountIsland } from '../shared/mountIsland.js'
import App from './App.jsx'

mountIsland('estadisticas', App)
