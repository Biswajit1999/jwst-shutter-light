import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber';
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Box3, Vector3 } from 'three';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const BASE_URL = import.meta.env.BASE_URL;
const MODEL_URL = `${BASE_URL}models/James-Webb-Space-Telescope-B.glb`;

function configureLoader(loader) {
  const draco = new DRACOLoader();
  draco.setDecoderPath(`${BASE_URL}draco/`);
  loader.setDRACOLoader(draco);
}

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

function FrameTicker({ reducedMotion }) {
  const invalidate = useThree((state) => state.invalidate);
  useEffect(() => {
    invalidate();
    if (reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') invalidate();
    }, 1000 / 24);
    return () => window.clearInterval(timer);
  }, [invalidate, reducedMotion]);
  return null;
}

function ModelPlaceholder() {
  return (
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[0.78, 0.035, 8, 48]} />
      <meshBasicMaterial color="#a7823b" transparent opacity={0.55} />
    </mesh>
  );
}

function WebbModel({ reducedMotion }) {
  const gltf = useLoader(GLTFLoader, MODEL_URL, configureLoader);
  const model = useRef();
  const normalized = useMemo(() => {
    const scene = gltf.scene.clone(true);
    const bounds = new Box3().setFromObject(scene);
    const center = bounds.getCenter(new Vector3());
    const size = bounds.getSize(new Vector3());
    const scale = 5.5 / Math.max(size.x, size.y, size.z);
    return { scene, position: center.multiplyScalar(-1), scale };
  }, [gltf.scene]);

  useFrame((state, delta) => {
    if (!model.current || reducedMotion) return;
    model.current.rotation.y += delta * 0.08;
    model.current.position.y = 0.18 + Math.sin(state.clock.elapsedTime * 0.36) * 0.045;
  });

  return (
    <group ref={model} position={[0, 0.18, 0]} rotation={[0.32, -0.78, 0.08]}>
      <group scale={normalized.scale}>
        <primitive object={normalized.scene} position={normalized.position} />
      </group>
    </group>
  );
}

useLoader.preload(GLTFLoader, MODEL_URL, configureLoader);

export default function JwstHero() {
  const reducedMotion = useReducedMotion();
  return (
    <figure className="instrument-figure">
      <div
        className="instrument-canvas"
        role="img"
        aria-label="Animated three-dimensional model of the James Webb Space Telescope"
      >
        <Canvas
          camera={{ position: [0, 0.1, 7.4], fov: 44 }}
          dpr={[1, 1.5]}
          frameloop="demand"
          gl={{ antialias: true, powerPreference: 'low-power' }}
        >
          <ambientLight intensity={1.5} />
          <directionalLight position={[-3, 5, 5]} intensity={3.8} color="#fff0bf" />
          <directionalLight position={[4, -2, 3]} intensity={2.1} color="#b95f67" />
          <FrameTicker reducedMotion={reducedMotion} />
          <Suspense fallback={<ModelPlaceholder />}>
            <WebbModel reducedMotion={reducedMotion} />
          </Suspense>
        </Canvas>
      </div>
      <figcaption>
        <span>James Webb Space Telescope 3D model</span>
        <span aria-hidden="true"> · </span>
        <a href="https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/" target="_blank" rel="noreferrer">
          NASA / Christopher R. Meaney
        </a>
        <span aria-hidden="true"> · </span>
        <span>visual context, not analysis data</span>
      </figcaption>
    </figure>
  );
}
