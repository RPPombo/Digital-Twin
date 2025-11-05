import { useEffect, useRef } from "react"
import * as THREE from "three"

export function useGLTFObjects(scene: THREE.Scene) {
  const topMovelRef = useRef<THREE.Object3D | null>(null)
  const breadRef = useRef<THREE.Object3D | null>(null)
  const handRef = useRef<THREE.Object3D | null>(null)

  useEffect(() => {
    const topo = scene.getObjectByName("topo_movel")

    const pao =
      scene.getObjectByName("pao") ||
      scene.getObjectByName("bread") ||
      scene.getObjectByName("pao_001")

    const mao =
      scene.getObjectByName("mao") ||
      scene.getObjectByName("hand") ||
      scene.getObjectByName("mao_001")

    if (topo) {
      topMovelRef.current = topo
      topo.userData.initialY = topo.position.y
    }
    if (pao) breadRef.current = pao
    if (mao) handRef.current = mao
  }, [scene])

  return { topMovelRef, breadRef, handRef }
}
