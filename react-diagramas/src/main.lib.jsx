import React from 'react'
import ReactDOM from 'react-dom/client'
import DiagramaEsftt from './DiagramaEsftt.jsx'

// El bundle IIFE expone window.DiagramaEsftt = { mount }
// El template Flask llama: window.DiagramaEsftt.mount(element)
export function mount(element) {
  ReactDOM.createRoot(element).render(
    <React.StrictMode>
      <DiagramaEsftt />
    </React.StrictMode>
  )
}
