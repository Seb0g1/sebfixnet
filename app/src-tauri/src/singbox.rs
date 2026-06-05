use std::fs;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{AppHandle, Manager};

pub struct SingBoxManager {
    process: Mutex<Option<Child>>,
    config_path: Mutex<Option<PathBuf>>,
}

impl SingBoxManager {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
            config_path: Mutex::new(None),
        }
    }

    fn singbox_binary(app: &AppHandle) -> Result<PathBuf, String> {
        let resource_dir = app
            .path()
            .resource_dir()
            .map_err(|e| e.to_string())?;

        let candidates = [
            resource_dir.join("binaries").join("sing-box.exe"),
            resource_dir.join("sing-box.exe"),
            PathBuf::from("binaries/sing-box.exe"),
        ];

        for path in candidates {
            if path.exists() {
                return Ok(path);
            }
        }

        if let Ok(sidecar) = app.path().resolve("binaries/sing-box", tauri::path::BaseDirectory::Resource) {
            if sidecar.exists() {
                return Ok(sidecar);
            }
        }

        Err(
            "sing-box.exe not found. Place it in src-tauri/binaries/ before building.".into(),
        )
    }

    fn config_dir(app: &AppHandle) -> Result<PathBuf, String> {
        let dir = app
            .path()
            .app_data_dir()
            .map_err(|e| e.to_string())?
            .join("config");
        fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
        Ok(dir)
    }

    pub fn start(&self, app: &AppHandle, config_json: &str) -> Result<String, String> {
        self.stop()?;

        let config_dir = Self::config_dir(app)?;
        let config_path = config_dir.join("singbox.json");
        fs::write(&config_path, config_json).map_err(|e| e.to_string())?;

        let binary = Self::singbox_binary(app)?;
        let child = Command::new(&binary)
            .args(["run", "-c", config_path.to_str().unwrap_or_default()])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Failed to start sing-box: {e}"))?;

        *self.process.lock().unwrap() = Some(child);
        *self.config_path.lock().unwrap() = Some(config_path);

        Ok("Connected".into())
    }

    pub fn stop(&self) -> Result<String, String> {
        let mut guard = self.process.lock().unwrap();
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
        Ok("Disconnected".into())
    }

    pub fn is_running(&self) -> bool {
        let mut guard = self.process.lock().unwrap();
        if let Some(child) = guard.as_mut() {
            match child.try_wait() {
                Ok(None) => return true,
                _ => {
                    *guard = None;
                    return false;
                }
            }
        }
        false
    }
}
