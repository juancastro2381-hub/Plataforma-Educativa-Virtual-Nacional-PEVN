/**
 * PEVN Frontend — Application Entry Point
 *
 * Mounts the React application to the DOM.
 * Uses React 18's createRoot for concurrent features.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@/styles/globals.css'
import { App } from './App'

// Mount the application
const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error(
    '[PEVN] Root element #root not found in the DOM. ' +
      'Check that index.html contains <div id="root"></div>.'
  )
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
)
