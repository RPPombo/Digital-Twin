"use client"

import { useConfig } from "@/providers/config-provider"
import { useStatus } from "@/providers/status-provider"
import { Wifi, RefreshCw } from "lucide-react"
import { useEffect, useState } from "react"

export function SettingsPanel() {
  const { wsUrl, apiUrl, wsPort, setConfig, availablePorts, setAvailablePorts } = useConfig()
  const { isRunning } = useStatus()
  const [loadingPorts, setLoadingPorts] = useState(false)

  const handleInputChange = (key: string, value: string | boolean) => {
    setConfig({ [key]: value } as any)
  }

  const fetchPorts = async () => {
    if (!apiUrl) return
    setLoadingPorts(true)
    try {
      const response = await fetch(`${apiUrl}/serial/ports`)
      if (!response.ok) throw new Error("Falha ao buscar portas")
      const data = await response.json()
      const ports = (data?.ports || []).map((p: any) => p.device || p.name || "Unknown")
      setAvailablePorts(ports)
    } catch (error) {
      console.error("Erro ao buscar portas:", error)
      setAvailablePorts([])
    } finally {
      setLoadingPorts(false)
    }
  }

  useEffect(() => {
    fetchPorts()
  }, [apiUrl])

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 flex items-center justify-center">
      <div className="w-full max-w-4xl h-[70vh]">
        <div className="bg-[#1e1e1e] rounded-lg shadow-2xl border border-gray-800 h-full flex flex-col">
          <div className="bg-[#2d2d2d] px-4 py-3 flex items-center justify-between border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <div className="w-3 h-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 text-sm text-gray-400 font-medium flex items-center gap-2">
                <Wifi className="w-4 h-4 text-blue-400" /> Network Configuration
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            {/* WebSocket URL */}
            <div className="bg-[#2a2a2a] p-5 rounded-lg border border-gray-800">
              <label className="block text-sm font-medium text-gray-300 mb-2">WebSocket URL</label>
              <input
                type="text"
                value={wsUrl}
                onChange={(e) => handleInputChange("wsUrl", e.target.value)}
                disabled={isRunning}
                className="w-full bg-[#1e1e1e] border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* API URL */}
            <div className="bg-[#2a2a2a] p-5 rounded-lg border border-gray-800">
              <label className="block text-sm font-medium text-gray-300 mb-2">API Base URL</label>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => handleInputChange("apiUrl", e.target.value)}
                disabled={isRunning}
                className="w-full bg-[#1e1e1e] border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Port Dropdown */}
            <div className="bg-[#2a2a2a] p-5 rounded-lg border border-gray-800">
              <label className="block text-sm font-medium text-gray-300 mb-2">Select Port</label>
              <div className="flex gap-2 items-center">
                <select
                  value={wsPort}
                  onChange={(e) => handleInputChange("wsPort", e.target.value)}
                  className="flex-1 bg-[#1e1e1e] border border-gray-700 rounded-lg px-4 py-2.5 text-white"
                >
                  {loadingPorts ? (
                    <option disabled>Carregando...</option>
                  ) : availablePorts.length > 0 ? (
                    availablePorts.map((port) => (
                      <option key={port} value={port}>{port}</option>
                    ))
                  ) : (
                    <option disabled>Nenhuma porta encontrada</option>
                  )}
                </select>
                <button
                  onClick={fetchPorts}
                  disabled={loadingPorts}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    loadingPorts
                      ? "bg-blue-900/40 text-gray-400 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
                  }`}
                >
                  <RefreshCw className={`w-4 h-4 ${loadingPorts ? "animate-spin" : ""}`} />
                  {loadingPorts ? "Recarregando..." : "Reload"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
