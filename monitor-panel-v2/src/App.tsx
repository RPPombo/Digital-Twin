import { useEffect, useState } from "react"
import { Home } from "lucide-react"
import { TerminalLogs } from "./components/terminal"
import { SettingsPanel } from "./components/settings"
import { Dock } from "./components/dock"
import DashboardHome  from "./components/dashboard-home"
import LockScreen from "./components/loock-screen"





export default function App() {
  const [activeApp, setActiveApp] = useState<"logs" | "settings" | "home">("logs")
  const [isLocked, setIsLocked] = useState(true)


    useEffect(() => {
    const handleKeyPress = () => {
      if (isLocked) {
        setIsLocked(false)
      }
    }
    window.addEventListener("keydown", handleKeyPress)
    return () => window.removeEventListener("keydown", handleKeyPress)
  }, [isLocked])

  if (isLocked) {
    return <LockScreen onUnlock={() => setIsLocked(false)} />
  }
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Main Content */}
      <main className="pb-32">
        {activeApp === "logs" && <TerminalLogs />}
        {activeApp === "settings" && <SettingsPanel />}
        {activeApp === "home" && ( <DashboardHome/>
          // <div className="flex flex-col items-center justify-center min-h-screen text-gray-300">
          //   <Home className="w-16 h-16 text-green-400 mb-4" />
          //   <h1 className="text-2xl font-semibold">Dashboard</h1>
          //   <p className="text-gray-500 mt-2 text-sm">System overview</p>
          // </div>
        )}
      </main>

      {/* macOS Sequoia Dock */}
      <Dock activeApp={activeApp} setActiveApp={setActiveApp} />
    </div>
  )
}
