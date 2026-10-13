use std::fs::{File, OpenOptions};
use std::io::{Read, Write, Seek, SeekFrom};
use std::path::Path;

const RECORD_SIZE: usize = 256;
const NAME_SIZE: usize = 64;
const SIGNATURE_SIZE: usize = 128;
const VERSION_SIZE: usize = 16;
const FLAGS_SIZE: usize = 8;

#[repr(C, packed)]
struct ModuleRecord {
    name: [u8; NAME_SIZE],
    signature: [u8; SIGNATURE_SIZE],
    version: [u8; VERSION_SIZE],
    flags: u64,
    invocation_count: u64,
    last_access: u64,
    _padding: [u8; RECORD_SIZE - NAME_SIZE - SIGNATURE_SIZE - VERSION_SIZE - FLAGS_SIZE - 16],
}

impl ModuleRecord {
    fn empty() -> Self {
        ModuleRecord {
            name: [0; NAME_SIZE],
            signature: [0; SIGNATURE_SIZE],
            version: [0; VERSION_SIZE],
            flags: 0,
            invocation_count: 0,
            last_access: 0,
            _padding: [0; RECORD_SIZE - NAME_SIZE - SIGNATURE_SIZE - VERSION_SIZE - FLAGS_SIZE - 16],
        }
    }

    fn from_bytes(buf: &[u8; RECORD_SIZE]) -> Self {
        unsafe { std::ptr::read(buf.as_ptr() as *const ModuleRecord) }
    }

    fn to_bytes(&self) -> [u8; RECORD_SIZE] {
        unsafe { std::ptr::read(self as *const ModuleRecord as *const [u8; RECORD_SIZE]) }
    }
}

pub struct ModuleRegistry {
    file: File,
    index: Vec<u64>,
}

impl ModuleRegistry {
    pub fn open(path: &Path) -> std::io::Result<Self> {
        let mut file = OpenOptions::new().read(true).write(true).create(true).open(path)?;
        let mut index = Vec::new();
        let mut offset = 0u64;
        loop {
            let mut buf = [0u8; RECORD_SIZE];
            match file.read_exact(&mut buf) {
                Ok(_) => {
                    let rec = ModuleRecord::from_bytes(&buf);
                    if rec.name[0] != 0 {
                        index.push(offset);
                    }
                    offset += RECORD_SIZE as u64;
                }
                Err(_) => break,
            }
        }
        Ok(ModuleRegistry { file, index })
    }

    pub fn get(&mut self, name: &str) -> std::io::Result<Option<ModuleRecord>> {
        for &offset in &self.index {
            self.file.seek(SeekFrom::Start(offset))?;
            let mut buf = [0u8; RECORD_SIZE];
            self.file.read_exact(&mut buf)?;
            let rec = ModuleRecord::from_bytes(&buf);
            if rec.name.starts_with(name.as_bytes()) {
                return Ok(Some(rec));
            }
        }
        Ok(None)
    }
}