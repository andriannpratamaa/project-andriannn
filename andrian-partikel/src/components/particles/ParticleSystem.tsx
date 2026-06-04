import React, { useMemo, useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useAppStore, GestureType } from '../../store/useAppStore';

const COUNT = 8000;

// Helper to generate text points
const generateTextPoints = (text: string, count: number): Float32Array => {
  const canvas = document.createElement('canvas');
  const size = 128;
  canvas.width = size * 4; // Wide for text
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) return new Float32Array(count * 3);

  ctx.fillStyle = 'black';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'white';
  ctx.font = 'bold 80px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  const validPixels: number[] = [];

  for (let i = 0; i < canvas.width * canvas.height; i++) {
    if (data[i * 4] > 128) { // If pixel is bright
      validPixels.push(i);
    }
  }

  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const pixelIndex = validPixels[Math.floor(Math.random() * validPixels.length)];
    const x = (pixelIndex % canvas.width) - canvas.width / 2;
    const y = canvas.height / 2 - Math.floor(pixelIndex / canvas.width); // Flip Y
    
    positions[i * 3] = x * 0.05; // Scale down
    positions[i * 3 + 1] = y * 0.05;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 0.5; // Thin depth
  }
  return positions;
};

const generatePositions = (type: GestureType, count: number): Float32Array => {
  const positions = new Float32Array(count * 3);
  
  for (let i = 0; i < count; i++) {
    let x = 0, y = 0, z = 0;
    const i3 = i * 3;

    if (type === 'victory') {
      return generateTextPoints("I LOVE U", count);
    } else if (type === 'metal') {
      // Heart Shape
      // x = 16 sin^3(t)
      // y = 13 cos(t) - 5 cos(2t) - 2 cos(3t) - cos(4t)
      const t = Math.random() * Math.PI * 2;
      // Add some volume
      const r = Math.random(); 
      
      // Parametric Heart
      const hx = 16 * Math.pow(Math.sin(t), 3);
      const hy = 13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t);
      
      // Scale and add volume
      const scale = 0.15;
      x = hx * scale;
      y = hy * scale;
      z = (Math.random() - 0.5) * 2; // Thickness
      
      // Fill inside
      x *= Math.sqrt(r);
      y *= Math.sqrt(r);
      z *= Math.sqrt(r);
      
    } else if (type === 'closed') {
      // Galaxy / Ring
      const angle = Math.random() * Math.PI * 2;
      if (i < count * 0.3) {
        // Planet
        const r = 1.5 * Math.cbrt(Math.random());
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);
        x = r * Math.sin(phi) * Math.cos(theta);
        y = r * Math.sin(phi) * Math.sin(theta);
        z = r * Math.cos(phi);
      } else {
        // Ring
        const r = 3 + (Math.random() - 0.5) * 1.5;
        x = r * Math.cos(angle);
        y = (Math.random() - 0.5) * 0.2;
        z = r * Math.sin(angle);
      }
    } else {
      // Open -> Sphere
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 4 * Math.cbrt(Math.random());
      x = r * Math.sin(phi) * Math.cos(theta);
      y = r * Math.sin(phi) * Math.sin(theta);
      z = r * Math.cos(phi);
    }
    
    positions[i3] = x;
    positions[i3 + 1] = y;
    positions[i3 + 2] = z;
  }
  
  return positions;
};

const ParticleSystem: React.FC = () => {
  const { gestureType, handPosition, particleColor } = useAppStore();
  const pointsRef = useRef<THREE.Points>(null);
  
  // Pre-calculate targets
  const spherePos = useMemo(() => generatePositions('open', COUNT), []);
  const galaxyPos = useMemo(() => generatePositions('closed', COUNT), []);
  const textPos = useMemo(() => generateTextPoints("I LOVE U", COUNT), []);
  const heartPos = useMemo(() => generatePositions('metal', COUNT), []);
  
  // Current positions buffer
  const currentPositions = useMemo(() => new Float32Array(COUNT * 3), []);
  
  // Initialize
  useEffect(() => {
    spherePos.forEach((v, i) => currentPositions[i] = v);
  }, []);

  useFrame((state) => {
    if (!pointsRef.current) return;

    const time = state.clock.getElapsedTime();
    const positions = pointsRef.current.geometry.attributes.position.array as Float32Array;
    
    // Determine target based on gesture
    let target = spherePos;
    let noiseAmount = 0.05;
    let explosionFactor = 0;

    if (gestureType === 'closed') {
      target = galaxyPos;
      noiseAmount = 0.02;
    } else if (gestureType === 'victory') {
      target = textPos;
      noiseAmount = 0.01;
    } else if (gestureType === 'metal') {
      target = heartPos;
      noiseAmount = 0.03; // Heart beat noise?
    } else if (gestureType === 'open') {
      target = spherePos;
      explosionFactor = 1.0;
    } else {
      target = spherePos;
    }

    // Gyro Effect (Rotate system based on hand position)
    // Increased sensitivity (1.5x)
    pointsRef.current.rotation.x += (-handPosition.y * 1.5 - pointsRef.current.rotation.x) * 0.1;
    pointsRef.current.rotation.y += (handPosition.x * 1.5 - pointsRef.current.rotation.y) * 0.1;

    // Update Particles
    const lerpFactor = 0.08;

    for (let i = 0; i < COUNT; i++) {
      const i3 = i * 3;
      
      // 1. Morph to target
      currentPositions[i3] += (target[i3] - currentPositions[i3]) * lerpFactor;
      currentPositions[i3 + 1] += (target[i3 + 1] - currentPositions[i3 + 1]) * lerpFactor;
      currentPositions[i3 + 2] += (target[i3 + 2] - currentPositions[i3 + 2]) * lerpFactor;
      
      // 2. Apply Effects
      let x = currentPositions[i3];
      let y = currentPositions[i3 + 1];
      let z = currentPositions[i3 + 2];

      // Explosion (Open Hand)
      if (explosionFactor > 0) {
        const dist = Math.sqrt(x*x + y*y + z*z);
        const dirX = x / dist || 0;
        const dirY = y / dist || 0;
        const dirZ = z / dist || 0;
        
        const noise = Math.sin(time * 2 + i) * 2;
        
        x += dirX * noise * explosionFactor;
        y += dirY * noise * explosionFactor;
        z += dirZ * noise * explosionFactor;
      }

      // Heart Beat Effect for Metal
      if (gestureType === 'metal') {
         const beat = 1 + Math.sin(time * 10) * 0.05; // Fast beat
         x *= beat;
         y *= beat;
         z *= beat;
      }

      // Idle Noise
      x += Math.sin(time + i) * noiseAmount;
      y += Math.cos(time + i * 0.5) * noiseAmount;
      z += Math.sin(time * 0.5 + i) * noiseAmount;

      positions[i3] = x;
      positions[i3 + 1] = y;
      positions[i3 + 2] = z;
    }
    
    pointsRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={COUNT}
          array={currentPositions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.08}
        color={particleColor}
        transparent
        opacity={0.9}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

export default ParticleSystem;
