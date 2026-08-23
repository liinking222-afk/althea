#[repr(C, packed)]
pub struct TLEElements {
    pub epoch_year: u8,
    pub epoch_day: f64,
    pub mean_motion_d1: f64,
    pub mean_motion_d2: f64,
    pub bstar: f64,
    pub inclination: f64,
    pub raan: f64,
    pub eccentricity: f64,
    pub arg_perigee: f64,
    pub mean_anomaly: f64,
    pub mean_motion: f64,
    pub rev_number: u32,
}

pub struct TLEParser<'a> {
    line1: &'a [u8],
    line2: &'a [u8],
}

impl<'a> TLEParser<'a> {
    #[inline]
    pub fn new(line1: &'a str, line2: &'a str) -> Option<Self> {
        let l1 = line1.as_bytes();
        let l2 = line2.as_bytes();
        if l1.len() != 69 || l2.len() != 69 || l1[0] != b'1' || l2[0] != b'2' {
            return None;
        }
        Some(TLEParser { line1: l1, line2: l2 })
    }

    #[inline]
    fn parse_f64(&self, line: &[u8], start: usize, end: usize) -> f64 {
        unsafe { std::str::from_utf8_unchecked(&line[start..end]) }
            .trim()
            .parse()
            .unwrap_or(0.0)
    }

    #[inline]
    fn parse_decimal(&self, s: &[u8]) -> f64 {
        let sign = if s[0] == b'-' { -1.0 } else { 1.0 };
        let digits = unsafe { std::str::from_utf8_unchecked(&s[1..s.len()-2]) };
        let exp: i32 = (s[s.len()-1] as char).to_digit(10).unwrap_or(0) as i32;
        sign * digits.parse::<f64>().unwrap_or(0.0) * 10f64.powi(-exp)
    }

    pub fn parse(&self) -> TLEElements {
        TLEElements {
            epoch_year: self.parse_f64(self.line1, 18, 20) as u8,
            epoch_day: self.parse_f64(self.line1, 20, 32),
            mean_motion_d1: self.parse_f64(self.line1, 33, 43),
            mean_motion_d2: self.parse_decimal(&self.line1[44..52]),
            bstar: self.parse_decimal(&self.line1[53..61]),
            inclination: self.parse_f64(self.line2, 8, 16),
            raan: self.parse_f64(self.line2, 17, 25),
            eccentricity: self.parse_f64(self.line2, 26, 33) / 1e7,
            arg_perigee: self.parse_f64(self.line2, 34, 42),
            mean_anomaly: self.parse_f64(self.line2, 43, 51),
            mean_motion: self.parse_f64(self.line2, 52, 63),
            rev_number: self.parse_f64(self.line2, 63, 68) as u32,
        }
    }
}