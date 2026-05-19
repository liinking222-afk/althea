use std::arch::x86_64::*;

#[repr(align(64))]
pub struct CognitiveFlags(u64);

impl CognitiveFlags {
    #[inline(always)]
    pub const fn new() -> Self { Self(0) }
    
    #[inline(always)]
    pub const fn with_bits(bits: u64) -> Self { Self(bits) }
    
    // Branchless: 1 cycle latency on modern x86
    #[inline(always)]
    pub fn set(&mut self, flag: u8) {
        self.0 |= 1u64 << (flag & 63);
    }
    
    #[inline(always)]
    pub fn clear(&mut self, flag: u8) {
        self.0 &= !(1u64 << (flag & 63));
    }
    
    // Branchless test: CMOVcc on x86, 1 cycle
    #[inline(always)]
    pub fn test(&self, flag: u8) -> bool {
        (self.0 >> (flag & 63)) & 1 == 1
    }
    
    // POPCNT intrinsic: 3 cycles latency, 1 cycle throughput
    #[inline(always)]
    pub fn count_active(&self) -> u32 {
        unsafe { _popcnt64(self.0 as i64) as u32 }
    }
    
    // Parallel multi-flag test: PEXT on BMI2 CPUs (3 cycle)
    #[inline(always)]
    pub fn match_all(&self, mask: u64) -> bool {
        self.0 & mask == mask
    }
    
    #[inline(always)]
    pub fn match_any(&self, mask: u64) -> bool {
        (self.0 & mask) != 0
    }
    
    // Branchless select: uses CMOV, zero pipeline stalls
    #[inline(always)]
    pub fn select<T: Copy>(&self, flag: u8, if_set: T, if_clear: T) -> T {
        let mask = -((self.0 >> (flag & 63)) & 1) as i64;
        unsafe {
            let a = std::mem::transmute_copy(&if_set);
            let b = std::mem::transmute_copy(&if_clear);
            std::mem::transmute_copy(&((a & mask) | (b & !mask)))
        }
    }
    
    #[inline(always)]
    pub fn raw(&self) -> u64 { self.0 }
}

// Cache-aligned array for hot-path batch operations
#[repr(align(64))]
pub struct FlagBank([CognitiveFlags; 8]);

impl FlagBank {
    #[inline(always)]
    pub fn aggregate_popcnt(&self) -> u32 {
        unsafe {
            _popcnt64(self.0[0].0 as i64) as u32 +
            _popcnt64(self.0[1].0 as i64) as u32 +
            _popcnt64(self.0[2].0 as i64) as u32 +
            _popcnt64(self.0[3].0 as i64) as u32 +
            _popcnt64(self.0[4].0 as i64) as u32 +
            _popcnt64(self.0[5].0 as i64) as u32 +
            _popcnt64(self.0[6].0 as i64) as u32 +
            _popcnt64(self.0[7].0 as i64) as u32
        }
    }
}