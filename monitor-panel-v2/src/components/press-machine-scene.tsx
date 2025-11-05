"use client"

import { useGLTF } from "@react-three/drei"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"
import { useEffect } from "react"
import { useGLTFObjects } from "./use-gltf-objects"
import { useWebSocket } from "@/providers/ws-provider"

/* 🧮 Mapeia o valor do sensor (20–60) → posição (-0.03 ↔ 0.03) */
function mapSensorToPosition(distance: number): number {
  const clamped = Math.max(20, Math.min(60, distance))
  return 0.03 - ((clamped - 20) / 40) * 0.06
}

export function PressMachineScene() {
  const { sensors } = useWebSocket()
  const { scene } = useGLTF("/models/prensa_completa.glb") // ✅ usa o original, sem clone
  const { topMovelRef, breadRef, handRef } = useGLTFObjects(scene)

  /* 🩹 Corrige materiais e configurações gerais */
  useEffect(() => {
    scene.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.castShadow = true
        obj.receiveShadow = true

        const material = obj.material as THREE.Material
        if (material) {
          material.side = THREE.DoubleSide
          material.transparent = false
        }
      }
    })
  }, [scene])

  /* 🧠 Atualiza posição e visibilidade conforme sensores */
  useFrame(() => {
    const latest = Object.values(sensors)[0] as any
    const distance = latest?.distance ?? 40
    const breadVisible = latest?.ir_bread ?? false
    const handVisible = latest?.ir_hand ?? false

    // Movimento do topo da prensa
    if (topMovelRef.current) {
      const baseY = topMovelRef.current.userData.initialY ?? 0
      const targetY = baseY + mapSensorToPosition(distance)
      topMovelRef.current.position.y = THREE.MathUtils.lerp(
        topMovelRef.current.position.y,
        targetY,
        0.15
      )
    }

    // Exibir/ocultar objetos
    if (breadRef.current) breadRef.current.visible = breadVisible
    if (handRef.current) handRef.current.visible = handVisible
  })

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} />
      <primitive object={scene} scale={20} position={[-1.8, -2, 0.5]} />
    </>
  )
}

useGLTF.preload("/models/prensa_completa.glb")
