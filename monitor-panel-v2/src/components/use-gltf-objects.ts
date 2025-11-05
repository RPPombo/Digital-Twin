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





    const placa = scene.getObjectByName("placa")

    if (placa && placa instanceof THREE.Mesh) {
      const material = placa.material as THREE.MeshStandardMaterial

      // cor fixa (exemplo: azul)
      // material.color = new THREE.Color(0x007bff)

      // cor dinâmica baseada em temperatura
      const temp = 80 // exemplo
      const t = Math.min(Math.max(temp / 100, 0), 1)
      material.color.setHSL((1 - t) * 0.66, 1, 0.5) // azul → vermelho conforme temperatura
    }

  }, [scene])

  return { topMovelRef, breadRef, handRef }
}
