"use client"

import { Canvas } from "@react-three/fiber"
import { Environment, OrbitControls, Stage } from "@react-three/drei"
import { Suspense, useEffect, useState } from "react"
import { Activity, Gauge, Thermometer, Ruler, RotateCcw, Move } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { useWebSocket } from "@/providers/ws-provider"
import MacOSWindow from "./macos-window"

import * as THREE from "three"
import { useRef } from "react"
import { Button } from "@/components/ui/button"
import { useFrame } from "@react-three/fiber"

import { useGLTF } from "@react-three/drei"
import { PressMachineScene } from "./press-machine-scene"
import Screen_Test from "./screen_test"
import test from "node:test"
import { ErrorBoundary } from "./ErrorBoundary"

/* ---------- Helper universal p/ normalizar payloads de sensores ---------- */
function normalizeSensorPayload(msg: any) {
  // 1) se vier string, tenta parsear
  if (typeof msg === "string") {
    try { msg = JSON.parse(msg) } catch { return {} as any }
  }
  // 2) desce um nível se vier envelopado
  let r = msg?.reading ?? msg?.data ?? msg ?? {}

  // 3) casos unitários {sensor:'pressure', value:123}
  if (r && typeof r === "object" && "sensor" in r && "value" in r) {
    const m: any = {}
    const s = String((r as any).sensor).toLowerCase()
    if (s.includes("temp")) m.temperature = Number((r as any).value)
    if (s.includes("press")) m.pressure = Number((r as any).value)
    if (s.includes("dist")) m.distance = Number((r as any).value)
    if (s.includes("bread")) m.ir_bread = !!(r as any).value
    if (s.includes("hand"))  m.ir_hand  = !!(r as any).value
    r = m
  }

  // 4) normaliza nomes do backend
  if ("pressao_kPa" in r && !("pressure" in r)) r = { ...r, pressure: Number((r as any).pressao_kPa) }
  if ("temperatura_C" in r && !("temperature" in r)) r = { ...r, temperature: Number((r as any).temperatura_C) }
  if ("distancia_mm" in r && !("distance" in r))     r = { ...r, distance: Number((r as any).distancia_mm) }

  // 5) garante números/booleanos
  return {
    temperature: Number((r as any).temperature ?? 0),
    pressure:    Number((r as any).pressure ?? 0),
    distance:    Number((r as any).distance ?? 0),
    ir_bread:    Boolean((r as any).ir_bread),
    ir_hand:     Boolean((r as any).ir_hand),
  }
}

function CameraSync({
  position,
  autoFollow,
}: {
  position: THREE.Vector3
  autoFollow: boolean
}) {
  useFrame(({ camera }) => {
    if (autoFollow) {
      camera.position.lerp(position, 0.15)
      camera.lookAt(0, 0, 0)
    }
  })
  return null
}

