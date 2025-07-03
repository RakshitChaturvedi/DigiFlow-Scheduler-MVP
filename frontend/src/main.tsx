import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import App from './App.js'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/react-query.js'
import { AuthProvider } from './auth/AuthContext.js'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
      <BrowserRouter>
        <QueryClientProvider client={(queryClient)}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
  </React.StrictMode>
)
