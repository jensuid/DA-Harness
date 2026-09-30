import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import { initTheme } from './theme'
import './index.css'

// DMDARK: before the first React render, so the tree mounts into the
// appearance the bootstrap already set and nothing reflows. The listener the
// bootstrap cannot add is attached here.
initTheme()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
