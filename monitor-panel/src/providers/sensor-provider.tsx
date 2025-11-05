"use client"

import React, { createContext, useState, useEffect, useRef, useContext } from "react"

interface SensorData {
  temperature: number
  pressure: number
  distance: number
  ir_bread: boolean
  ir_hand: boolean
  timestamp: string
}

interface StartSerialConfig {
  port: string
  baudrate: number
  device_id: string
}

interface SerialPortInfo {
  device: string
  name: string
  description: string
}

interface SensorContextType {
  sensorData: SensorData
  isConnected: boolean
  isCollecting: boolean
  dataSource: "fake" | "serial" | null
  logs: string[]
  serialPorts: SerialPortInfo[]
  fetchSerialPorts: () => Promise<void>
  startCollection: (type: "fake" | "serial", serialConfig?: StartSerialConfig) => Promise<void>
  stopCollection: () => Promise<void>
  manualReconnect: () => void
}

const SensorContext = createContext<SensorContextType | undefined>(undefined)

export const SensorProvider = ({ children }: { children: React.ReactNode }) => {
  const [sensorData, setSensorData] = useState<SensorData>({
    temperature: 0,
    pressure: 0,
    distance: 0,
    ir_bread: false,
    ir_hand: false,
    timestamp: new Date().toISOString(),
  })

  const [isConnected, setIsConnected] = useState(false)
  const [isCollecting, setIsCollecting] = useState(false)
  const [dataSource, setDataSource] = useState<"fake" | "serial" | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [serialPorts, setSerialPorts] = useState<SerialPortInfo[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | undefined>()

  const addLog = (message: string) => {
    setLogs((prev) => [
      ...prev.slice(-50),
      `[${new Date().toLocaleTimeString()}] ${message}`,
    ])
  }

  // ---------------------------
  // 🔌 WebSocket connection
  // ---------------------------
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket("ws://localhost:4000/sensor/ws")
        wsRef.current = ws

        ws.onopen = () => {
          setIsConnected(true)
          addLog("✅ WebSocket connected")
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.event === "ingest" && data.reading) {
              const reading = data.reading
              setSensorData({
                temperature: reading.temperature ?? 0,
pressure: reading.pressao_kPa ?? reading.pressure ?? 0,

                distance: reading.distance ?? 0,
                ir_bread: reading.ir_bread ?? false,
                ir_hand: reading.ir_hand ?? false,
                timestamp: new Date().toISOString(),
              })
              addLog(
                `📡 Ingested → T:${reading.temperature?.toFixed?.(1)}°C | P:${reading.pressure?.toFixed?.(
                  2
                )} | D:${reading.distance?.toFixed?.(1)}`
              )
            } else if (data.type === "keepalive") {
              addLog("💓 Keepalive signal")
            } else {
              addLog(`🪶 Message: ${event.data}`)
            }
          } catch {
            addLog(`⚠️ Invalid JSON: ${event.data}`)
          }
        }

        ws.onerror = () => {
          addLog("❌ WebSocket error")
          setIsConnected(false)
        }

        ws.onclose = () => {
          setIsConnected(false)
          addLog("🔌 WebSocket closed, retrying in 5s...")
          reconnectTimeoutRef.current = window.setTimeout(connectWebSocket, 5000)
        }
      } catch {
        addLog("⚠️ Failed to connect WebSocket")
      }
    }

    connectWebSocket()

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [])

  // ---------------------------
  // 🔍 Buscar portas seriais
  // ---------------------------
  const fetchSerialPorts = async () => {
    try {
      const res = await fetch("http://localhost:4000/serial/ports")
      if (!res.ok) throw new Error("Request failed")
      const data = await res.json()
      if (data.ok && Array.isArray(data.ports)) {
        setSerialPorts(data.ports)
        addLog(`🔌 Found ${data.count} serial ports`)
      } else {
        addLog("⚠️ Invalid ports response format")
      }
    } catch (err) {
      addLog("❌ Failed to fetch serial ports")
    }
  }

  // ---------------------------
  // ▶️ Start / Stop Collection
  // ---------------------------
  const startCollection = async (
    type: "fake" | "serial",
    serialConfig?: StartSerialConfig
  ) => {
    try {
      let response

      if (type === "serial") {
        const body = JSON.stringify({
          port: serialConfig?.port || "/dev/tty.usbserial-10",
          baudrate: serialConfig?.baudrate || 9600,
          device_id: serialConfig?.device_id || "sim-arduino-01",
        })

        response = await fetch(`http://localhost:4000/serial/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
        })
        addLog(`🚀 Serial start → ${body}`)
      } else {
        response = await fetch(`http://localhost:4000/fake/start`, { method: "POST" })
        addLog("🚀 Fake start")
      }

      if (response.ok) {
        setIsCollecting(true)
        setDataSource(type)
        addLog(`🟢 ${type.toUpperCase()} collection started`)
      } else {
        addLog(`❌ Failed to start ${type} collection`)
      }
    } catch (err) {
      addLog("⚠️ API not reachable on port 4000")
    }
  }

  const stopCollection = async () => {
    if (!dataSource) return
    try {
      const response = await fetch(`http://localhost:4000/${dataSource}/stop`, {
        method: "POST",
      })
      if (response.ok) {
        setIsCollecting(false)
        addLog(`🛑 Stopped ${dataSource} collection`)
      } else {
        addLog(`❌ Failed to stop ${dataSource} collection`)
      }
    } catch {
      addLog("⚠️ API not reachable on port 4000")
    }
  }

  const manualReconnect = () => {
    addLog("🔄 Manual reconnect triggered")
    wsRef.current?.close()
  }

  return (
    <SensorContext.Provider
      value={{
        sensorData,
        isConnected,
        isCollecting,
        dataSource,
        logs,
        serialPorts,
        fetchSerialPorts,
        startCollection,
        stopCollection,
        manualReconnect,
      }}
    >
      {children}
    </SensorContext.Provider>
  )
}

export const useSensor = () => {
  const context = useContext(SensorContext)
  if (!context) throw new Error("useSensor must be used inside SensorProvider")
  return context
}