export function CameraControlPanel({
  cameraPosition,
  setCameraPosition,
  setAutoFollow,
}: {
  cameraPosition: THREE.Vector3
  setCameraPosition: React.Dispatch<React.SetStateAction<THREE.Vector3>>
  setAutoFollow: React.Dispatch<React.SetStateAction<boolean>>
}) {
  const [isCompact, setIsCompact] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const move = (axis: "x" | "y" | "z", delta: number) => {
    setAutoFollow(true)
    setCameraPosition((prev) =>
      prev.clone().add(
        new THREE.Vector3(
          axis === "x" ? delta : 0,
          axis === "y" ? delta : 0,
          axis === "z" ? delta : 0,
        ),
      ),
    )
  }

  const reset = () => {
    setAutoFollow(true)
    setCameraPosition(new THREE.Vector3(3, 2, 5))
  }

  const presets = [
    { label: "Front", desc: "Frontal View", pos: new THREE.Vector3(3, 2, 5) },
    { label: "Diagonal", desc: "Diagonal View", pos: new THREE.Vector3(4, 2, 3) },
    { label: "Side", desc: "Lateral View", pos: new THREE.Vector3(0, 2, 6) },
    { label: "Top", desc: "Top View", pos: new THREE.Vector3(0, 7, 0) },
  ]

  const handleToggleCompact = () => setIsCompact((prev) => !prev)

  return (
    <div
      className={`absolute left-6 bottom-0 transition-all duration-500 ease-in-out ${isCompact
          ? "w-[180px]  opacity-60"
          : "w-[280px] translate-y-0 opacity-100"
        }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={`bg-[#1e1e1e]/95 backdrop-blur-xl rounded-xl shadow-2xl overflow-hidden border border-gray-700
        transition-all duration-500 ease-in-out
        ${!isHovered && isCompact
            ? "opacity-50 scale-50 blur-[1px] "
            : "opacity-100 scale-100 blur-0"
          }`}
      >
        {/* Title Bar */}
        <div className="bg-[#2d2d2d] px-4 py-2.5 flex items-center gap-2 border-b border-gray-800">
          <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
          <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
          <div
            className="w-3 h-3 rounded-full bg-[#28c840] cursor-pointer hover:opacity-80 transition"
            onClick={handleToggleCompact}
            title={isCompact ? "Expand" : "Minimize"}
          />
          <span className="ml-2 text-xs text-gray-400 font-medium">Camera Control</span>
        </div>

        {/* Expanded Content */}
        <div className={`p-4 transition-all duration-500 ${isCompact ? "hidden" : "block"}`}>
          {/* Axis Controls */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Move className="w-3.5 h-3.5" />
              <span className="font-medium">Position</span>
            </div>

            {(["x", "y", "z"] as const).map((axis) => (
              <div key={axis} className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-300 uppercase w-8">{axis} Axis</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => move(axis, -0.2)}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-all active:scale-95 border border-gray-700"
                  >
                    −
                  </button>
                  <button
                    onClick={() => move(axis, 0.2)}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-all active:scale-95 border border-gray-700"
                  >
                    +
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Reset Button */}
          <button
            onClick={reset}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-all active:scale-95 mt-4"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Camera
          </button>

          {/* Divider */}
          <div className="h-px bg-gray-800 my-3" />

          {/* Presets */}
          <div className="space-y-2">
            <div className="text-xs text-gray-400 font-medium">View Presets</div>
            <div className="grid grid-cols-2 gap-2">
              {presets.map((p) => (
                <button
                  key={p.label}
                  onClick={() => setCameraPosition(p.pos.clone())}
                  title={p.desc}
                  className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-all active:scale-95 border border-gray-700"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Compact Mode — Presets Only */}
        {isCompact && (
          <div
            className={`p-3 grid grid-cols-2 gap-2 transition-all duration-500 ${!isHovered ? "scale-90 opacity-70" : "scale-100 opacity-100"
              }`}
          >
            {presets.map((p) => (
              <button
                key={p.label}
                onClick={() => setCameraPosition(p.pos.clone())}
                title={p.desc}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-all active:scale-95 border border-gray-700"
              >
                {p.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PressMachineModel() {
  const { scene } = useGLTF("/models/prensa_completa.glb")
  return <primitive object={scene} scale={20} position={[-1.8, -2, 0.5]} />
}

// 🧩 Tipagem para dados dos sensores
interface SensorData {
  temperature: number
  pressure: number
  distance: number
  timestamp: string
}

interface ChartData {
  time: string
  temperature: number
  pressure: number
  distance: number
}

export default function DashboardHome() {
  const { sensors, isConnected } = useWebSocket()
  const [chartData, setChartData] = useState<ChartData[]>([])
  useGLTF.preload("/models/prensa_completa.glb")

  useEffect(() => {
    const entries = Object.values(sensors as any)
    if (entries.length === 0) return

    // último pacote vindo do provider
    const latestRaw: any = entries.at(-1)
    const rec = normalizeSensorPayload(latestRaw)

    console.log("📡 Normalized:", rec, "RAW:", latestRaw)

    setChartData((prev: ChartData[]) => [
      ...prev.slice(-30),
      {
        time: new Date().toLocaleTimeString().split(" ")[0],
        temperature: rec.temperature,
        pressure: rec.pressure,
        distance: rec.distance,
      },
    ])
  }, [sensors])

  const latestValues = chartData[chartData.length - 1] || {
    temperature: 0,
    pressure: 0,
    distance: 0,
  }

  const [cameraPosition, setCameraPosition] = useState(new THREE.Vector3(3, 2, 5))
  const [autoFollow, setAutoFollow] = useState(true)
  const controlsRef = useRef<any>(null)

  return (
    <div className="flex flex-col min-h-screen text-gray-300 px-10 pt-6 space-y-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* macOS Header */}
      <div className="flex w-full items-center justify-between bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl px-6 py-3 shadow-lg">
        <div className="flex items-center gap-2 text-gray-400">
          <Activity className={`${isConnected ? "text-green-400" : "text-red-500"} w-4 h-4`} />
          <span className="text-sm">Digital Twin Monitor</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400 animate-pulse" : "bg-red-500"
              }`}
          />
          <span>{isConnected ? "Live" : "Offline"}</span>
        </div>
        <div className="text-sm text-gray-400">{new Date().toLocaleTimeString()}</div>
      </div>

      {/* Layout principal */}
      <div className="flex w-full max-w-7xl mx-auto gap-6 items-start justify-center">
        {/* Coluna esquerda (cards empilhados) */}
        <div className="flex flex-col gap-6 w-[320px]">
          <MacOSWindow title="Temperature">
            <SensorCard
              title="Temperature"
              icon={<Thermometer className="text-orange-400 w-5 h-5" />}
              unit="°C"
              dataKey="temperature"
              data={chartData}
            />
          </MacOSWindow>

          <MacOSWindow title="Pressure">
            <SensorCard
              title="Pressure"
              icon={<Gauge className="text-blue-400 w-5 h-5" />}
              unit="kPa"
              dataKey="pressure"
              data={chartData}
            />
          </MacOSWindow>

          <MacOSWindow title="Distance">
            <SensorCard
              title="Distance"
              icon={<Ruler className="text-purple-400 w-5 h-5" />}
              unit="mm"
              dataKey="distance"
              data={chartData}
            />
          </MacOSWindow>
        </div>

        {/* Coluna direita (Digital Twin grande) */}
        <div className="flex-1">
          <MacOSWindow title="Digital Twin">
            <div className="w-full h-[600px] bg-[#0f0f0f]/60 rounded-2xl border border-gray-700 shadow-xl overflow-hidden relative">
              <ErrorBoundary fallback={<div className="p-4 text-sm text-red-300">Falha ao carregar assets 3D.</div>}>

                <Canvas camera={{ fov: 45 }}>
                  <CameraSync position={cameraPosition} autoFollow={autoFollow} />

                  <ambientLight intensity={0.8} />
                  <directionalLight position={[2, 2, 5]} />

                  <Suspense fallback={null}>
                    <PressMachineScene />
                    {/* <Screen_Test/> */}
                  </Suspense>

                  <OrbitControls
                    ref={controlsRef}
                    enablePan
                    enableZoom
                    enableRotate
                    onStart={() => setAutoFollow(false)}
                  />
                </Canvas>

              </ErrorBoundary>

              {/* Debug overlay (remova quando quiser) */}
              <div className="absolute top-3 right-4 text-[10px] max-w-sm bg-black/60 p-2 rounded border border-gray-700">
                Último: {JSON.stringify(normalizeSensorPayload(Object.values(sensors as any).at(-1)), null, 0)}
              </div>

              <CameraControlPanel
                cameraPosition={cameraPosition}
                setCameraPosition={setCameraPosition}
                setAutoFollow={setAutoFollow}
              />

              <div className="absolute top-3 left-4 text-xs text-gray-400 bg-black/50 px-3 py-1 rounded-lg border border-gray-700">
                Digital Twin — Press Machine
              </div>
            </div>
          </MacOSWindow>
        </div>
      </div>
    </div>
  )
}

/* 🧩 Card de Sensor */
function SensorCard({
  title,
  icon,
  data,
  dataKey,
  unit,
}: {
  title: string
  icon: React.ReactNode
  data: ChartData[]
  dataKey: keyof ChartData
  unit: string
}) {
  const latest = data[data.length - 1]?.[dataKey] ?? 0

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-lg p-4 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-semibold text-white">{title}</h3>
        </div>
        <span className="text-sm text-gray-400">{Number(latest).toFixed(2)} {unit}</span>
      </div>
      <div className="h-20">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="time" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e1e1e",
                border: "1px solid #333",
                borderRadius: "8px",
              }}
              labelStyle={{ color: "#ccc" }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke="#38bdf8"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
