// Entry de la isla "command-palette" (#532, ADR-018).
// Isla GLOBAL: el contenedor lo pone el shell (base_app.html), no una vista.
// Auto-montaje: busca [data-react-island="command-palette"] y renderiza ahí.
import { mountIsland } from '../shared/mountIsland.js'
import CommandPalette from './CommandPalette.jsx'
import './styles/palette.css'

mountIsland('command-palette', CommandPalette)
