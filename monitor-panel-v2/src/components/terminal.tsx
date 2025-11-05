import { useEffect, useRef, useState } from "react"
import { useConfig } from "@/providers/config-provider"
import { useStatus } from "@/providers/status-provider"
import { useWebSocket } from "@/providers/ws-provider"

export function TerminalLogs() {
  const { logs, isConnected, connect, disconnect, clearLogs, addLog } = useWebSocket()
  const { apiUrl, wsPort, availablePorts } = useConfig()
  const logsEndRef = useRef<HTMLDivElement>(null)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const { setIsRunning } = useStatus()

  const apiPost = async (endpoint: string) => {
    try {
      const res = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port: wsPort, // ✅ usa a porta selecionada
          baudrate: 9600,
          device_id: "sim-arduino-01",
        }),
      })

      const json = await res.json()
      addLog(`🚀 ${endpoint} → ${JSON.stringify(json)}`)

      if (endpoint.includes("/start")) setIsRunning(true)
      if (endpoint.includes("/stop")) setIsRunning(false)
    } catch (err) {
      console.error(err)
      addLog(`❌ Failed to call ${endpoint}`)
    }
  }

  // 🧭 Controla auto-scroll
  useEffect(() => {
    const container = logContainerRef.current
    if (!container) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 10
      setAutoScroll(isAtBottom)
    }

    container.addEventListener("scroll", handleScroll)
    return () => container.removeEventListener("scroll", handleScroll)
  }, [])

  // 🔁 Mantém scroll no fim se autoScroll = true
  useEffect(() => {
    if (autoScroll) logsEndRef.current?.scrollIntoView({ block: "end" })
  }, [logs, autoScroll])

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-8">
      <div className="w-full max-w-6xl h-[85vh] overflow-hidden">
        <div className="bg-[#1e1e1e] rounded-lg shadow-2xl overflow-hidden border border-gray-800">
          {/* Header */}
          <div className="bg-[#2d2d2d] px-4 py-3 flex items-center justify-between border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <div className="w-3 h-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 text-sm text-gray-400 font-medium">
                sensor-logs — bash — 80×24
              </span>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 mr-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? "bg-green-500" : "bg-red-500"
                  } animate-pulse`}
                />
                <span className="text-xs text-gray-500">
                  {isConnected ? "Connected" : "Disconnected"}
                </span>
              </div>

              <button
                onClick={connect}
                className="px-2 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded transition-colors"
              >
                Connect
              </button>
              <button
                onClick={disconnect}
                className="px-2 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded transition-colors"
              >
                Disconnect
              </button>
              <button
                onClick={() => apiPost("/fake/start")}
                className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
              >
                Start Fake
              </button>
              <button
                onClick={() => apiPost("/fake/stop")}
                className="px-2 py-1 text-xs bg-blue-800 hover:bg-blue-700 text-white rounded transition-colors"
              >
                Stop Fake
              </button>
              <button
                onClick={() => apiPost("/serial/start")}
                className="px-2 py-1 text-xs bg-yellow-600 hover:bg-yellow-500 text-white rounded transition-colors"
              >
                Start Serial
              </button>
              <button
                onClick={() => apiPost("/serial/stop")}
                className="px-2 py-1 text-xs bg-yellow-800 hover:bg-yellow-700 text-white rounded transition-colors"
              >
                Stop Serial
              </button>
              <button
                onClick={clearLogs} // ✅ corrigido
                className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Terminal Content */}
          <div className="bg-[#1e1e1e] p-6 font-mono text-sm">
            {/* Info sobre porta atual */}
            <div className="mb-2 text-gray-400 text-xs">
              🔌 Porta atual:{" "}
              <span className="text-yellow-400 font-semibold">{wsPort || "Nenhuma selecionada"}</span>
            </div>

            {/* Header de sessão */}
            <div className="mb-4 text-gray-400">
              <div className="text-green-400">
                Last login: {new Date().toLocaleString()} on ttys001
              </div>
              <div className="mt-2">
                <span className="text-blue-400">user@macbook</span>
                <span className="text-white">:</span>
                <span className="text-cyan-400">~/sensor-monitor</span>
                <span className="text-white">$ </span>
                <span className="text-gray-300">./watch-sensors.sh</span>
              </div>
              <div className="mt-2 text-yellow-400">
                🛰️ WebSocket Live Sensor Monitor
              </div>
              <div className="h-px bg-gray-700 my-3" />
            </div>

            {/* Logs */}
            <div
              ref={logContainerRef}
              className="h-[60vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
            >
              {logs.length === 0 ? (
                <div className="text-gray-500 italic">Waiting for data...</div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, i) => (
                    <div
                      key={i}
                      className="text-gray-300 leading-relaxed hover:bg-gray-800/30 px-2 py-0.5 rounded transition-colors"
                    >
                      {log}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>

            {/* Prompt */}
            <div className="mt-4 flex items-center">
              <span className="text-blue-400">user@macbook</span>
              <span className="text-white">:</span>
              <span className="text-cyan-400">~/sensor-monitor</span>
              <span className="text-white">$ </span>
              <span className="w-2 h-4 bg-gray-400 animate-pulse ml-1" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
