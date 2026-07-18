import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';

const mirrorRows = [3, 4, 4, 4, 3];

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  return reduced;
}

function InstrumentAssembly({ reducedMotion }) {
  const rig = useRef();
  const { invalidate } = useThree();
  const mirrorSegments = useMemo(() => {
    const segments = [];
    mirrorRows.forEach((count, row) => {
      const y = (2 - row) * 0.48;
      const offset = (count - 1) * 0.27;
      for (let column = 0; column < count; column += 1) {
        segments.push([column * 0.54 - offset, y, row * 0.01]);
      }
    });
    return segments;
  }, []);
  const shutters = useMemo(() => Array.from({ length: 42 }, (_, index) => ({
    x: (index % 7) * 0.19 - 0.57,
    y: Math.floor(index / 7) * 0.24 - 0.6,
    closed: index % 11 === 0 || index === 24,
  })), []);

  useEffect(() => {
    invalidate();
    if (reducedMotion) return undefined;
    const tick = () => {
      if (!document.hidden) invalidate();
    };
    const timer = window.setInterval(tick, 50);
    return () => window.clearInterval(timer);
  }, [invalidate, reducedMotion]);

  useFrame(({ clock }) => {
    if (!rig.current || reducedMotion) return;
    const elapsed = clock.getElapsedTime();
    rig.current.rotation.y = -0.12 + Math.sin(elapsed * 0.34) * 0.08;
    rig.current.position.y = Math.sin(elapsed * 0.46) * 0.04;
  });

  return (
    <group ref={rig} position={[0.25, -0.05, 0]} rotation={[0.05, -0.12, -0.02]}>
      <group position={[-1.45, 0.3, 0.1]} rotation={[0.06, -0.2, -0.03]}>
        {mirrorSegments.map(([x, y, z], index) => (
          <mesh key={`${x}-${y}`} position={[x, y, z]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.29, 0.29, 0.055, 6]} />
            <meshStandardMaterial color={index % 4 === 0 ? '#f3d777' : '#d2a644'} metalness={0.7} roughness={0.24} />
          </mesh>
        ))}
        <mesh position={[0, -1.25, -0.3]}>
          <boxGeometry args={[0.68, 0.52, 0.52]} />
          <meshStandardMaterial color="#8d6a35" metalness={0.55} roughness={0.4} />
        </mesh>
        {[0, 1, 2, 3, 4].map((layer) => (
          <mesh key={layer} position={[0, -1.75 - layer * 0.025, -0.1 - layer * 0.09]} rotation={[0.68, 0, Math.PI / 4]} scale={[1.85 - layer * 0.08, 1.12 - layer * 0.035, 1]}>
            <circleGeometry args={[1, 4]} />
            <meshStandardMaterial color={layer % 2 === 0 ? '#bc8b42' : '#d6b566'} metalness={0.55} roughness={0.48} side={2} />
          </mesh>
        ))}
      </group>

      <group position={[2.25, -0.2, 0.25]} rotation={[0.02, -0.18, 0.02]}>
        <mesh position={[0, 0, -0.08]}>
          <boxGeometry args={[1.75, 1.75, 0.09]} />
          <meshStandardMaterial color="#391015" metalness={0.3} roughness={0.7} />
        </mesh>
        {shutters.map((shutter, index) => (
          <mesh key={index} position={[shutter.x, shutter.y, 0]}>
            <boxGeometry args={[0.13, 0.18, 0.035]} />
            <meshStandardMaterial color={shutter.closed ? '#4c151b' : '#e0b452'} metalness={0.5} roughness={0.38} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

export default function JwstHero() {
  const reducedMotion = useReducedMotion();
  return (
    <figure className="instrument-figure">
      <div className="instrument-canvas" aria-hidden="true">
        <Canvas
          camera={{ position: [0, 0.1, 7.4], fov: 44 }}
          dpr={[1, 1.5]}
          frameloop="demand"
          gl={{ antialias: true, powerPreference: 'low-power' }}
        >
          <ambientLight intensity={1.1} />
          <directionalLight position={[-3, 5, 5]} intensity={3.5} color="#ffe7a1" />
          <pointLight position={[4, -2, 3]} intensity={28} color="#ba3340" distance={9} />
          <InstrumentAssembly reducedMotion={reducedMotion} />
        </Canvas>
      </div>
      <figcaption>Stylized illustration, not flight data</figcaption>
    </figure>
  );
}
