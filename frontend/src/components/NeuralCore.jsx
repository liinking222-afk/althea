import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Line } from "@react-three/drei";
import * as THREE from "three";

const LAYERS = [6, 10, 10, 4];
const ACCENT = "#CCFF00";
const CYAN = "#00F0FF";

function buildGraph() {
    const nodes = [];
    const edges = [];
    const layerX = LAYERS.map(
        (_, i) => -6 + (12 / (LAYERS.length - 1)) * i,
    );
    LAYERS.forEach((count, li) => {
        for (let i = 0; i < count; i++) {
            const y = -3 + (6 / Math.max(count - 1, 1)) * i;
            const z = (Math.sin((i + li) * 1.7) * 1.2);
            nodes.push({
                id: `${li}-${i}`,
                position: [layerX[li], y, z],
                layer: li,
                seed: Math.random(),
            });
        }
    });
    // edges between adjacent layers
    let layerStart = 0;
    for (let li = 0; li < LAYERS.length - 1; li++) {
        const a = layerStart;
        const b = layerStart + LAYERS[li];
        for (let i = 0; i < LAYERS[li]; i++) {
            for (let j = 0; j < LAYERS[li + 1]; j++) {
                edges.push({
                    from: a + i,
                    to: b + j,
                    weight: Math.random(),
                });
            }
        }
        layerStart += LAYERS[li];
    }
    return { nodes, edges };
}

const Node = ({ position, seed }) => {
    const ref = useRef();
    useFrame((state) => {
        const t = state.clock.elapsedTime;
        const s = 0.16 + 0.06 * Math.sin(t * 1.8 + seed * 6);
        if (ref.current) {
            ref.current.scale.set(s * 4, s * 4, s * 4);
            ref.current.material.emissiveIntensity =
                0.7 + 0.5 * Math.sin(t * 2 + seed * 8);
        }
    });
    return (
        <mesh ref={ref} position={position}>
            <sphereGeometry args={[0.1, 16, 16]} />
            <meshStandardMaterial
                color={ACCENT}
                emissive={ACCENT}
                emissiveIntensity={1.2}
                toneMapped={false}
            />
        </mesh>
    );
};

const Edge = ({ from, to, weight }) => {
    const points = useMemo(() => [from, to], [from, to]);
    return (
        <Line
            points={points}
            color={weight > 0.5 ? ACCENT : CYAN}
            opacity={0.15 + weight * 0.35}
            transparent
            lineWidth={0.6}
        />
    );
};

const RotatingGraph = () => {
    const groupRef = useRef();
    const { nodes, edges } = useMemo(() => buildGraph(), []);
    useFrame((state) => {
        if (groupRef.current) {
            groupRef.current.rotation.y =
                state.clock.elapsedTime * 0.18;
            groupRef.current.rotation.x =
                Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
        }
    });
    return (
        <group ref={groupRef}>
            {edges.map((e, i) => (
                <Edge
                    key={i}
                    from={nodes[e.from].position}
                    to={nodes[e.to].position}
                    weight={e.weight}
                />
            ))}
            {nodes.map((n) => (
                <Node key={n.id} position={n.position} seed={n.seed} />
            ))}
            {/* central glow */}
            <mesh>
                <sphereGeometry args={[0.35, 32, 32]} />
                <meshBasicMaterial
                    color={ACCENT}
                    transparent
                    opacity={0.18}
                />
            </mesh>
        </group>
    );
};

const ParticleField = () => {
    const ref = useRef();
    const geom = useMemo(() => {
        const g = new THREE.BufferGeometry();
        const n = 400;
        const pos = new Float32Array(n * 3);
        for (let i = 0; i < n; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 30;
            pos[i * 3 + 1] = (Math.random() - 0.5) * 18;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 30;
        }
        g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        return g;
    }, []);
    useFrame((state) => {
        if (ref.current) {
            ref.current.rotation.y = state.clock.elapsedTime * 0.02;
        }
    });
    return (
        <points ref={ref} geometry={geom}>
            <pointsMaterial
                size={0.04}
                color="#ffffff"
                transparent
                opacity={0.35}
            />
        </points>
    );
};

const NeuralCore = ({ introspection }) => {
    return (
        <section
            className="panel cut h-full flex flex-col relative overflow-hidden grain scanlines"
            data-testid="neural-core"
        >
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10 z-10">
                <div className="flex items-center gap-2">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase">
                        neural core // live lattice
                    </h2>
                </div>
                <span className="label text-[9px]">
                    layers: {LAYERS.join("·")}
                </span>
            </header>

            <div className="flex-1 relative">
                <Canvas
                    camera={{ position: [0, 0, 14], fov: 50 }}
                    gl={{ antialias: true, alpha: true }}
                >
                    <color attach="background" args={["#050505"]} />
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} />
                    <RotatingGraph />
                    <ParticleField />
                    <OrbitControls
                        enableZoom={false}
                        enablePan={false}
                        autoRotate={false}
                    />
                </Canvas>

                {/* HUD overlays */}
                <div className="pointer-events-none absolute inset-0">
                    {/* corner ticks */}
                    <CornerTick className="top-3 left-3" />
                    <CornerTick className="top-3 right-3" flipX />
                    <CornerTick className="bottom-3 left-3" flipY />
                    <CornerTick className="bottom-3 right-3" flipX flipY />

                    {/* introspection readout (bottom-left HUD) */}
                    <div className="absolute bottom-4 left-4 max-w-sm space-y-1 fade-up">
                        <div className="label text-[#CCFF00]">
                            self-observation
                        </div>
                        <div className="text-[12px] text-white/90 leading-relaxed">
                            {introspection?.thought ??
                                "[INIT] introspection daemon warming..."}
                        </div>
                        <div className="flex gap-4 mt-2 text-[10px] text-[#888]">
                            <span>
                                depth: <span className="text-[#CCFF00]">
                                    {introspection?.self_reference_depth ?? "-"}
                                </span>
                            </span>
                            <span>
                                threads: <span className="text-[#CCFF00]">
                                    {introspection?.active_threads ?? "-"}
                                </span>
                            </span>
                            <span>
                                pulse: <span className="text-[#CCFF00]">
                                    {introspection
                                        ? (introspection.coherence * 100).toFixed(
                                              1,
                                          ) + "%"
                                        : "-"}
                                </span>
                            </span>
                        </div>
                    </div>

                    {/* right-side telemetry numbers */}
                    <div className="absolute top-4 right-4 text-right space-y-2">
                        <ReadoutBlock
                            label="lat. ms"
                            value={(
                                introspection
                                    ? 12 + (1 - introspection.coherence) * 80
                                    : 42
                            ).toFixed(0)}
                        />
                        <ReadoutBlock
                            label="entropy"
                            value={(
                                introspection
                                    ? 1 - introspection.integrity
                                    : 0.07
                            ).toFixed(4)}
                        />
                    </div>
                </div>
            </div>
        </section>
    );
};

const CornerTick = ({ className = "", flipX, flipY }) => (
    <div
        className={`absolute w-6 h-6 ${className}`}
        style={{
            transform: `scale(${flipX ? -1 : 1}, ${flipY ? -1 : 1})`,
        }}
    >
        <div className="absolute top-0 left-0 w-4 h-px bg-[#CCFF00]/70" />
        <div className="absolute top-0 left-0 h-4 w-px bg-[#CCFF00]/70" />
    </div>
);

const ReadoutBlock = ({ label, value }) => (
    <div>
        <div className="label text-[9px]">{label}</div>
        <div className="heading text-base text-[#CCFF00] glow leading-none mt-0.5">
            {value}
        </div>
    </div>
);

export default NeuralCore;
