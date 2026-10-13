from dataclasses import dataclass
from typing import Callable, TypeVar, Generic, List
import numpy as np

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Signal(Generic[A]):
    """Immutable signal container with algebraic properties"""
    data: np.ndarray
    sample_rate: float
    metadata: tuple = ()
    
    def map(self, f: Callable[[np.ndarray], np.ndarray]) -> 'Signal[A]':
        """Functor: transform data while preserving structure"""
        return Signal(f(self.data), self.sample_rate, self.metadata)
    
    def compose(self, other: 'Signal[A]', op: Callable) -> 'Signal[A]':
        """Applicative: combine two signals algebraically"""
        return Signal(op(self.data, other.data), self.sample_rate, 
                     self.metadata + other.metadata)

@dataclass(frozen=True)
class Transform(Generic[A, B]):
    """Pure transform with composition laws"""
    func: Callable[[Signal[A]], Signal[B]]
    inverse: Callable[[Signal[B]], Signal[A]] = None
    name: str = "anonymous"
    
    def __call__(self, sig: Signal[A]) -> Signal[B]:
        return self.func(sig)
    
    def then(self, other: 'Transform[B, C]') -> 'Transform[A, C]':
        """Composition: (g ∘ f)(x) = g(f(x))"""
        return Transform(
            lambda s: other(self(s)),
            lambda s: self.inverse(other.inverse(s)) if self.inverse and other.inverse else None,
            f"{self.name} → {other.name}"
        )
    
    def parallel(self, other: 'Transform[A, B]') -> 'Transform[A, B]':
        """Product: apply both transforms, combine results"""
        return Transform(
            lambda s: self(s).compose(other(s), lambda x, y: (x + y) / 2),
            name=f"{self.name} ⊗ {other.name}"
        )

# Spectral algebra primitives
FFT = Transform(
    lambda s: s.map(np.fft.fft),
    lambda s: s.map(np.fft.ifft),
    "FFT"
)

PowerSpectrum = Transform(
    lambda s: s.map(lambda x: np.abs(x) ** 2),
    name="Power"
)

Normalize = Transform(
    lambda s: s.map(lambda x: x / (np.max(np.abs(x)) + 1e-10)),
    name="Normalize"
)

# Compose spectral pipeline declaratively
SpectralProfile = FFT.then(PowerSpectrum).then(Normalize)

def identity() -> Transform[A, A]:
    """Identity transform (monoid identity)"""
    return Transform(lambda s: s, lambda s: s, "id")

def frequency_band(low: float, high: float) -> Transform:
    """Declarative frequency filter as transform"""
    def band_filter(sig: Signal) -> Signal:
        freqs = np.fft.fftfreq(len(sig.data), 1/sig.sample_rate)
        mask = (np.abs(freqs) >= low) & (np.abs(freqs) <= high)
        return sig.map(lambda x: x * mask)
    return Transform(band_filter, name=f"Band[{low}-{high}Hz]")