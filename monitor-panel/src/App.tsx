"use client"

import { Badge } from "@/components/ui/badge"
import { Activity, Wifi, WifiOff } from "lucide-react"

import LeftSidebar from "./components/left-sidebar"
import RightSidebar from "./components/right-sidebar"
// import { PressMachineModel } from "./components/press-machine-model"
import { PressMachineModel } from "./components/press-machine/press-machine-model"
import { SensorProvider, useSensor } from "./providers/sensor-provider"

function Header() {
  const { isConnected } = useSensor()

  return (
    <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Branding */}
        <div className="flex items-center gap-4">
          <Activity className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold text-primary">
            INDUSTRIAL DIGITAL TWIN
          </h1>
          <Badge variant="outline" className="text-xs">
            Pneumatic Press Monitor
          </Badge>
        </div>

        {/* Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-green-400" />
                <span className="text-xs text-green-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-400" />
                <span className="text-xs text-red-400">Disconnected</span>
              </>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date().toLocaleString()}
          </span>
        </div>
      </div>
    </header>
  )
}

function MainLayout() {
  const { sensorData } = useSensor()

  return (
    <div className="grid grid-cols-12 gap-4 p-4 h-[calc(100vh-80px)]">
      {/* Sidebar esquerda (dados e status) */}
      <LeftSidebar />

      {/* Centro — visualização 3D */}
      <main className="col-span-6 flex flex-col gap-4">
        <PressMachineModel />
      </main>

      {/* Sidebar direita (controles e logs) */}
      <RightSidebar />
    </div>
  )
}

export default function App() {
  return (
    <SensorProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <MainLayout />
      </div>
    </SensorProvider>
  )
}
