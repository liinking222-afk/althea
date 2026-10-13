#![allow(dead_code)]
use std::arch::x86_64::*;

#[repr(align(32))]
#[derive(Copy, Clone)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    _pad: f64, // Cache line alignment for streaming
}

#[repr(align(64))]
#[derive(Copy, Clone)]
pub struct OrbitalState {
    pub pos: Vec3,
    pub vel: Vec3,
}

impl Vec3 {
    #[inline(always)]
    pub const fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z, _pad: 0.0 }
    }

    #[inline(always)]
    pub fn dot(&self, other: &Vec3) -> f64 {
        // Compiler auto-vectorizes with -C target-cpu=native
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    #[inline(always)]
    pub fn cross(&self, other: &Vec3) -> Vec3 {
        Vec3::new(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )
    }

    #[inline(always)]
    pub fn mag_sq(&self) -> f64 {
        self.dot(self)
    }

    #[inline(always)]
    pub fn mag(&self) -> f64 {
        self.mag_sq().sqrt() // Single sqrt, no intermediate vars
    }

    #[inline(always)]
    pub fn scale(&self, s: f64) -> Vec3 {
        Vec3::new(self.x * s, self.y * s, self.z * s)
    }

    #[inline(always)]
    pub fn add(&self, other: &Vec3) -> Vec3 {
        Vec3::new(self.x + other.x, self.y + other.y, self.z + other.z)
    }
}

impl OrbitalState {
    #[inline(always)]
    pub fn propagate_step(&mut self, accel: &Vec3, dt: f64) {
        // Verlet integration hot path - no branching, cache-coherent
        let dt_sq_half = 0.5 * dt * dt;
        self.pos.x += self.vel.x * dt + accel.x * dt_sq_half;
        self.pos.y += self.vel.y * dt + accel.y * dt_sq_half;
        self.pos.z += self.vel.z * dt + accel.z * dt_sq_half;
        self.vel.x += accel.x * dt;
        self.vel.y += accel.y * dt;
        self.vel.z += accel.z * dt;
    }
}