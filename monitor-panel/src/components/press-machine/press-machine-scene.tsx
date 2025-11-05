"use client"

import { OrbitControls, useGLTF } from "@react-three/drei"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"
import { useGLTFObjects } from "./use-gltf-obect"
import { mapSensorToPosition } from "./map-sensor-to-position"

interface Props {
  distance: number
  breadVisible: boolean
  handVisible: boolean
}

export function PressMachineScene({ distance, breadVisible, handVisible }: Props) {
  const { scene } = useGLTF("/models/prensa_completa.glb")
  const { topMovelRef, breadRef, handRef } = useGLTFObjects(scene)

  useFrame(() => {
    if (topMovelRef.current) {
      const baseY = topMovelRef.current.userData.initialY ?? 0
      const targetY = baseY + mapSensorToPosition(distance)
      topMovelRef.current.position.y = THREE.MathUtils.lerp(
        topMovelRef.current.position.y,
        targetY,
        0.2
      )
    }

    if (breadRef.current) breadRef.current.visible = breadVisible
    if (handRef.current) handRef.current.visible = handVisible
  })

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} />
      <primitive object={scene} scale={10} />
      <OrbitControls enablePan enableZoom enableRotate />
    </>
  )
}

useGLTF.preload("/models/prensa_completa.glb")
