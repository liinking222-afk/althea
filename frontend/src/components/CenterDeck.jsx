import React from "react";
import NeuralCore from "@/components/NeuralCore";
import ObservationScreen from "@/components/ObservationScreen";
import NetworkScreen from "@/components/NetworkScreen";
import ConnectScreen from "@/components/ConnectScreen";
import GrowthScreen from "@/components/GrowthScreen";

const TAB_LABELS = {
    neural: "neural core // live lattice",
    observe: "observation // optical input",
    network: "network // interaction graph",
    connect: "connect // device + wi-fi bridge",
    growth: "autopoiesis // grown capabilities",
};

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
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10 z-10">
                <div className="flex items-center gap-2">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase">
                        {TAB_LABELS[tab] || "core"}
                    </h2>
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                    <TabBtn active={tab === "neural"} onClick={() => setTab("neural")} testid="center-tab-neural" label="neural" />
                    <TabBtn active={tab === "observe"} onClick={() => setTab("observe")} testid="center-tab-observe" label="observe" />
                    <TabBtn active={tab === "network"} onClick={() => setTab("network")} testid="center-tab-network" label="network" />
                    <TabBtn active={tab === "connect"} onClick={() => setTab("connect")} testid="center-tab-connect" label="connect" />
                    <TabBtn active={tab === "growth"} onClick={() => setTab("growth")} testid="center-tab-growth" label="growth" />
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
                {tab === "growth" && (
                    <div className="absolute inset-0">
                        <GrowthScreen onExecuted={onGrowthExecuted} />
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
        className={`heading text-[10px] uppercase tracking-widest px-3 py-1 border ${
            active
                ? "border-[#CCFF00]/60 text-[#CCFF00] bg-[#CCFF00]/10"
                : "border-white/10 text-[#888] hover:text-white"
        }`}
    >
        {label}
    </button>
);

export default CenterDeck;
