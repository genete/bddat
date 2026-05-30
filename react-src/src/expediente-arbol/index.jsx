// Entry de la isla "expediente-arbol" (#500, ADR-016).
// Auto-montaje: busca [data-react-island="expediente-arbol"] y renderiza App ahí.
import { mountIsland } from '../shared/mountIsland.js'
import App from './App.jsx'

mountIsland('expediente-arbol', App)
