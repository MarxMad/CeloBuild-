"use client"

import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export function AgentVis() {
  const mountRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!mountRef.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight)
    mountRef.current.appendChild(renderer.domElement)

    // Helper to create "Gideon-style" AI nodes
    const createAgentNode = (color: number) => {
        const group = new THREE.Group()

        // 1. Inner Core (Dense, solid looking)
        const coreGeo = new THREE.IcosahedronGeometry(0.15, 0)
        const coreMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            wireframe: true,
            transparent: true,
            opacity: 0.9
        })
        const core = new THREE.Mesh(coreGeo, coreMat)

        // 2. Mid Shell (Geodesic structure)
        const midGeo = new THREE.IcosahedronGeometry(0.28, 1)
        const midMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            wireframe: true,
            transparent: true,
            opacity: 0.4,
            side: THREE.DoubleSide
        })
        const mid = new THREE.Mesh(midGeo, midMat)

        // 3. Outer Ring (Halo effect)
        const outerGeo = new THREE.TorusGeometry(0.45, 0.01, 16, 100)
        const outerMat = new THREE.MeshBasicMaterial({ 
            color: color,
            transparent: true,
            opacity: 0.2
        })
        const outer = new THREE.Mesh(outerGeo, outerMat)

        group.add(core, mid, outer)
        return { group, core, mid, outer }
    }
    
    // Celo Colors: Yellow (#FCFF52), Green (#35D07F), White (#FFFFFF)
    const trendAgent = createAgentNode(0xFCFF52)
    const eligibilityAgent = createAgentNode(0x35D07F)
    const rewardAgent = createAgentNode(0xFFFFFF)

    // Positioning (Elevated and Spaced)
    // Adjusted Y from 0.5 to 0.8 to center them vertically better
    trendAgent.group.position.set(-2.2, 0.8, 0)
    eligibilityAgent.group.position.set(0, 0.8, 0)
    rewardAgent.group.position.set(2.2, 0.8, 0)

    scene.add(trendAgent.group, eligibilityAgent.group, rewardAgent.group)

    // Data Stream Connections
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xFCFF52, opacity: 0.15, transparent: true })
    const points = []
    points.push(new THREE.Vector3(-2.2, 0.8, 0))
    points.push(new THREE.Vector3(0, 0.8, 0))
    points.push(new THREE.Vector3(2.2, 0.8, 0))
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points)
    const lines = new THREE.Line(lineGeometry, lineMaterial)
    scene.add(lines)

    camera.position.z = 5

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)
      const time = Date.now() * 0.001

      // Rotate entire groups slightly
      trendAgent.group.rotation.y = Math.sin(time * 0.5) * 0.2
      eligibilityAgent.group.rotation.y = Math.cos(time * 0.5) * 0.2
      rewardAgent.group.rotation.y = Math.sin(time * 0.5 + 1) * 0.2

      // Animate internals (Gideon Style)
    const agents = [trendAgent, eligibilityAgent, rewardAgent];
    agents.forEach((agent, i) => {
        const speed = 1 + (i * 0.1)
          
          // Core spins fast
          agent.core.rotation.y -= 0.02 * speed
          agent.core.rotation.x -= 0.01 * speed

          // Mid shell spins opposite slowly
          agent.mid.rotation.y += 0.005 * speed
          agent.mid.rotation.z += 0.002 * speed

          // Outer ring wobbles
          agent.outer.rotation.x = Math.PI / 2 + Math.sin(time + i) * 0.2
          agent.outer.rotation.y = Math.cos(time * 0.5 + i) * 0.1

          // Pulse scale
          const pulse = 1 + Math.sin(time * 2 + i) * 0.05
          agent.group.scale.setScalar(pulse)
      })

      renderer.render(scene, camera)
    }

    animate()

    const handleResize = () => {
      if (!mountRef.current) return
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      mountRef.current?.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div ref={mountRef} className="w-full h-[300px] md:h-[400px] pointer-events-none" />
  )
}
