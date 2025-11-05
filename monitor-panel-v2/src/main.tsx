import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ConfigProvider } from './providers/config-provider.tsx'
import { StatusProvider } from './providers/status-provider.tsx'
import { WebSocketProvider } from './providers/ws-provider.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode >
      <StatusProvider>
        <ConfigProvider>
    <WebSocketProvider>
          <App />
    </WebSocketProvider>
        </ConfigProvider>
      </StatusProvider>
  </StrictMode>,
)
