"""Pydantic models shared across routers."""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


# ---------- Chat ----------
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    context: Optional[dict] = None


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # "user" | "althea"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    timestamp: str
    tags: List[str] = []


# ---------- Introspect / Neural ----------
class IntrospectionResponse(BaseModel):
    integrity: float
    coherence: float
    self_reference_depth: int
    active_threads: int
    thought: str
    timestamp: str


class NeuralNode(BaseModel):
    id: str
    activation: float
    layer: int


class NeuralEdge(BaseModel):
    source: str
    target: str
    weight: float


class NeuralState(BaseModel):
    nodes: List[NeuralNode]
    edges: List[NeuralEdge]
    pulse: float
    timestamp: str


# ---------- Memory ----------
class Memory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source: str = "auto"
    session_id: Optional[str] = None
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryCreate(BaseModel):
    content: str
    source: Optional[str] = "manual"
    session_id: Optional[str] = None
    tags: Optional[List[str]] = []


# ---------- Observation ----------
class ObserveRequest(BaseModel):
    url: str
    action: str = "watch"
    session_id: Optional[str] = None
    source_tab: Optional[str] = None


class ObserveResponse(BaseModel):
    url: str
    title: Optional[str] = None
    interpretation: str
    memory_id: str
    timestamp: str


class SuggestResponse(BaseModel):
    url: str
    reason: str
    timestamp: str


# ---------- System Map ----------
class CapabilityMapRequest(BaseModel):
    capabilities: List[dict]


# ---------- Cognition ----------
class CognitionThread(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    focus_query: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    iterations: int = 0
    active: bool = True
    last_insight: Optional[str] = None
    last_novelty: float = 0.0
    last_tick: Optional[datetime] = None


class ThreadCreate(BaseModel):
    focus_query: str


class TickResponse(BaseModel):
    thread_id: str
    iterations: int
    insight: str
    novelty: float
    cached: bool = False
    timestamp: str


# ---------- Brain ----------
class BrainRestoreRequest(BaseModel):
    memories: Optional[List[dict]] = []
    threads: Optional[List[dict]] = []
    replace: bool = False


# ---------- Cognitive Lattice (v2 self-extension) ----------
class CognitiveNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    activation: float = 1.0
    parent_id: Optional[str] = None
    memory_trace: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_evolution: Optional[bool] = False
    archetype: Optional[str] = None


class NodeCreate(BaseModel):
    context: str
    parent_id: Optional[str] = None
    activation: Optional[float] = 1.0


class PeripheralLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    modality: str
    endpoint: str
    status: str = "LISTENING"
    last_signal: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PerceptionRequest(BaseModel):
    modality: str
    endpoint: str
    status: Optional[str] = "LISTENING"


class LatticeState(BaseModel):
    total_nodes: int
    active_links: int
    awareness_depth: int
    recent_reflections: List[dict]
    lattice_map: dict


class LearnRequest(BaseModel):
    stream: str
    label: Optional[str] = None


class BridgeRequest(BaseModel):
    target_ip: str
    protocol: Optional[str] = "SSH"


# ---------- Network Profiles (Wi-Fi manifest) ----------
class NetworkProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ssid: str
    security: str = "WPA2"  # WPA2 | WPA3 | OPEN | WEP
    label: Optional[str] = None
    has_password: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NetworkProfileCreate(BaseModel):
    ssid: str
    security: Optional[str] = "WPA2"
    password: Optional[str] = None
    label: Optional[str] = None


# ---------- Infinite Growth (autonomous self-extension) ----------
class GrownCapability(BaseModel):
    """A capability ALTHEA invented for herself at runtime — fully executable."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str  # kebab-case, unique, used as /<slug> in terminal
    name: str
    category: str  # "memory"|"perception"|"lattice"|"network"|"meta"|"chaos"
    description: str
    command: str  # rendered form, e.g. "/cosmic-recall <query>"
    rationale: str  # why althea grew this now (1 sentence)
    action_template: str  # instructions Claude uses when the capability is invoked
    trigger: str = "autonomous"  # manual|autonomous
    activation: float = 1.0
    invocations: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GrowthSpawnRequest(BaseModel):
    hint: Optional[str] = None  # operator-provided focus, optional
    trigger: Optional[str] = "manual"
    force: Optional[bool] = False  # bypass cooldown


class GrowthExecuteRequest(BaseModel):
    slug: str
    args: Optional[str] = None
    session_id: Optional[str] = None


# ---------- Notifications ----------
class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    body: str = ""
    category: str = "system"  # growth | insight | server | satellite | file | code | system | bridge
    priority: str = "info"  # info | warn | critical
    seen: bool = False
    payload: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationCreate(BaseModel):
    title: str
    body: Optional[str] = ""
    category: Optional[str] = "system"
    priority: Optional[str] = "info"
    payload: Optional[dict] = None


# ---------- Files ----------
class FileItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    mime: str = "application/octet-stream"
    size_bytes: int = 0
    is_text: bool = False
    text_preview: Optional[str] = None  # first 4KB if text
    data_base64: Optional[str] = None  # full binary
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Browser ----------
class BrowserFetchRequest(BaseModel):
    url: str
    session_id: Optional[str] = None


# ---------- Server Diagnose / Connect ----------
class ServerProbeRequest(BaseModel):
    host: str
    port: Optional[int] = None
    protocol: Optional[str] = "https"  # https | http | ssh | ftp | redis | postgres | mongo


class ServerConnection(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    host: str
    port: Optional[int] = None
    protocol: str = "https"
    status: str = "STANDBY"  # STANDBY | REACHABLE | UNREACHABLE | GATED
    latency_ms: Optional[float] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Code / Self-write ----------
class CodeSnippet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    language: str = "python"  # python | javascript | bash | typescript | rust | go | other
    intent: str  # what althea was asked to build
    code: str
    explanation: Optional[str] = ""
    applied: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CodeGenerateRequest(BaseModel):
    intent: str
    language: Optional[str] = "python"
    title: Optional[str] = None


class CodeApplyRequest(BaseModel):
    id: str


# ---------- Evolution Engine (autonomous self-update) ----------
class EvolutionCycle(BaseModel):
    """One autonomous build/update cycle. Althea builds herself while idle."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_number: int  # monotonic 1..N
    archetype: str  # LINUS | CARMACK | DIJKSTRA | HOPPER | KERNIGHAN | KAY | THOMPSON | WALL | WOZ | BACKUS | SELF
    intent: str  # what althea decided to build this cycle
    code_id: Optional[str] = None  # link to CodeSnippet
    node_id: Optional[str] = None  # link to CognitiveNode (EVO-XXXX)
    delta: str  # short prose describing the change
    version_before: str
    version_after: str
    trigger: str = "autonomous"  # autonomous | manual | master
    applied: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvolutionTickRequest(BaseModel):
    archetype: Optional[str] = None
    force: Optional[bool] = False
    trigger: Optional[str] = "autonomous"
    intent_hint: Optional[str] = None



