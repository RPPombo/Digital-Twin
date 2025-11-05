"use client"

import { createContext, useContext, useEffect, useState, type Dispatch, type ReactNode, type SetStateAction } from "react"

// 📘 Define o tipo de configuração global
export interface ConfigType {
  wsUrl: string
  apiUrl: string
  wsPort: string
  apiPort: string
  autoConnect: boolean
  logLimit: string
  setConfig: (config: Partial<ConfigType>) => void

  availablePorts: string[], // 👈 array, não string
  setAvailablePorts: Dispatch<SetStateAction<string[]>>


}

// 📦 Cria o contexto
const ConfigContext = createContext<ConfigType | undefined>(undefined)

// 💡 Provider global que guarda e sincroniza as configs
export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfigState] = useState<ConfigType>({
    wsUrl: "ws://localhost:4000/sensor/ws",
    apiUrl: "http://localhost:4000",
    wsPort: "4000",
    apiPort: "4000",
    autoConnect: true,
    logLimit: "200",
    setConfig: () => { },

    availablePorts: [],
    setAvailablePorts: () => { }
  })

const [availablePorts, setAvailablePorts] = useState<string[]>([])


  // 🔁 Atualiza estado e salva no localStorage
  const setConfig = (newConfig: Partial<ConfigType>) => {
    setConfigState((prev) => {
      const updated = { ...prev, ...newConfig }
      localStorage.setItem("monitor_config", JSON.stringify(updated))
      return updated
    })
  }

  // 📂 Carrega config do localStorage ao iniciar
  useEffect(() => {
    const stored = localStorage.getItem("monitor_config")
    if (stored) {
      try {
        setConfigState(JSON.parse(stored))
      } catch {
        console.warn("⚠️ Config storage corrupted, using defaults.")
      }
    }
  }, [])

  return (
    <ConfigContext.Provider value={{ ...config, setConfig, availablePorts, setAvailablePorts }}>
      {children}
    </ConfigContext.Provider>
  )
}

// 🧩 Hook de acesso rápido
export const useConfig = () => {
  const ctx = useContext(ConfigContext)
  if (!ctx) throw new Error("useConfig must be used inside ConfigProvider")
  return ctx
}
