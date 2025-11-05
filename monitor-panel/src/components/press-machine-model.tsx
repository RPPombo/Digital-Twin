"use client"

import { Canvas, useFrame, useThree } from "@react-three/fiber"
import { Html } from "@react-three/drei"


import { useSensor } from "@/providers/sensor-provider"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import * as THREE from "three"
import { mapSensorToPosition } from "./press-machine/map-sensor-to-position"
import { PressMachineScene } from "./press-machine/press-machine-scene"

/* ---------- Componente principal ---------- */
export function PressMachineModel() {
  const { sensorData } = useSensor()

  const distance = sensorData?.distance ?? 40
  const breadVisible = sensorData?.ir_bread ?? false
  const handVisible = sensorData?.ir_hand ?? false

  return (
    <div className="relative w-full h-full">
      <Canvas style={{ backgroundColor: "#0b0d10" }} camera={{ position: [3, 2, 5], fov: 45 }}>
        <PressMachineScene
          distance={distance}
          breadVisible={breadVisible}
          handVisible={handVisible}
        />
        <CameraController />
        <CameraPresets />
      </Canvas>

      {/* Painel de sensores */}
      <div className="absolute bottom-6 right-6 bg-[#141619]/80 backdrop-blur-sm border border-primary/30 rounded-md p-3 text-xs font-mono text-gray-300 leading-tight">
        <div className="font-semibold text-primary mb-1">📡 Sensor Data</div>
        <div>
          Distância: {distance.toFixed(2)} cm → Posição: {mapSensorToPosition(distance).toFixed(4)}
        </div>
        <div>
          Pão: {breadVisible ? "✅ visível" : "❌ oculto"} | Mão:{" "}
          {handVisible ? "✅ visível" : "❌ oculta"}
        </div>
      </div>
    </div>
  )
}

/* ---------- Controle da câmera manual ---------- */
function CameraController() {
  const { camera } = useThree()
  const [pos, setPos] = useState({ x: camera.position.x, y: camera.position.y, z: camera.position.z })

  useFrame(() => {
    setPos({
      x: camera.position.x,
      y: camera.position.y,
      z: camera.position.z,
    })
  })

  const move = (axis: "x" | "y" | "z", delta: number) => {
    camera.position[axis] += delta
  }

  const updateFromInput = (axis: "x" | "y" | "z", value: string) => {
    const num = parseFloat(value)
    if (!isNaN(num)) camera.position[axis] = num
  }

  const reset = () => {
    camera.position.set(3, 2, 5)
  }

  return (
    // 🔥 Posiciona o painel dentro da cena 3D
    <Html
      position={[0.3, 0.6, 0.4]} // mude conforme quiser o local do painel na cena
      distanceFactor={2} // ajusta o tamanho aparente conforme distância da câmera
      transform // faz o HTML seguir rotação/escala do espaço 3D
      occlude // esconde se for obstruído por objetos
    >
      <div className="bg-[#141619]/90 backdrop-blur-sm border border-primary/30 rounded-md p-3 text-xs font-mono text-gray-300 w-[180px]">
        <div className="font-semibold text-primary mb-1">🎮 Camera Control</div>

        {(["x", "y", "z"] as const).map((axis) => (
          <div key={axis} className="flex items-center justify-between mb-1">
            <span className="uppercase w-4">{axis}</span>
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                variant="outline"
                className="h-5 w-5 text-xs p-0"
                onClick={() => move(axis, -0.1)}
              >
                –
              </Button>
              <input
                type="number"
                step="0.1"
                value={pos[axis].toFixed(2)}
                onChange={(e) => updateFromInput(axis, e.target.value)}
                className="w-12 bg-transparent border border-border rounded text-center text-xs"
              />
              <Button
                size="sm"
                variant="outline"
                className="h-5 w-5 text-xs p-0"
                onClick={() => move(axis, 0.1)}
              >
                +
              </Button>
            </div>
          </div>
        ))}

        <div className="flex justify-center mt-2">
          <Button
            size="sm"
            variant="secondary"
            className="text-xs px-2 py-1"
            onClick={reset}
          >
            Reset
          </Button>
        </div>
      </div>
    </Html>
  )
}


/* ---------- Presets de câmera (dentro do Canvas) ---------- */
function CameraPresets() {
  const { camera } = useThree()

  const moveCamera = (position: [number, number, number]) => {
    const start = camera.position.clone()
    const target = new THREE.Vector3(...position)
    const duration = 800
    const startTime = performance.now()

    const animate = (time: number) => {
      const t = Math.min((time - startTime) / duration, 1)
      camera.position.lerpVectors(start, target, t)
      if (t < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }

  const presets = [
    { label: "1", position: [3, 2, 5] },
    { label: "2", position: [2, 3, 6] },
    { label: "3", position: [4, 1.5, 3] },
    { label: "4", position: [0, 5, 0] },
  ]

  return (
    <Html position={[0, 0, 0]}>
      <div className="absolute bottom-6 right-[280px] bg-[#141619]/80 backdrop-blur-sm border border-primary/30 rounded-md p-3 text-xs font-mono text-gray-300">
        <div className="font-semibold text-primary mb-1">🎥 Camera Presets</div>
        <div className="flex gap-2">
          {presets.map((preset) => (
            <Button
              key={preset.label}
              size="sm"
              variant="outline"
              className="h-6 w-6 p-0 text-xs"
              onClick={() => moveCamera(preset.position)}
              title={`Mover para posição ${preset.label}`}
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </div>
    </Html>
  )
}
