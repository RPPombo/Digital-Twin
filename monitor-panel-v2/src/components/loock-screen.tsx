import { useEffect, useState } from "react"

export default function LockScreen({ onUnlock }: { onUnlock: () => void }) {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 cursor-pointer"
      onClick={onUnlock}
    >
      {/* Animated background overlay */}
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-8 animate-fade-in">
        {/* Time Display */}
        <div className="text-center">
          <div className="text-[120px] font-extralight text-white leading-none tracking-tight">
            {formatTime(currentTime)}
          </div>
          <div className="text-3xl font-light text-white/90 mt-4">{formatDate(currentTime)}</div>
        </div>

        {/* User Avatar */}
        <div className="mt-12 flex flex-col items-center gap-4">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-2xl border-4 border-white/30">
            <span className="text-4xl font-semibold text-white">U</span>
          </div>
          <div className="text-xl font-medium text-white">User</div>
        </div>

        {/* Click to Enter */}
        <div className="mt-8 flex flex-col items-center gap-3">
          <div className="px-6 py-3 bg-white/10 backdrop-blur-md rounded-full border border-white/20 shadow-lg">
            <span className="text-white/90 text-sm font-medium">Click anywhere to enter</span>
          </div>
          <div className="text-white/60 text-xs animate-pulse">Press any key or click</div>
        </div>
      </div>

      {/* Bottom Info */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 text-white/70 text-sm">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        <span>System Ready</span>
      </div>
    </div>
  )
}