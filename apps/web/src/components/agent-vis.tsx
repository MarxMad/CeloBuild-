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

    // Create a main group to hold the triangle formation
    const mainGroup = new THREE.Group()
    scene.add(mainGroup)

    // Celo Colors: Yellow (#FCFF52), Green (#35D07F), White (#FFFFFF)
    const trendAgent = createAgentNode(0xFCFF52)
    const eligibilityAgent = createAgentNode(0x35D07F)
    const rewardAgent = createAgentNode(0xFFFFFF)

    // Positioning in a Triangle (Increased spacing for larger spheres)
    // Top
    trendAgent.group.position.set(0, 1.8, 0)
    // Bottom Right
    eligibilityAgent.group.position.set(1.8, -1.2, 0)
    // Bottom Left
    rewardAgent.group.position.set(-1.8, -1.2, 0)

    // Increase scale for "larger" look (2.0)
    const scale = 2.0
    trendAgent.group.scale.setScalar(scale)
    eligibilityAgent.group.scale.setScalar(scale)
    rewardAgent.group.scale.setScalar(scale)

    mainGroup.add(trendAgent.group, eligibilityAgent.group, rewardAgent.group)

    // Move the whole group up to center vertically
    mainGroup.position.y = 1.2

    // Data Stream Connections (Triangle Lines)
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0xFCFF52,
      opacity: 0.3,
      transparent: true,
      linewidth: 2
    })
    const points = []
    points.push(new THREE.Vector3(0, 1.8, 0))      // Top
    points.push(new THREE.Vector3(1.8, -1.2, 0))   // Bottom Right
    points.push(new THREE.Vector3(-1.8, -1.2, 0))  // Bottom Left
    points.push(new THREE.Vector3(0, 1.8, 0))      // Back to Top to close loop

    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points)
    const lines = new THREE.Line(lineGeometry, lineMaterial)
    mainGroup.add(lines)

    camera.position.z = 8 // Pull back slightly more to fit the larger formation

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)
      const time = Date.now() * 0.001

      // Rotate the entire triangle group
      mainGroup.rotation.y = time * 0.2 // Constant rotation
      mainGroup.rotation.z = Math.sin(time * 0.3) * 0.1 // Slight tilt wobble

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

        // Pulse scale (relative to base scale)
        const pulse = scale + Math.sin(time * 2 + i) * 0.1
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
