"use client"

import { useGLTF } from "@react-three/drei"
import { useMemo, useEffect } from "react"
import * as THREE from "three"

/**
 * 🔍 Componente simples para visualizar o modelo 'prensa_completa.glb'
 * ✅ Sem Canvas interno (ideal para ser usado dentro de outro <Canvas>)
 * ✅ Corrige possíveis SkinnedMesh sem skeleton (evita erro matrixWorld)
 * ✅ Ativa sombras e dupla face nos materiais
 */

export default function Screen_Test() {
  const gltf = useGLTF("/models/prensa_completa-2.glb")
  const scene = useMemo(() => gltf.scene.clone(), [])

  // 🩹 Corrige possíveis SkinnedMeshes bugados
  useEffect(() => {
    scene.traverse((obj) => {
      if (obj.type === "SkinnedMesh") {
        const skinned = obj as any
        if (!skinned.skeleton || !skinned.skeleton.bones?.length) {
          const geometry = skinned.geometry.clone()
          const material = (skinned.material as THREE.Material).clone()
          const mesh = new THREE.Mesh(geometry, material)
          mesh.name = skinned.name + "_fixed"
          mesh.position.copy(skinned.position)
          mesh.scale.copy(skinned.scale)
          mesh.rotation.copy(skinned.rotation)
          skinned.parent?.add(mesh)
          skinned.visible = false
          console.log("🩹 Corrigido SkinnedMesh vazio:", mesh.name)
        }
      }
    })
  }, [scene])

  // ⚙️ Ajusta materiais e sombras
  useEffect(() => {
    scene.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.castShadow = true
        obj.receiveShadow = true
        if (obj.material) {
          obj.material.side = THREE.DoubleSide
          obj.material.transparent = false
        }
      }
    })
  }, [scene])

  return <primitive object={scene} scale={10} position={[0, -2, 0]} />
}

useGLTF.preload("/models/prensa_completa-2.glb")
