"use client"

import { useState } from "react"
import { Home, LogOut, Settings, TerminalSquare } from "lucide-react"

export function Dock({ activeApp, setActiveApp }: { activeApp: string; setActiveApp: (id: string) => void }) {
  const [hoveredApp, setHoveredApp] = useState<string | null>(null)
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className={`fixed bottom-3 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ease-out ${
        isHovered ? "scale-100 opacity-100" : "scale-[0.55] opacity-60 translate-y-6"
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={`relative bg-white/10 backdrop-blur-2xl border border-white/20 rounded-[24px] px-3 py-2 shadow-2xl transition-all duration-500 ${
          isHovered ? "backdrop-blur-2xl" : "backdrop-blur-md"
        }`}
      >
        {/* Dock Items */}
        <div className="flex items-end gap-2">
          {[
            { id: "logs", icon: TerminalSquare, label: "Terminal Logs", color: "text-green-400" },
            { id: "home", icon: Home, label: "Dashboard", color: "text-blue-400" },
            { id: "settings", icon: Settings, label: "Settings", color: "text-gray-400" },
          ].map(({ id, icon: Icon, label, color }) => (
            <button
              key={id}
              onClick={() => setActiveApp(id as any)}
              onMouseEnter={() => setHoveredApp(id)}
              onMouseLeave={() => setHoveredApp(null)}
              className="relative flex flex-col items-center group"
              title={label}
            >
              {/* Tooltip */}
              {hoveredApp === id && (
                <div className="absolute -top-12 bg-gray-900/95 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap shadow-lg border border-gray-700">
                  {label}
                </div>
              )}

              {/* Icon Container */}
              <div
                className={`relative p-3 rounded-2xl transition-all duration-300 ease-out ${
                  activeApp === id
                    ? "bg-white/20 scale-110"
                    : "bg-white/5 hover:bg-white/15 scale-100"
                } ${hoveredApp === id ? "scale-125 -translate-y-3" : ""}`}
              >
                <Icon
                  className={`w-8 h-8 transition-colors ${
                    activeApp === id ? color : "text-gray-300 group-hover:text-white"
                  }`}
                />
              </div>

              {/* Active Indicator */}
              <div
                className={`absolute -bottom-1 h-1 w-1 rounded-full transition-all duration-300 ${
                  activeApp === id ? "bg-white opacity-100" : "opacity-0"
                }`}
              />
            </button>
          ))}

          {/* Divider */}
          <div className="w-px h-12 bg-white/20 mx-1" />

          {/* Logout Button */}
          <button
            onClick={() => alert("Logging out...")}
            onMouseEnter={() => setHoveredApp("logout")}
            onMouseLeave={() => setHoveredApp(null)}
            className="relative p-3 rounded-2xl bg-white/5 hover:bg-red-500/20 transition-all duration-300 ease-out group"
            title="Logout"
          >
            {hoveredApp === "logout" && (
              <div className="absolute -top-12 bg-gray-900/95 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap shadow-lg border border-gray-700">
                Logout
              </div>
            )}
            <LogOut
              className={`w-8 h-8 text-gray-300 group-hover:text-red-400 transition-all duration-300 ${
                hoveredApp === "logout" ? "scale-125 -translate-y-3" : ""
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  )
}
