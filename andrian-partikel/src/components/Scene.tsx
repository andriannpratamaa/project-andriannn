import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import ParticleSystem from './particles/ParticleSystem';

const Scene: React.FC = () => {
  return (
    <div className="w-full h-full absolute inset-0 bg-black">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 60 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={['#050505']} />
        <Suspense fallback={null}>
          <ParticleSystem />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        </Suspense>
        <OrbitControls enableZoom={true} enablePan={false} autoRotate={false} />
        <ambientLight intensity={0.5} />
      </Canvas>
    </div>
  );
};

export default Scene;
