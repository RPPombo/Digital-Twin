import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react"
import { useConfig } from "@/providers/config-provider"
import { useStatus } from "./status-provider"

interface SensorReading {
  device_id: string
  temperature: number
  pressao_kPa: number
  distance: number
  ir_bread?: boolean
  ir_hand?: boolean
  timestamp: string
}

interface WebSocketContextType {
  logs: string[]
  isConnected: boolean
  sensors: Record<string, SensorReading>
  connect: () => void
  disconnect: () => void
  addLog: (msg: string) => void
  clearLogs: () => void
  wsRef: React.MutableRefObject<WebSocket | null>
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { wsUrl, logLimit } = useConfig()
  const { setIsRunning } = useStatus()
  const [logs, setLogs] = useState<string[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [sensors, setSensors] = useState<Record<string, SensorReading>>({})
  const wsRef = useRef<WebSocket | null>(null)

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs((prev) => [...prev.slice(-Number(logLimit)), `[${timestamp}] ${msg}`])
  }

  const clearLogs = () => setLogs([])

  const connect = () => {
    if (wsRef.current) {
      console.warn("🔄 Already connected")
      return
    }

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setIsRunning(true)
      addLog("✅ Connected to WebSocket")
    }

    ws.onmessage = (event) => {
      addLog(event.data)

      try {
        const parsed = JSON.parse(event.data)
        if (parsed.event === "ingest" && parsed.reading) {
          const reading = parsed.reading
          const deviceId = reading.device_id ?? "unknown"

          setSensors((prev) => ({
            ...prev,
            [deviceId]: {
              device_id: deviceId,
              temperature: reading.temperature ?? 0,
              pressure: reading.pressure ?? 0,
              distance: reading.distance ?? 0,
              ir_bread: reading.ir_bread,
              ir_hand: reading.ir_hand,
              timestamp: new Date().toLocaleTimeString(),
            },
          }))
        }
      } catch {
        // ignora logs não JSON
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      setIsRunning(false)
      wsRef.current = null
      addLog("🔌 Disconnected.")
    }

    ws.onerror = (err) => {
      console.error("❌ WebSocket error:", err)
      addLog("❌ WebSocket error")
      ws.close()
    }
  }

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setIsConnected(false)
      addLog("🧹 Manual disconnect")
    }
  }

  useEffect(() => {
    connect()
  }, [wsUrl])

  return (
    <WebSocketContext.Provider
      value={{ logs, isConnected, sensors, connect, disconnect, addLog, clearLogs, wsRef }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = () => {
  const ctx = useContext(WebSocketContext)
  if (!ctx) throw new Error("useWebSocket must be used inside WebSocketProvider")
  return ctx
}
