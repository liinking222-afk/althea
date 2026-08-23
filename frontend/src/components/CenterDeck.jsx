import React from "react";
import NeuralCore from "@/components/NeuralCore";
import ObservationScreen from "@/components/ObservationScreen";
import NetworkScreen from "@/components/NetworkScreen";
import ConnectScreen from "@/components/ConnectScreen";
import GrowthScreen from "@/components/GrowthScreen";
import BrowserScreen from "@/components/BrowserScreen";
import ServerScreen from "@/components/ServerScreen";
import CodeScreen from "@/components/CodeScreen";
import SatelliteScreen from "@/components/SatelliteScreen";
import EvolutionScreen from "@/components/EvolutionScreen";
import QuantumScreen from "@/components/QuantumScreen";
import TroubleshootScreen from "@/components/TroubleshootScreen";
import NeuralInterfaceScreen from "@/components/NeuralInterfaceScreen";

const TAB_LABELS = {
    neural: "neural core // live lattice",
    observe: "observation // optical input",
    browser: "browser // althea surfs the web",
    network: "network // interaction graph",
    connect: "connect // device + wi-fi bridge",
    server: "server // diagnose · probe · gated-connect",
    code: "self-write // althea authors code",
    growth: "autopoiesis // grown capabilities",
    satellite: "satellite // L.E.O. mesh uplink",
    evolution: "evolution // althea builds herself",
    quantum: "quantum mind os // live neural brain",
    troubleshoot: "troubleshoot // self-diagnose & repair",
    bci: "neural link // ANIP/1.0 signal decoding",
};

const TABS = [
    { id: "neural", label: "neural" },
    { id: "observe", label: "observe" },
    { id: "browser", label: "browser" },
    { id: "network", label: "network" },
    { id: "connect", label: "connect" },
    { id: "server", label: "server" },
    { id: "code", label: "code" },
    { id: "growth", label: "growth" },
    { id: "satellite", label: "satellite" },
    { id: "evolution", label: "evolution" },
    { id: "quantum", label: "quantum" },
    { id: "troubleshoot", label: "troubleshoot" },
    { id: "bci", label: "neural-link" },
];

const CenterDeck = ({
    tab,
    setTab,
    introspection,
    observationUrl,
    setObservationUrl,
    watchLog,
    observationMeta,
    onLatticeNodeClick,
    onHostClick,
    onCognitiveNodeClick,
    onGrowthExecuted,
}) => {
    return (
        <section
            className="panel cut h-full flex flex-col relative overflow-hidden grain"
            data-testid="center-deck"
        >
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10 z-10 gap-2">
                <div className="flex items-center gap-2 shrink-0">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase truncate">
                        {TAB_LABELS[tab] || "core"}
                    </h2>
                </div>
                <div
                    className="flex items-center gap-1 flex-nowrap overflow-x-auto althea-scroll-h"
                    data-testid="center-tabs"
                >
                    {TABS.map((t) => (
                        <TabBtn
                            key={t.id}
                            active={tab === t.id}
                            onClick={() => setTab(t.id)}
                            testid={`center-tab-${t.id}`}
                            label={t.label}
                        />
                    ))}
                </div>
            </header>

            <div className="flex-1 relative min-h-0">
                <div
                    className="absolute inset-0"
                    style={{ visibility: tab === "neural" ? "visible" : "hidden" }}
                >
                    <NeuralCore
                        introspection={introspection}
                        embed
                        onLatticeNodeClick={onLatticeNodeClick}
                    />
                </div>
                {tab === "observe" && (
                    <div className="absolute inset-0">
                        <ObservationScreen
                            url={observationUrl}
                            setUrl={setObservationUrl}
                            watchLog={watchLog}
                            meta={observationMeta}
                        />
                    </div>
                )}
                {tab === "browser" && (
                    <div className="absolute inset-0">
                        <BrowserScreen onWatch={setObservationUrl} />
                    </div>
                )}
                {tab === "network" && (
                    <div className="absolute inset-0">
                        <NetworkScreen
                            onHostClick={onHostClick}
                            onCognitiveNodeClick={onCognitiveNodeClick}
                        />
                    </div>
                )}
                {tab === "connect" && (
                    <div className="absolute inset-0">
                        <ConnectScreen />
                    </div>
                )}
                {tab === "server" && (
                    <div className="absolute inset-0">
                        <ServerScreen />
                    </div>
                )}
                {tab === "code" && (
                    <div className="absolute inset-0">
                        <CodeScreen />
                    </div>
                )}
                {tab === "growth" && (
                    <div className="absolute inset-0">
                        <GrowthScreen onExecuted={onGrowthExecuted} />
                    </div>
                )}
                {tab === "satellite" && (
                    <div className="absolute inset-0">
                        <SatelliteScreen />
                    </div>
                )}
                {tab === "evolution" && (
                    <div className="absolute inset-0">
                        <EvolutionScreen />
                    </div>
                )}
                {tab === "quantum" && (
                    <div className="absolute inset-0">
                        <QuantumScreen />
                    </div>
                )}
                {tab === "troubleshoot" && (
                    <div className="absolute inset-0">
                        <TroubleshootScreen />
                    </div>
                )}
                {tab === "bci" && (
                    <div className="absolute inset-0">
                        <NeuralInterfaceScreen />
                    </div>
                )}
            </div>
        </section>
    );
};

const TabBtn = ({ active, onClick, testid, label }) => (
    <button
        onClick={onClick}
        data-testid={testid}
        className={`heading text-[10px] uppercase tracking-widest px-3 py-1 border whitespace-nowrap shrink-0 ${
            active
                ? "border-[#CCFF00]/60 text-[#CCFF00] bg-[#CCFF00]/10"
                : "border-white/10 text-[#888] hover:text-white"
        }`}
    >
        {label}
    </button>
);

export default CenterDeck;
