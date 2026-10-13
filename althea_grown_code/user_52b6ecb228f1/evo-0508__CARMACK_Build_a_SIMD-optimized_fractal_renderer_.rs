use std::arch::x86_64::*;

// Mandelbrot hot path: 4 pixels parallel via SSE2, cache-aligned scanlines
// Why: Fractal compute is embarrassingly parallel + float-heavy. Carmack would inline everything,
// use SIMD, precompute constants, and treat the inner loop as sacred performance territory.

#[repr(align(16))]
struct AlignedScanline([u32; 256]); // Cache-line friendly, power-of-2 width

#[inline(always)]
unsafe fn mandel_sse2(cr: __m128, ci: __m128, max_iter: i32) -> __m128i {
    let four = _mm_set1_ps(4.0);
    let one = _mm_set1_epi32(1);
    let mut zr = _mm_setzero_ps();
    let mut zi = _mm_setzero_ps();
    let mut count = _mm_setzero_si128();
    
    for _ in 0..max_iter {
        let zr2 = _mm_mul_ps(zr, zr);
        let zi2 = _mm_mul_ps(zi, zi);
        let mag2 = _mm_add_ps(zr2, zi2);
        let mask = _mm_castps_si128(_mm_cmplt_ps(mag2, four));
        
        if _mm_movemask_epi8(mask) == 0 { break; } // All diverged, early exit
        
        let zrzi = _mm_mul_ps(zr, zi);
        zi = _mm_add_ps(_mm_add_ps(zrzi, zrzi), ci);
        zr = _mm_add_ps(_mm_sub_ps(zr2, zi2), cr);
        
        count = _mm_sub_epi32(count, _mm_and_si128(mask, one));
    }
    count
}

pub fn render_fractal_optimized(width: usize, height: usize, max_iter: i32) -> Vec<u32> {
    assert_eq!(width, 256); // Fixed for cache optimization
    let mut buffer = vec![0u32; width * height];
    let x_scale = 3.5 / width as f32;
    let y_scale = 2.0 / height as f32;
    
    unsafe {
        for y in 0..height {
            let scanline = &mut buffer[y * width..(y + 1) * width];
            let cy = y as f32 * y_scale - 1.0;
            let ci = _mm_set1_ps(cy);
            
            for x in (0..width).step_by(4) {
                let cx = _mm_set_ps(
                    (x + 3) as f32 * x_scale - 2.5,
                    (x + 2) as f32 * x_scale - 2.5,
                    (x + 1) as f32 * x_scale - 2.5,
                    x as f32 * x_scale - 2.5,
                );
                let iters = mandel_sse2(cx, ci, max_iter);
                let mut result = [0i32; 4];
                _mm_storeu_si128(result.as_mut_ptr() as *mut __m128i, iters);
                
                scanline[x] = result[0] as u32;
                scanline[x + 1] = result[1] as u32;
                scanline[x + 2] = result[2] as u32;
                scanline[x + 3] = result[3] as u32;
            }
        }
    }
    buffer
}