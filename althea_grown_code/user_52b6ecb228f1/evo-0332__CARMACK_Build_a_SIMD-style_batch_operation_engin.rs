use std::arch::x86_64::*;
use std::simd::{f32x8, SimdFloat};

const CACHE_LINE: usize = 64;
const BATCH_SIZE: usize = 8;

#[repr(C, align(64))]
struct OpBatch {
    weights: [f32; BATCH_SIZE],
    inputs: [f32; BATCH_SIZE],
    outputs: [f32; BATCH_SIZE],
    op_type: u8,
}

pub struct VectorizedCognition {
    batches: Vec<OpBatch>,
    hot_buffer: [OpBatch; 4],
    cursor: usize,
}

impl VectorizedCognition {
    #[inline(always)]
    pub fn process_hot(&mut self) {
        for batch in &mut self.hot_buffer {
            let w = f32x8::from_array(batch.weights);
            let i = f32x8::from_array(batch.inputs);
            
            let result = match batch.op_type {
                0 => w * i,                              // multiply: 1 cycle latency
                1 => (w * i).simd_max(f32x8::splat(0.0)), // relu: 2 cycles
                2 => {    // tanh approx: 8 cycles
                    let x = w * i;
                    let x2 = x * x;
                    x * (f32x8::splat(27.0) + x2) / 
                    (f32x8::splat(27.0) + f32x8::splat(9.0) * x2)
                },
                _ => w + i,                              // fallback add: 1 cycle
            };
            
            batch.outputs = result.to_array();
        }
    }
    
    #[inline(always)]
    pub fn enqueue(&mut self, w: f32, i: f32, op: u8) -> f32 {
        let idx = self.cursor % BATCH_SIZE;
        let batch_idx = self.cursor / BATCH_SIZE % 4;
        
        self.hot_buffer[batch_idx].weights[idx] = w;
        self.hot_buffer[batch_idx].inputs[idx] = i;
        self.hot_buffer[batch_idx].op_type = op;
        
        if idx == BATCH_SIZE - 1 { self.process_hot(); }
        
        self.cursor += 1;
        self.hot_buffer[batch_idx].outputs[idx]
    }
}