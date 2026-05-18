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

