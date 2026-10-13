use std::fs::{File, OpenOptions};
use std::io::{Read, Write, Seek, SeekFrom};
use std::path::Path;

const RECORD_SIZE: usize = 128;
const PATTERN_LEN: usize = 48;
const OUTCOME_LEN: usize = 48;
const METRIC_SIZE: usize = 8;

#[repr(C, packed)]
struct MemoryRecord {
    pattern_hash: [u8; PATTERN_LEN],
    outcome_hash: [u8; OUTCOME_LEN],
    density_score: f64,
    resonance_flag: u64,
    timestamp: u64,
}

impl MemoryRecord {
    fn to_bytes(&self) -> [u8; RECORD_SIZE] {
        let mut buf = [0u8; RECORD_SIZE];
        buf[..PATTERN_LEN].copy_from_slice(&self.pattern_hash);
        buf[PATTERN_LEN..PATTERN_LEN+OUTCOME_LEN].copy_from_slice(&self.outcome_hash);
        buf[96..104].copy_from_slice(&self.density_score.to_le_bytes());
        buf[104..112].copy_from_slice(&self.resonance_flag.to_le_bytes());
        buf[112..120].copy_from_slice(&self.timestamp.to_le_bytes());
        buf
    }

    fn from_bytes(buf: &[u8; RECORD_SIZE]) -> Self {
        let mut pattern_hash = [0u8; PATTERN_LEN];
        let mut outcome_hash = [0u8; OUTCOME_LEN];
        pattern_hash.copy_from_slice(&buf[..PATTERN_LEN]);
        outcome_hash.copy_from_slice(&buf[PATTERN_LEN..PATTERN_LEN+OUTCOME_LEN]);
        
        MemoryRecord {
            pattern_hash,
            outcome_hash,
            density_score: f64::from_le_bytes(buf[96..104].try_into().unwrap()),
            resonance_flag: u64::from_le_bytes(buf[104..112].try_into().unwrap()),
            timestamp: u64::from_le_bytes(buf[112..120].try_into().unwrap()),
        }
    }
}

pub struct MemoryIndex {
    file: File,
}

impl MemoryIndex {
    pub fn open(path: &Path) -> std::io::Result<Self> {
        let file = OpenOptions::new().read(true).write(true).create(true).open(path)?;
        Ok(MemoryIndex { file })
    }

    pub fn write_record(&mut self, pattern: &str, outcome: &str, density: f64, resonance: u64) -> std::io::Result<u64> {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let record = MemoryRecord {
            pattern_hash: hash_to_fixed(pattern),
            outcome_hash: hash_to_fixed(outcome),
            density_score: density,
            resonance_flag: resonance,
            timestamp,
        };
        
        self.file.seek(SeekFrom::End(0))?;
        let offset = self.file.stream_position()?;
        self.file.write_all(&record.to_bytes())?;
        Ok(offset / RECORD_SIZE as u64)
    }

    pub fn read_record(&mut self, index: u64) -> std::io::Result<MemoryRecord> {
        let mut buf = [0u8; RECORD_SIZE];
        self.file.seek(SeekFrom::Start(index * RECORD_SIZE as u64))?;
        self.file.read_exact(&mut buf)?;
        Ok(MemoryRecord::from_bytes(&buf))
    }
}

fn hash_to_fixed(s: &str) -> [u8; PATTERN_LEN] {
    let mut result = [0u8; PATTERN_LEN];
    let bytes = s.as_bytes();
    for (i, &b) in bytes.iter().take(PATTERN_LEN).enumerate() {
        result[i] = b;
    }
    result
}