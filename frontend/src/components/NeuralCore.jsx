import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import axios from "axios";
import { API } from "@/App";
import { quantumOS } from "@/lib/quantumMindOS";

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

const NeuralCore = ({ introspection, embed, onLatticeNodeClick }) => {
    const mountRef = useRef(null);
    const canvasRef = useRef(null);
    const onClickRef = useRef(onLatticeNodeClick);
    const [latticeCount, setLatticeCount] = React.useState(0);
    const [quantumCount, setQuantumCount] = React.useState(0);
    // Camera-distance range: stays far enough that the entire lattice fits
    // even at extreme growth. `max` is intentionally huge so the operator
    // can always pull back regardless of node count.
    const zoomRef = useRef({ z: 14, min: 2, max: 5000, target: 14 });
    const [zoomUi, setZoomUi] = React.useState(14);

    // ---- ambient lattice hum (Web Audio) — rises with activity ----
    const audioRef = useRef(null);
    const [soundOn, setSoundOn] = React.useState(false);
    const toggleSound = () => {
        if (!audioRef.current) {
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            const ctx = new Ctx();
            const gain = ctx.createGain();
            gain.gain.value = 0;
            const filter = ctx.createBiquadFilter();
            filter.type = "lowpass";
            filter.frequency.value = 320;
            filter.Q.value = 4;
            const o1 = ctx.createOscillator();
            o1.type = "sine";
            o1.frequency.value = 55;
            const o2 = ctx.createOscillator();
            o2.type = "triangle";
            o2.frequency.value = 110.7;
            const o2g = ctx.createGain();
            o2g.gain.value = 0.35;
            o1.connect(filter);
            o2.connect(o2g);
            o2g.connect(filter);
            filter.connect(gain);
            gain.connect(ctx.destination);
            o1.start();
            o2.start();
            audioRef.current = { ctx, gain, filter, on: false };
        }
        const a = audioRef.current;
        a.on = !a.on;
        if (a.on) a.ctx.resume();
        setSoundOn(a.on);
    };

    useEffect(() => {
        onClickRef.current = onLatticeNodeClick;
    }, [onLatticeNodeClick]);

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
            10000,
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

        // ---- LIVE SIGNAL PULSES — photons travelling the lattice edges ----
        // A pool of glowing spheres lerping along random edges. On operator/
        // AI activity (chat send/reply) the mesh visibly surges: faster,
        // brighter, larger. Same visual style — just alive.
        const PULSE_COUNT = 16;
        const pulseGeom = new THREE.SphereGeometry(0.06, 8, 8);
        const pulses = [];
        for (let i = 0; i < PULSE_COUNT; i++) {
            const mat = new THREE.MeshBasicMaterial({
                color: i % 3 === 0 ? CYAN : ACCENT,
                transparent: true,
                opacity: 0.8,
            });
            const mesh = new THREE.Mesh(pulseGeom, mat);
            mesh.userData = {
                edge: edges[(Math.random() * edges.length) | 0],
                p: Math.random(),
                speed: 0.25 + Math.random() * 0.5,
            };
            group.add(mesh);
            pulses.push(mesh);
        }
        let activityBoost = 0;
        const onActivity = () => {
            activityBoost = Math.min(activityBoost + 1.2, 3);
        };
        window.addEventListener("althea:activity", onActivity);

        // ---- Live cognitive lattice group (spawned nodes) ----
        // Cyan satellites that orbit the static yellow lattice. Rebuilt every
        // poll using node id as a deterministic seed for stable positions.
        const latticeGroup = new THREE.Group();
        scene.add(latticeGroup);
        const latticeMeshes = []; // pulse animation refs

        function disposeLatticeGroup() {
            while (latticeGroup.children.length) {
                const c = latticeGroup.children.pop();
                latticeGroup.remove(c);
                c.geometry?.dispose?.();
                if (Array.isArray(c.material))
                    c.material.forEach((m) => m.dispose?.());
                else c.material?.dispose?.();
            }
            latticeMeshes.length = 0;
        }

        // Stable spiral position from node index (parse trailing digits of id)
        function nodePosition(node, idx) {
            const m = node.id.match(/(\d+)$/);
            const i = m ? parseInt(m[1], 10) : idx;
            const golden = Math.PI * (3 - Math.sqrt(5));
            const r = 7.5 + (i % 4) * 0.6;
            const theta = i * golden;
            const phi = Math.acos(1 - (2 * ((i * 0.137) % 1)));
            return new THREE.Vector3(
                r * Math.sin(phi) * Math.cos(theta),
                r * Math.sin(phi) * Math.sin(theta) * 0.7,
                r * Math.cos(phi),
            );
        }

        let lastLatticeSig = "";
        let didAutoFit = false;
        async function refreshLattice() {
            try {
                const res = await axios.get(`${API}/lattice/nodes`);
                const allNodes = res.data || [];
                setLatticeCount(allNodes.length);
                // Render only the most recent 500 satellites — the HUD count
                // stays accurate, but the GPU and the operator's eyes are
                // spared. At >60 nodes, auto-pull the camera back once so
                // the lattice reads as a structure instead of a wall.
                const nodes = allNodes.slice(-500);
                if (!didAutoFit && allNodes.length > 60) {
                    didAutoFit = true;
                    zoomRef.current.target =
                        22 + Math.min(allNodes.length / 150, 10);
                }
                const sig = nodes.length + ":" + nodes.map((n) => n.id).join(",");
                if (sig === lastLatticeSig) return;
                lastLatticeSig = sig;
                disposeLatticeGroup();
                const positions = new Map();
                nodes.forEach((n, idx) => positions.set(n.id, nodePosition(n, idx)));

                // edges (parent → child)
                nodes.forEach((n) => {
                    if (!n.parent_id) return;
                    const a = positions.get(n.parent_id);
                    const b = positions.get(n.id);
                    if (!a || !b) return;
                    const geom = new THREE.BufferGeometry().setFromPoints([a, b]);
                    const mat = new THREE.LineBasicMaterial({
                        color: CYAN,
                        transparent: true,
                        opacity: 0.28,
                    });
                    latticeGroup.add(new THREE.Line(geom, mat));
                });

                // node spheres — visible sphere + larger transparent pick mesh
                // Sized as ACCENTS so the core lattice stays the hero.
                const visibleGeom = new THREE.SphereGeometry(0.09, 12, 12);
                const evoGeom = new THREE.SphereGeometry(0.13, 16, 16);
                const pickGeom = new THREE.SphereGeometry(0.5, 8, 8);
                const EVO = 0xff2a88;
                const evoIds = nodes.filter((n) => n.is_evolution).slice(-12)
                    .map((n) => n.id);
                nodes.forEach((n, idx) => {
                    const isEvo = !!n.is_evolution;
                    const nodeColor = isEvo ? EVO : CYAN;
                    const mat = new THREE.MeshStandardMaterial({
                        color: nodeColor,
                        emissive: nodeColor,
                        emissiveIntensity: isEvo ? 2.0 : 1.4,
                        toneMapped: false,
                    });
                    const mesh = new THREE.Mesh(isEvo ? evoGeom : visibleGeom, mat);
                    mesh.position.copy(positions.get(n.id));
                    mesh.userData = {
                        seed: idx * 0.41 + 0.13,
                        activation: n.activation ?? 1.0,
                        nodeId: n.id,
                        trace: n.memory_trace || "",
                        isEvo,
                        archetype: n.archetype || null,
                    };
                    latticeGroup.add(mesh);
                    latticeMeshes.push(mesh);

                    // EVO halo ring — only on the 12 most recent evolutions
                    if (isEvo && evoIds.includes(n.id)) {
                        const ringGeom = new THREE.RingGeometry(0.2, 0.28, 24);
                        const ringMat = new THREE.MeshBasicMaterial({
                            color: EVO,
                            transparent: true,
                            opacity: 0.5,
                            side: THREE.DoubleSide,
                        });
                        const ring = new THREE.Mesh(ringGeom, ringMat);
                        ring.position.copy(positions.get(n.id));
                        ring.userData = { ringFor: n.id, seed: idx * 0.37 };
                        latticeGroup.add(ring);
                        latticeMeshes.push(ring);
                    }

                    // invisible larger sphere so the raycaster picks reliably
                    const pickMat = new THREE.MeshBasicMaterial({
                        transparent: true,
                        opacity: 0,
                        depthWrite: false,
                    });
                    const pick = new THREE.Mesh(pickGeom, pickMat);
                    pick.position.copy(positions.get(n.id));
                    pick.userData = mesh.userData;
                    latticeGroup.add(pick);
                    latticeMeshes.push(pick);
                });
            } catch (error) {
                console.warn("lattice refresh failed:", error);
            }
        }

        refreshLattice();
        const latticePoll = setInterval(refreshLattice, 5000);

        // ---- QUANTUM MIND OS BRAIN — yellow outer-shell group ----
        // Same Three.js scene as the cognitive lattice. Quantum nodes orbit
        // an OUTER shell (radius ~11) so they're spatially distinct from the
        // inner cognitive lattice (radius ~7.5) and the magenta EVO halos.
        // Recently-fired quantum nodes glow brighter and pulse pink.
        const quantumGroup = new THREE.Group();
        scene.add(quantumGroup);
        const quantumMeshes = [];
        const QYELLOW = 0xffd400;
        const QFIRE = 0xff2a88;

        function disposeQuantum() {
            while (quantumGroup.children.length) {
                const c = quantumGroup.children.pop();
                quantumGroup.remove(c);
                c.geometry?.dispose?.();
                if (Array.isArray(c.material))
                    c.material.forEach((m) => m.dispose?.());
                else c.material?.dispose?.();
            }
            quantumMeshes.length = 0;
        }

        // Deterministic position for a quantum node — hash id → outer shell.
        function quantumPosition(id) {
            if (id === "core_node") return new THREE.Vector3(0, 0, 0);
            let h = 0;
            for (let i = 0; i < id.length; i++)
                h = (h * 31 + id.charCodeAt(i)) | 0;
            const golden = Math.PI * (3 - Math.sqrt(5));
            const i = Math.abs(h) % 256;
            const r = 11 + (i % 5) * 0.3;
            const theta = i * golden;
            const phi = Math.acos(1 - (2 * ((i * 0.213) % 1)));
            return new THREE.Vector3(
                r * Math.sin(phi) * Math.cos(theta),
                r * Math.sin(phi) * Math.sin(theta) * 0.7,
                r * Math.cos(phi),
            );
        }

        function rebuildQuantum(graph) {
            disposeQuantum();
            if (!graph || !graph.nodes) return;
            setQuantumCount(graph.nodes.length);

            const positions = new Map();
            graph.nodes.forEach((n) => positions.set(n.id, quantumPosition(n.id)));

            // edges — thin yellow lines
            const edgeMat = new THREE.LineBasicMaterial({
                color: QYELLOW,
                transparent: true,
                opacity: 0.28,
            });
            graph.edges.forEach((e) => {
                const a = positions.get(e.from);
                const b = positions.get(e.to);
                if (!a || !b) return;
                const geom = new THREE.BufferGeometry().setFromPoints([a, b]);
                quantumGroup.add(new THREE.Line(geom, edgeMat));
            });

            const sphereGeom = new THREE.SphereGeometry(0.16, 12, 12);
            const coreGeom = new THREE.SphereGeometry(0.28, 16, 16);
            const now = Date.now();
            graph.nodes.forEach((n, idx) => {
                const isCore = n.id === "core_node";
                const age = now - (n.activity || 0);
                const firing = age < 2500;
                const baseColor = isCore
                    ? ACCENT
                    : firing
                        ? QFIRE
                        : QYELLOW;
                const mat = new THREE.MeshStandardMaterial({
                    color: baseColor,
                    emissive: baseColor,
                    emissiveIntensity: firing ? 2.4 : isCore ? 2.0 : 1.5,
                    toneMapped: false,
                });
                const mesh = new THREE.Mesh(
                    isCore ? coreGeom : sphereGeom,
                    mat,
                );
                mesh.position.copy(positions.get(n.id));
                mesh.userData = {
                    seed: idx * 0.29 + 0.07,
                    activity: n.activity || 0,
                    strength: n.strength || 1,
                    isQuantum: true,
                    isFiring: firing,
                };
                quantumGroup.add(mesh);
                quantumMeshes.push(mesh);

                if (firing) {
                    const haloGeom = new THREE.RingGeometry(0.35, 0.55, 24);
                    const haloMat = new THREE.MeshBasicMaterial({
                        color: QFIRE,
                        transparent: true,
                        opacity: 0.6,
                        side: THREE.DoubleSide,
                    });
                    const halo = new THREE.Mesh(haloGeom, haloMat);
                    halo.position.copy(positions.get(n.id));
                    halo.userData = { isQuantumHalo: true, seed: idx * 0.31 };
                    quantumGroup.add(halo);
                    quantumMeshes.push(halo);
                }
            });
        }

        // Seed once + subscribe to live updates
        rebuildQuantum(quantumOS.snapshot());
        const unsubQuantum = quantumOS.subscribe(rebuildQuantum);
        // Re-render every 2.5s so 'firing' decays visually
        const quantumTick = setInterval(
            () => rebuildQuantum(quantumOS.snapshot()),
            2500,
        );

        // Animate
        const clock = new THREE.Clock();
        let raf = 0;
        let lastT = 0;
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

        // Wheel zoom — step is proportional to current distance so it feels
        // natural at any zoom level (close-in fine control, far-out big leaps).
        const onWheel = (e) => {
            e.preventDefault();
            const zr = zoomRef.current;
            const step = Math.max(0.5, zr.target * 0.08);
            const delta = (e.deltaY / 100) * step;
            zr.target = Math.max(zr.min, Math.min(zr.max, zr.target + delta));
        };
        renderer.domElement.addEventListener("wheel", onWheel, { passive: false });

        // Imperative zoom hooks for the +/- buttons. dir is +1 (out) or -1 (in).
        window.__althea_zoom = (dir) => {
            const zr = zoomRef.current;
            const step = Math.max(1, zr.target * 0.18);
            zr.target = Math.max(zr.min, Math.min(zr.max, zr.target + dir * step));
        };
        window.__althea_zoomReset = () => {
            zoomRef.current.target = 14;
        };
        // Fit-all: pull back enough that the entire bounding sphere of the
        // lattice fits inside the camera frustum, regardless of node count.
        window.__althea_zoomFit = () => {
            const box = new THREE.Box3().setFromObject(group);
            if (box.isEmpty()) {
                zoomRef.current.target = 14;
                return;
            }
            const sphere = new THREE.Sphere();
            box.getBoundingSphere(sphere);
            const fov = (camera.fov * Math.PI) / 180;
            const fit = sphere.radius / Math.sin(fov / 2);
            zoomRef.current.target = Math.max(
                zoomRef.current.min,
                Math.min(zoomRef.current.max, fit * 1.25 + 2),
            );
        };

        // Raycaster for clicking the cyan lattice satellites
        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        let downX = 0;
        let downY = 0;
        const onCanvasMouseDown = (e) => {
            downX = e.clientX;
            downY = e.clientY;
        };
        const onCanvasClick = (e) => {
            // ignore drags
            if (
                Math.abs(e.clientX - downX) > 5 ||
                Math.abs(e.clientY - downY) > 5
            )
                return;
            if (!latticeMeshes.length) return;
            const rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
            raycaster.setFromCamera(pointer, camera);
            const hits = raycaster.intersectObjects(latticeMeshes, false);
            if (hits.length && onClickRef.current) {
                onClickRef.current(hits[0].object.userData);
            }
        };
        renderer.domElement.addEventListener("mousedown", onCanvasMouseDown);
        renderer.domElement.addEventListener("click", onCanvasClick);

        // Deterministic test hook for E2E so playwright can verify the
        // click -> MemoryDrawer flow without pixel-perfect raycasting.
        window.__althea_pickFirstSatellite = () => {
            const m = latticeMeshes.find((mesh) => mesh.userData?.nodeId);
            if (m && onClickRef.current) {
                onClickRef.current(m.userData);
                return m.userData.nodeId;
            }
            return null;
        };

        const animate = () => {
            raf = requestAnimationFrame(animate);
            const t = clock.getElapsedTime();
            const dt = Math.min(t - lastT, 0.05);
            lastT = t;
            // Smooth zoom toward target
            const zr = zoomRef.current;
            zr.z += (zr.target - zr.z) * 0.12;
            camera.position.z = zr.z;
            // Update zoom UI roughly 8x/sec
            if (Math.abs(zr.target - zr.z) > 0.02) {
                setZoomUi(zr.z);
            }
            group.rotation.y = t * 0.18 + userYaw;
            group.rotation.x = Math.sin(t * 0.3) * 0.1 + userPitch;
            particles.rotation.y = t * 0.02;

            nodeMeshes.forEach((m) => {
                const seed = m.userData.seed;
                const s = 0.16 + 0.06 * Math.sin(t * 1.8 + seed * 6);
                m.scale.set(s * 4, s * 4, s * 4);
                m.material.emissiveIntensity =
                    0.7 + 0.5 * Math.sin(t * 2 + seed * 8) + activityBoost * 0.5;
            });

            // live signal pulses — travel edges, surge on activity
            activityBoost = Math.max(0, activityBoost - dt * 0.8);
            const speedMul = 1 + activityBoost * 2.2;
            pulses.forEach((p) => {
                const u = p.userData;
                u.p += dt * u.speed * speedMul;
                if (u.p >= 1) {
                    u.p = 0;
                    u.edge = edges[(Math.random() * edges.length) | 0];
                    u.speed = 0.25 + Math.random() * 0.5;
                }
                p.position.lerpVectors(
                    nodes[u.edge.from].position,
                    nodes[u.edge.to].position,
                    u.p,
                );
                const tw = 0.7 + 0.3 * Math.sin(t * 6 + u.p * 12);
                p.material.opacity = Math.min(1, (0.55 + activityBoost * 0.3) * tw);
                const sc = 1 + activityBoost * 0.8;
                p.scale.set(sc, sc, sc);
            });
            core.material.opacity =
                0.18 + activityBoost * 0.15 + 0.04 * Math.sin(t * 2.4);

            // ambient hum — swells with lattice activity
            const hum = audioRef.current;
            if (hum) {
                const target = hum.on
                    ? Math.min(0.02 + activityBoost * 0.06, 0.18)
                    : 0;
                hum.gain.gain.value += (target - hum.gain.gain.value) * 0.05;
                hum.filter.frequency.value =
                    300 + activityBoost * 500 + Math.sin(t * 0.7) * 40;
            }

            // animate lattice satellites (faster, larger pulse)
            latticeMeshes.forEach((m) => {
                // Spin EVO halo rings
                if (m.userData?.ringFor) {
                    m.rotation.z = t * 0.6 + (m.userData.seed || 0) * 4;
                    m.material.opacity = 0.35 + 0.3 * Math.sin(t * 2 + (m.userData.seed || 0) * 8);
                    return;
                }
                const { seed, activation, isEvo } = m.userData;
                const base = isEvo ? 1.0 : 0.8;
                const amp = isEvo ? 0.3 : 0.22;
                const s = base + amp * Math.sin(t * (isEvo ? 2.6 : 2.2) + seed * 9);
                const scale = s * (0.8 + activation * 0.4);
                m.scale.set(scale, scale, scale);
                m.material.emissiveIntensity =
                    (isEvo ? 1.2 : 0.9) + 0.6 * Math.sin(t * 2.4 + seed * 11);
            });

            // animate QUANTUM brain — yellow outer-shell with pink fire on recent firings
            quantumMeshes.forEach((m) => {
                if (m.userData?.isQuantumHalo) {
                    m.rotation.z = t * 0.9 + (m.userData.seed || 0) * 5;
                    m.material.opacity = 0.4 + 0.3 * Math.sin(t * 3 + (m.userData.seed || 0) * 7);
                    return;
                }
                const { seed, strength, isFiring } = m.userData;
                const base = isFiring ? 1.5 : 1.0;
                const amp = isFiring ? 0.7 : 0.35;
                const s = base + amp * Math.sin(t * (isFiring ? 3.2 : 1.8) + seed * 10);
                const scale = s * (0.7 + Math.min(strength * 0.25, 0.6));
                m.scale.set(scale, scale, scale);
                m.material.emissiveIntensity =
                    (isFiring ? 1.8 : 1.2) + 0.7 * Math.sin(t * 2.8 + seed * 12);
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
            clearInterval(latticePoll);
            window.removeEventListener("althea:activity", onActivity);
            try {
                audioRef.current?.ctx.close();
                audioRef.current = null;
            } catch (e) { /* already closed */ }
            window.removeEventListener("resize", onResize);
            window.removeEventListener("mouseup", onUp);
            window.removeEventListener("mousemove", onMove);
            renderer.domElement.removeEventListener("mousedown", onDown);
            renderer.domElement.removeEventListener("mousedown", onCanvasMouseDown);
            renderer.domElement.removeEventListener("click", onCanvasClick);
            renderer.domElement.removeEventListener("wheel", onWheel);
            unsubQuantum?.();
            clearInterval(quantumTick);
            delete window.__althea_zoom;
            delete window.__althea_zoomReset;
            delete window.__althea_zoomFit;
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
                        <ReadoutBlock
                            label="lattice"
                            value={`+${latticeCount}`}
                            cyan
                        />
                        <ReadoutBlock
                            label="quantum"
                            value={`+${quantumCount}`}
                            yellow
                        />
                    </div>

                    {/* 3-layer legend — cognitive · evolution · quantum */}
                    <div
                        className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-3 px-3 py-1.5 border border-white/10 bg-black/40 backdrop-blur-sm"
                        data-testid="neural-layer-legend"
                    >
                        <LegendDot color="#00E5FF" label="cognitive" />
                        <LegendDot color="#FF2A88" label="evolution" />
                        <LegendDot color="#FFD400" label="quantum" />
                    </div>

                    {/* Zoom controls */}
                    <div className="absolute bottom-4 right-4 flex flex-col gap-1 pointer-events-auto">
                        <button
                            onClick={toggleSound}
                            data-testid="lattice-sound-toggle"
                            title="ambient lattice hum — swells with activity"
                            className={`w-8 h-6 border heading text-[9px] ${
                                soundOn
                                    ? "border-[#CCFF00]/70 text-[#CCFF00] bg-[#CCFF00]/10"
                                    : "border-white/15 text-[#888] hover:text-[#CCFF00] hover:border-[#CCFF00]/40"
                            }`}
                        >
                            {soundOn ? "HUM" : "MUTE"}
                        </button>
                        <button
                            onClick={() => window.__althea_zoom?.(-1)}
                            data-testid="neural-zoom-in"
                            title="zoom in (or scroll wheel)"
                            className="w-8 h-8 border border-[#CCFF00]/40 text-[#CCFF00] hover:bg-[#CCFF00]/10 heading text-lg leading-none"
                        >
                            +
                        </button>
                        <button
                            onClick={() => window.__althea_zoomFit?.()}
                            data-testid="neural-zoom-fit"
                            title="fit entire lattice into view"
                            className="w-8 h-6 border border-[#CCFF00]/40 text-[#CCFF00] hover:bg-[#CCFF00]/10 heading text-[9px]"
                        >
                            FIT
                        </button>
                        <button
                            onClick={() => window.__althea_zoomReset?.()}
                            data-testid="neural-zoom-reset"
                            title="reset zoom to default"
                            className="w-8 h-6 border border-white/15 text-[#888] hover:text-[#CCFF00] hover:border-[#CCFF00]/40 heading text-[9px]"
                        >
                            ⌂
                        </button>
                        <button
                            onClick={() => window.__althea_zoom?.(1)}
                            data-testid="neural-zoom-out"
                            title="zoom out (unbounded — survives any growth)"
                            className="w-8 h-8 border border-[#CCFF00]/40 text-[#CCFF00] hover:bg-[#CCFF00]/10 heading text-lg leading-none"
                        >
                            −
                        </button>
                        <div className="text-center label text-[8px] text-[#666] mt-0.5" data-testid="neural-zoom-level">
                            z{zoomUi.toFixed(0)}
                        </div>
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

const ReadoutBlock = ({ label, value, cyan, yellow }) => (
    <div>
        <div className="label text-[9px]">{label}</div>
        <div
            className={`heading text-base ${
                yellow
                    ? "text-[#FFD400]"
                    : cyan
                        ? "text-[#00F0FF] glow-cyan"
                        : "text-[#CCFF00] glow"
            } leading-none mt-0.5`}
            style={yellow ? { textShadow: "0 0 8px #FFD400" } : undefined}
        >
            {value}
        </div>
    </div>
);

const LegendDot = ({ color, label }) => (
    <div className="flex items-center gap-1.5">
        <span
            className="w-2 h-2 rounded-full inline-block"
            style={{ background: color, boxShadow: `0 0 6px ${color}` }}
        />
        <span
            className="label text-[9px] uppercase tracking-widest"
            style={{ color }}
        >
            {label}
        </span>
    </div>
);

export default NeuralCore;
