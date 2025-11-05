"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls } from "@react-three/drei"
import { PressMachineScene } from "./press-machine-scene"
import { mapSensorToPosition } from "./map-sensor-to-position"
import { useSensor } from "@/providers/sensor-provider"
import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import * as THREE from "three"

/* 🎥 Sincroniza a posição da câmera com o estado externo */
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

/* 🎮 Painel de controle + presets */
function CameraControlPanel({
  cameraPosition,
  setCameraPosition,
  setAutoFollow,
}: {
  cameraPosition: THREE.Vector3
  setCameraPosition: React.Dispatch<React.SetStateAction<THREE.Vector3>>
  setAutoFollow: React.Dispatch<React.SetStateAction<boolean>>
}) {
  const move = (axis: "x" | "y" | "z", delta: number) => {
    setAutoFollow(true)
    setCameraPosition((prev) =>
      prev.clone().add(
        new THREE.Vector3(
          axis === "x" ? delta : 0,
          axis === "y" ? delta : 0,
          axis === "z" ? delta : 0
        )
      )
    )
  }

  const updateFromInput = (axis: "x" | "y" | "z", value: string) => {
    const num = parseFloat(value)
    if (isNaN(num)) return
    setAutoFollow(true)
    setCameraPosition((prev) => {
      const newPos = prev.clone()
      newPos[axis] = num
      return newPos
    })
  }

  const reset = () => {
    setAutoFollow(true)
    setCameraPosition(new THREE.Vector3(3, 2, 5))
  }

  const presets = [
    { label: "1", desc: "Frontal", pos: new THREE.Vector3(3, 2, 5) },
    { label: "2", desc: "Diagonal", pos: new THREE.Vector3(4, 2, 3) },
    { label: "3", desc: "Lateral", pos: new THREE.Vector3(0, 2, 6) },
    { label: "4", desc: "Topo", pos: new THREE.Vector3(0, 7, 0) },
  ]

  const goToPreset = (pos: THREE.Vector3) => {
    setAutoFollow(true)
    setCameraPosition(pos.clone())
  }

  return (
    <div className="absolute bottom-6 left-6 bg-[#141619]/80 backdrop-blur-sm border border-primary/30 rounded-md p-3 text-xs font-mono text-gray-300 w-[240px]">
      <div className="font-semibold text-primary mb-2">🎮 Camera Control</div>

      {(["x", "y", "z"] as const).map((axis) => (
        <div key={axis} className="flex items-center justify-between mb-1">
          <span className="uppercase w-4">{axis}</span>
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="outline"
              className="h-5 w-5 text-xs p-0"
              onClick={() => move(axis, -0.2)}
            >
              –
            </Button>
            <input
              type="number"
              step="0.1"
              value={cameraPosition[axis].toFixed(2)}
              onChange={(e) => updateFromInput(axis, e.target.value)}
              className="w-12 bg-transparent border border-border rounded text-center text-xs"
            />
            <Button
              size="sm"
              variant="outline"
              className="h-5 w-5 text-xs p-0"
              onClick={() => move(axis, 0.2)}
            >
              +
            </Button>
          </div>
        </div>
      ))}

      <div className="flex justify-center mt-2 mb-3">
        <Button
          size="sm"
          variant="secondary"
          className="text-xs px-2 py-1"
          onClick={reset}
        >
          Reset
        </Button>
      </div>

      <div className="font-semibold text-primary mb-1">🎥 Presets</div>
      <div className="grid grid-cols-4 gap-2">
        {presets.map((p) => (
          <Button
            key={p.label}
            size="sm"
            variant="outline"
            className="h-6 w-full text-xs"
            onClick={() => goToPreset(p.pos)}
            title={p.desc}
          >
            {p.label}
          </Button>
        ))}
      </div>
    </div>
  )
}

/* 🧠 Componente principal */
export function PressMachineModel() {
  const { sensorData } = useSensor()
  const distance = sensorData?.distance ?? 40
  const breadVisible = sensorData?.ir_bread ?? false
  const handVisible = sensorData?.ir_hand ?? false

  // 💾 Estado da câmera
  const [cameraPosition, setCameraPosition] = useState(new THREE.Vector3(3, 2, 5))
  const [autoFollow, setAutoFollow] = useState(true)
  const controlsRef = useRef<any>(null)

  return (
    <div className="relative w-full h-full">
      <Canvas style={{ backgroundColor: "#0b0d10" }} camera={{ fov: 45 }}>
        <CameraSync position={cameraPosition} autoFollow={autoFollow} />

        <PressMachineScene
          distance={distance}
          breadVisible={breadVisible}
          handVisible={handVisible}
        />

        {/* 🧭 OrbitControls detecta interação manual */}
        <OrbitControls
          ref={controlsRef}
          enablePan
          enableZoom
          enableRotate
          onStart={() => setAutoFollow(false)} // 👈 desativa quando o usuário mexe
        />
      </Canvas>

      {/* 🎮 Painel da câmera */}
      <CameraControlPanel
        cameraPosition={cameraPosition}
        setCameraPosition={setCameraPosition}
        setAutoFollow={setAutoFollow}
      />

      {/* 📡 Painel de sensores */}
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
