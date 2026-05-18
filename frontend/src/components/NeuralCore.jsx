import React, { useEffect, useRef } from "react";
import * as THREE from "three";

const LAYERS = [6, 10, 10, 4];
const ACCENT = 0xccff00;
const CYAN = 0x00f0ff;

function buildGraph() {
    const nodes = [];
    const edges = [];
    const layerX = LAYERS.map(
        (_, i) => -6 + (12 / (LAYERS.length - 1)) * i,
    );
    LAYERS.forEach((count, li) => {
        for (let i = 0; i < count; i++) {
            const y = -3 + (6 / Math.max(count - 1, 1)) * i;
            const z = Math.sin((i + li) * 1.7) * 1.2;
            nodes.push({
                position: new THREE.Vector3(layerX[li], y, z),
                seed: Math.random(),
            });
        }
    });
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

const NeuralCore = ({ introspection, embed }) => {
    const mountRef = useRef(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        const mount = mountRef.current;
        if (!mount) return;

        const width = mount.clientWidth;
        const height = mount.clientHeight;

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x050505);

        const camera = new THREE.PerspectiveCamera(
            50,
            width / height,
            0.1,
            100,
        );
        camera.position.set(0, 0, 14);

        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
        });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(width, height);
        canvasRef.current = renderer.domElement;
        mount.appendChild(renderer.domElement);

        // Lights
        scene.add(new THREE.AmbientLight(0xffffff, 0.4));
        const point = new THREE.PointLight(0xffffff, 1);
        point.position.set(10, 10, 10);
        scene.add(point);

        // Build graph
        const group = new THREE.Group();
        scene.add(group);

        const { nodes, edges } = buildGraph();

        // Edges
        edges.forEach((e) => {
            const geom = new THREE.BufferGeometry().setFromPoints([
                nodes[e.from].position,
                nodes[e.to].position,
            ]);
            const mat = new THREE.LineBasicMaterial({
                color: e.weight > 0.5 ? ACCENT : CYAN,
                transparent: true,
                opacity: 0.15 + e.weight * 0.35,
            });
            const line = new THREE.Line(geom, mat);
            group.add(line);
        });

        // Nodes
        const nodeMeshes = [];
        const nodeGeom = new THREE.SphereGeometry(0.1, 16, 16);
        nodes.forEach((n) => {
            const mat = new THREE.MeshStandardMaterial({
                color: ACCENT,
                emissive: ACCENT,
                emissiveIntensity: 1.2,
                toneMapped: false,
            });
            const mesh = new THREE.Mesh(nodeGeom, mat);
            mesh.position.copy(n.position);
            mesh.userData.seed = n.seed;
            group.add(mesh);
            nodeMeshes.push(mesh);
        });

        // Central glow
        const core = new THREE.Mesh(
            new THREE.SphereGeometry(0.35, 32, 32),
            new THREE.MeshBasicMaterial({
                color: ACCENT,
                transparent: true,
                opacity: 0.18,
            }),
        );
        group.add(core);

        // Particle field
        const particleGeom = new THREE.BufferGeometry();
        const PCOUNT = 400;
        const positions = new Float32Array(PCOUNT * 3);
        for (let i = 0; i < PCOUNT; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 30;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 18;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 30;
        }
        particleGeom.setAttribute(
            "position",
            new THREE.BufferAttribute(positions, 3),
        );
        const particles = new THREE.Points(
            particleGeom,
            new THREE.PointsMaterial({
                size: 0.04,
                color: 0xffffff,
                transparent: true,
                opacity: 0.35,
            }),
        );
        scene.add(particles);

        // Animate
        const clock = new THREE.Clock();
        let raf = 0;
        let dragging = false;
        let lastX = 0;
        let lastY = 0;
        let userYaw = 0;
        let userPitch = 0;

        const onDown = (e) => {
            dragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
        };
        const onUp = () => {
            dragging = false;
        };
        const onMove = (e) => {
            if (!dragging) return;
            userYaw += (e.clientX - lastX) * 0.005;
            userPitch += (e.clientY - lastY) * 0.005;
            lastX = e.clientX;
            lastY = e.clientY;
        };

        renderer.domElement.addEventListener("mousedown", onDown);
        window.addEventListener("mouseup", onUp);
        window.addEventListener("mousemove", onMove);

        const animate = () => {
            raf = requestAnimationFrame(animate);
            const t = clock.getElapsedTime();
            group.rotation.y = t * 0.18 + userYaw;
            group.rotation.x = Math.sin(t * 0.3) * 0.1 + userPitch;
            particles.rotation.y = t * 0.02;

            nodeMeshes.forEach((m) => {
                const seed = m.userData.seed;
                const s = 0.16 + 0.06 * Math.sin(t * 1.8 + seed * 6);
                m.scale.set(s * 4, s * 4, s * 4);
                m.material.emissiveIntensity =
                    0.7 + 0.5 * Math.sin(t * 2 + seed * 8);
            });

            renderer.render(scene, camera);
        };
        animate();

        const onResize = () => {
            const w = mount.clientWidth;
            const h = mount.clientHeight;
            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
        };
        window.addEventListener("resize", onResize);

        return () => {
            cancelAnimationFrame(raf);
            window.removeEventListener("resize", onResize);
            window.removeEventListener("mouseup", onUp);
            window.removeEventListener("mousemove", onMove);
            renderer.domElement.removeEventListener("mousedown", onDown);
            renderer.dispose();
            if (mount.contains(renderer.domElement)) {
                mount.removeChild(renderer.domElement);
            }
            scene.traverse((o) => {
                if (o.geometry) o.geometry.dispose?.();
                if (o.material) {
                    if (Array.isArray(o.material))
                        o.material.forEach((m) => m.dispose?.());
                    else o.material.dispose?.();
                }
            });
        };
    }, []);

    const Inner = (
        <div className="flex-1 relative min-h-0 h-full">
                <div
                    ref={mountRef}
                    className="absolute inset-0"
                    data-testid="neural-core-canvas"
                />

                {/* HUD overlays */}
                <div className="pointer-events-none absolute inset-0">
                    <CornerTick className="top-3 left-3" />
                    <CornerTick className="top-3 right-3" flipX />
                    <CornerTick className="bottom-3 left-3" flipY />
                    <CornerTick
                        className="bottom-3 right-3"
                        flipX
                        flipY
                    />

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
                                depth:{" "}
                                <span className="text-[#CCFF00]">
                                    {introspection?.self_reference_depth ??
                                        "-"}
                                </span>
                            </span>
                            <span>
                                threads:{" "}
                                <span className="text-[#CCFF00]">
                                    {introspection?.active_threads ?? "-"}
                                </span>
                            </span>
                            <span>
                                pulse:{" "}
                                <span className="text-[#CCFF00]">
                                    {introspection
                                        ? (
                                              introspection.coherence * 100
                                          ).toFixed(1) + "%"
                                        : "-"}
                                </span>
                            </span>
                        </div>
                    </div>

                    <div className="absolute top-4 right-4 text-right space-y-2">
                        <ReadoutBlock
                            label="lat. ms"
                            value={(introspection
                                ? 12 +
                                  (1 - introspection.coherence) * 80
                                : 42
                            ).toFixed(0)}
                        />
                        <ReadoutBlock
                            label="entropy"
                            value={(introspection
                                ? 1 - introspection.integrity
                                : 0.07
                            ).toFixed(4)}
                        />
                    </div>
                </div>
            </div>
    );

    if (embed) {
        return (
            <div
                className="h-full w-full relative overflow-hidden scanlines"
                data-testid="neural-core"
            >
                {Inner}
            </div>
        );
    }

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
            {Inner}
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
