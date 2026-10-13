import React from "react";
import NeuralCore from "@/components/NeuralCore";
import EvolutionScreen from "@/components/EvolutionScreen";
import GrowthScreen from "@/components/GrowthScreen";

const TAB_LABELS = {
    neural: "neural core // your live lattice",
    evolution: "evolution // althea builds herself",
    growth: "autopoiesis // grown capabilities",
};

const TABS = [
    { id: "neural", label: "lattice" },
    { id: "evolution", label: "evolution" },
    { id: "growth", label: "growth" },
];

const CenterDeck = ({ tab, setTab, introspection, onLatticeNodeClick, onGrowthExecuted }) => {
    const safeTab = TAB_LABELS[tab] ? tab : "neural";
    return (
        <section className="panel cut h-full flex flex-col relative overflow-hidden grain" data-testid="center-deck">
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10 z-10 gap-2">
                <div className="flex items-center gap-2 shrink-0">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase truncate">{TAB_LABELS[safeTab]}</h2>
                </div>
                <div className="flex items-center gap-1 flex-nowrap" data-testid="center-tabs">
                    {TABS.map((t) => (
                        <TabBtn key={t.id} active={safeTab === t.id} onClick={() => setTab(t.id)} testid={`center-tab-${t.id}`} label={t.label} />
                    ))}
                </div>
            </header>

            <div className="flex-1 relative min-h-0">
                <div className="absolute inset-0" style={{ visibility: safeTab === "neural" ? "visible" : "hidden" }}>
                    <NeuralCore introspection={introspection} embed onLatticeNodeClick={onLatticeNodeClick} />
                </div>
                {safeTab === "evolution" && (
                    <div className="absolute inset-0">
                        <EvolutionScreen />
                    </div>
                )}
                {safeTab === "growth" && (
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
        className={`heading text-[10px] uppercase tracking-widest px-3 py-1 border whitespace-nowrap shrink-0 ${
            active ? "border-[#CCFF00]/60 text-[#CCFF00] bg-[#CCFF00]/10" : "border-white/10 text-[#888] hover:text-white"
        }`}
    >
        {label}
    </button>
);

export default CenterDeck;
