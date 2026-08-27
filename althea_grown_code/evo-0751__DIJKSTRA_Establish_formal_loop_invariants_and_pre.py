#!/usr/bin/env python3
"""SGP4 Orbital Propagator with Dijkstra-style Invariant Checking"""

import math
from typing import NamedTuple, Optional

class OrbitalState(NamedTuple):
    """Immutable state vector with proven bounds"""
    position: tuple[float, float, float]  # km, |r| in [6371, 50000]
    velocity: tuple[float, float, float]  # km/s, |v| in [0, 15]
    epoch_minutes: float  # minutes since epoch, >= 0

class Invariants:
    """Sacred invariants that must hold throughout propagation"""
    EARTH_RADIUS_KM = 6371.0
    MAX_ORBITAL_RADIUS_KM = 50000.0
    MAX_ORBITAL_VELOCITY_KM_S = 15.0
    MIN_ENERGY_THRESHOLD = -100.0  # MJ/kg, ensures bound orbit
    
    @staticmethod
    def check_state(state: OrbitalState, label: str) -> None:
        """Assert P(state) holds; abort if violated"""
        r_mag = math.sqrt(sum(x*x for x in state.position))
        v_mag = math.sqrt(sum(x*x for x in state.velocity))
        
        assert r_mag >= Invariants.EARTH_RADIUS_KM, f"{label}: collision {r_mag}"
        assert r_mag <= Invariants.MAX_ORBITAL_RADIUS_KM, f"{label}: escape {r_mag}"
        assert v_mag <= Invariants.MAX_ORBITAL_VELOCITY_KM_S, f"{label}: velocity {v_mag}"
        assert state.epoch_minutes >= 0, f"{label}: negative time"
        
        # Energy check: v²/2 - μ/r < 0 ensures elliptical orbit
        mu = 398600.4418  # km³/s²
        specific_energy = (v_mag * v_mag / 2.0) - (mu / r_mag)
        assert specific_energy < 0, f"{label}: unbound orbit E={specific_energy}"

def propagate_step(state: OrbitalState, dt_minutes: float) -> OrbitalState:
    """
    P: Invariants.check_state(state, "pre")
    Q: Invariants.check_state(result, "post") and result.epoch_minutes = state.epoch_minutes + dt_minutes
    """
    Invariants.check_state(state, "propagate_pre")
    
    # Simplified Kepler propagation (placeholder for full SGP4)
    mu = 398600.4418
    r_vec = state.position
    v_vec = state.velocity
    r = math.sqrt(sum(x*x for x in r_vec))
    
    # Ensure non-zero denominator
    assert r > Invariants.EARTH_RADIUS_KM, "Division by near-zero radius"
    
    dt_sec = dt_minutes * 60.0
    acc = tuple(-mu * x / (r**3) for x in r_vec)
    
    new_pos = tuple(r_vec[i] + v_vec[i] * dt_sec + 0.5 * acc[i] * dt_sec**2 for i in range(3))
    new_vel = tuple(v_vec[i] + acc[i] * dt_sec for i in range(3))
    new_epoch = state.epoch_minutes + dt_minutes
    
    result = OrbitalState(new_pos, new_vel, new_epoch)
    Invariants.check_state(result, "propagate_post")
    
    return result

def validate_tle_derived_state(pos: tuple, vel: tuple) -> Optional[OrbitalState]:
    """Parse and validate; return None if invariants violated"""
    try:
        state = OrbitalState(pos, vel, 0.0)
        Invariants.check_state(state, "tle_validation")
        return state
    except AssertionError:
        return None