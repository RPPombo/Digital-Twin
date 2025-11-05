"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Activity,
  Wifi,
  Play,
  Square,
  Settings,
  X,
  RefreshCw,
  PlugZap,
  Server,
  Link,
} from "lucide-react"
import { useSensor } from "@/providers/sensor-provider"

export default function RightSidebar() {
  const {
    isConnected,
    isCollecting,
    logs,
    startCollection,
    stopCollection,
    manualReconnect,
  } = useSensor()

  // Estado geral
  const [mode, setMode] = useState<"fake" | "serial">("fake")
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState("http://localhost:4000/sensor/ws")

  // Settings avançadas
  const [fakeStart, setFakeStart] = useState("/fake/start")
  const [fakeStop, setFakeStop] = useState("/fake/stop")
  const [serialStart, setSerialStart] = useState("/serial/start")
  const [serialStop, setSerialStop] = useState("/serial/stop")
  const [selectedPort, setSelectedPort] = useState("")

  const handleStart = () => {
    console.log(`▶️ Start ${mode} → ${mode === "fake" ? fakeStart : serialStart}`)
    startCollection("serial", {
      port: selectedPort, // vindo do dropdown
      baudrate: 9600,
      device_id: "sim-arduino-01",
    })

  }

  const handleStop = () => {
    console.log(`🛑 Stop ${mode} → ${mode === "fake" ? fakeStop : serialStop}`)
    stopCollection()
  }

  const handleConnect = () => {
    console.log("🔌 Connect →", webhookUrl)
    manualReconnect()
  }

  // const handleRefreshPorts = () => {
  //   console.log("🔄 Refresh serial ports")
  //   // aqui futuramente vai chamar o backend real
  //   setSerialPorts(["COM1", "COM2", "COM3", "ttyUSB0"])
  // }
  const { serialPorts, fetchSerialPorts } = useSensor()


  return (
    <aside className="col-span-3 flex flex-col gap-4 h-full overflow-hidden">
      <div className="flex flex-col flex-1 gap-4 overflow-hidden">

        {/* 🎛️ Painel principal */}
        <Card className="bg-card/80 backdrop-blur-sm border-primary/30 p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between text-xs text-primary mb-1">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span className="font-semibold">CONTROL PANEL</span>
            </div>
            <Badge
              variant={isConnected ? "default" : "destructive"}
              className="text-[10px]"
            >
              {isConnected ? "CONNECTED" : "DISCONNECTED"}
            </Badge>
          </div>

          {/* Webhook URL */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground flex items-center gap-1">
              <Link className="h-3 w-3" /> Webhook URL
            </label>
            <Input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="text-xs"
            />
          </div>

          {/* Toggle Mode */}
          <div className="flex flex-col ">
            <span className="text-xs text-muted-foreground">Mode:</span>
            <div className="flex justify-between">
              <div className="flex items-center gap-2 lex-1">
                <span className={`text-xs ${mode === "fake" ? "text-primary" : "text-muted-foreground"}`}>
                  Fake
                </span>
                <Switch
                  checked={mode === "serial"}
                  onCheckedChange={(v) => setMode(v ? "serial" : "fake")}
                />
                <span className={`text-xs ${mode === "serial" ? "text-primary" : "text-muted-foreground"}`}>
                  Serial
                </span>
              </div>

              {/* Porta atual selecionada */}
              {mode === "serial" && selectedPort && (
                <span className="text-[11px] text-muted-foreground ml-3">
                  Port: <span className="text-primary font-semibold">{selectedPort}</span>
                </span>
              )}
            </div>
          </div>


          {/* Botões */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              size="sm"
              variant="default"
              disabled={isCollecting}
              onClick={handleStart}
            >
              <Play className="h-4 w-4 mr-2" />
              Start
            </Button>
            <Button
              size="sm"
              variant="destructive"
              disabled={!isCollecting}
              onClick={handleStop}
            >
              <Square className="h-4 w-4 mr-2" />
              Stop
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={handleConnect}
              className="col-span-2"
            >
              <Wifi className="h-4 w-4 mr-2" />
              Connect
            </Button>
          </div>

          {/* Settings */}
          <Button
            size="sm"
            variant="outline"
            className="mt-2 w-full"
            onClick={() => setIsSettingsOpen(true)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </Card>

        {/* 🧾 Logs */}
        <div className="flex-[0.45] overflow-hidden">
          <EventLogsCard logs={logs} />
        </div>
      </div>

      {/* ⚙️ Modal de Settings */}
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="text-primary text-sm">Advanced Settings</span>
              <Button variant="ghost" size="icon" onClick={() => setIsSettingsOpen(false)}>
                <X className="h-4 w-4 text-muted-foreground" />
              </Button>
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Endpoints Fake */}
            <div>
              <p className="text-xs text-muted-foreground mb-1">Fake Endpoints</p>
              <Input
                value={fakeStart}
                onChange={(e) => setFakeStart(e.target.value)}
                className="text-xs mb-2"
                placeholder="/fake/start"
              />
              <Input
                value={fakeStop}
                onChange={(e) => setFakeStop(e.target.value)}
                className="text-xs"
                placeholder="/fake/stop"
              />
            </div>

            {/* Endpoints Serial */}
            <div>
              <p className="text-xs text-muted-foreground mb-1">Serial Endpoints</p>
              <Input
                value={serialStart}
                onChange={(e) => setSerialStart(e.target.value)}
                className="text-xs mb-2"
                placeholder="/serial/start"
              />
              <Input
                value={serialStop}
                onChange={(e) => setSerialStop(e.target.value)}
                className="text-xs"
                placeholder="/serial/stop"
              />
            </div>

            {/* Serial Ports */}
            <div>
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                <PlugZap className="h-3 w-3" /> Serial Port
              </p>
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-background border border-border rounded px-2 py-1 text-xs"
                  value={selectedPort}
                  onChange={(e) => setSelectedPort(e.target.value)}
                >
                  <option value="">Select Port</option>
                  {serialPorts.map((p) => (
                    <option key={p.device} value={p.device}>
                      {p.name || p.device}
                    </option>
                  ))}
                </select>
                <Button size="sm" variant="outline" onClick={fetchSerialPorts}>
                  <RefreshCw className="h-3 w-3" />
                </Button>

              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </aside>
  )
}

/* 🔍 Modal de logs */
function EventLogsCard({ logs }: { logs: string[] }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <Card className="flex-[0.35] bg-card/80 backdrop-blur-sm border-primary/30 p-4 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs text-primary">
            <Activity className="h-4 w-4" />
            <span className="font-semibold">EVENT LOGS</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => setIsOpen(true)}
            title="Expand logs"
          >
            <Settings className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>

        <div className="space-y-1 overflow-y-auto flex-1 pr-2 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
          {logs.length > 0 ? (
            logs
              .slice(-25)
              .reverse()
              .map((log, index) => (
                <div
                  key={index}
                  className="text-xs text-muted-foreground font-mono whitespace-pre-wrap"
                >
                  {log}
                </div>
              ))
          ) : (
            <p className="text-xs text-muted-foreground italic">No logs yet...</p>
          )}
        </div>
      </Card>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="text-primary text-sm">Event Logs — Fullscreen View</span>
              <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)}>
                <X className="h-4 w-4 text-muted-foreground" />
              </Button>
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto bg-background/80 rounded-md border border-border p-3 font-mono text-xs text-muted-foreground">
            {logs.length > 0 ? (
              logs
                .slice()
                .reverse()
                .map((log, index) => (
                  <div key={index} className="py-0.5 border-b border-border/20 last:border-none">
                    {log}
                  </div>
                ))
            ) : (
              <p className="italic">No logs yet...</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
