use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{AppHandle, Manager};

pub struct SingBoxManager {
    process: Mutex<Option<Child>>,
    elevated_pid: Mutex<Option<u32>>,
    config_path: Mutex<Option<PathBuf>>,
}

impl SingBoxManager {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
            elevated_pid: Mutex::new(None),
            config_path: Mutex::new(None),
        }
    }

    fn singbox_binary(app: &AppHandle) -> Result<PathBuf, String> {
        if let Ok(sidecar) = app.path().resolve(
            "binaries/sing-box-x86_64-pc-windows-msvc.exe",
            tauri::path::BaseDirectory::Resource,
        ) {
            if sidecar.exists() {
                return Ok(sidecar);
            }
        }

        if let Ok(sidecar) = app.path().resolve(
            "sing-box-x86_64-pc-windows-msvc.exe",
            tauri::path::BaseDirectory::Resource,
        ) {
            if sidecar.exists() {
                return Ok(sidecar);
            }
        }

        if let Ok(exe) = std::env::current_exe() {
            if let Some(dir) = exe.parent() {
                for name in [
                    "sing-box-x86_64-pc-windows-msvc.exe",
                    "sing-box.exe",
                ] {
                    let path = dir.join(name);
                    if path.exists() {
                        return Ok(path);
                    }
                }
            }
        }

        let resource_dir = app.path().resource_dir().map_err(|e| e.to_string())?;
        let candidates = [
            resource_dir.join("binaries").join("sing-box-x86_64-pc-windows-msvc.exe"),
            resource_dir.join("binaries").join("sing-box.exe"),
            PathBuf::from("binaries/sing-box.exe"),
        ];
        for path in candidates {
            if path.exists() {
                return Ok(path);
            }
        }

        Err("sing-box не найден. Переустановите FixInet.ez.".into())
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

    fn pid_file(app: &AppHandle) -> Result<PathBuf, String> {
        Ok(Self::config_dir(app)?.join("singbox.pid"))
    }

    #[cfg(windows)]
    fn spawn_elevated(binary: &Path, config: &Path, pid_file: &Path) -> Result<u32, String> {
        let binary_str = binary.to_string_lossy().replace('\'', "''");
        let config_str = config.to_string_lossy().replace('\'', "''");
        let pid_str = pid_file.to_string_lossy().replace('\'', "''");

        let script = format!(
            r#"
$ErrorActionPreference = 'Stop'
try {{
  $p = Start-Process -FilePath '{binary_str}' -ArgumentList @('run','-c','{config_str}') -Verb RunAs -WindowStyle Hidden -PassThru
  if (-not $p) {{ exit 2 }}
  Start-Sleep -Milliseconds 500
  $p.Id | Out-File -FilePath '{pid_str}' -Encoding ascii -NoNewline
  exit 0
}} catch {{
  exit 1
}}
"#
        );

        let status = Command::new("powershell")
            .args([
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                &script,
            ])
            .status()
            .map_err(|e| format!("Не удалось запустить sing-box: {e}"))?;

        if !status.success() {
            return Err(
                "Нужны права администратора для VPN. Подтвердите запрос UAC.".into(),
            );
        }

        if !pid_file.exists() {
            return Err("sing-box не запустился после UAC.".into());
        }

        let raw = fs::read_to_string(pid_file).map_err(|e| e.to_string())?;
        raw.trim()
            .parse::<u32>()
            .map_err(|_| "Не удалось прочитать PID sing-box.".into())
    }

    #[cfg(windows)]
    fn is_pid_running(pid: u32) -> bool {
        use windows::Win32::System::Threading::{
            OpenProcess, PROCESS_QUERY_LIMITED_INFORMATION,
        };
        use windows::Win32::Foundation::CloseHandle;

        unsafe {
            if let Ok(handle) = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, pid) {
                let _ = CloseHandle(handle);
                true
            } else {
                false
            }
        }
    }

    #[cfg(windows)]
    fn kill_pid(pid: u32) {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/F"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }

    #[cfg(not(windows))]
    fn spawn_elevated(_binary: &Path, _config: &Path, _pid_file: &Path) -> Result<u32, String> {
        Err("Elevated sing-box is only supported on Windows.".into())
    }

    #[cfg(not(windows))]
    fn is_pid_running(_pid: u32) -> bool {
        false
    }

    #[cfg(not(windows))]
    fn kill_pid(_pid: u32) {}

    pub fn start(&self, app: &AppHandle, config_json: &str) -> Result<String, String> {
        self.stop()?;

        let config_dir = Self::config_dir(app)?;
        let config_path = config_dir.join("singbox.json");
        fs::write(&config_path, config_json).map_err(|e| e.to_string())?;

        let binary = Self::singbox_binary(app)?;
        let pid_file = Self::pid_file(app)?;

        #[cfg(windows)]
        {
            let pid = Self::spawn_elevated(&binary, &config_path, &pid_file)?;
            *self.elevated_pid.lock().unwrap() = Some(pid);
            *self.config_path.lock().unwrap() = Some(config_path);
            return Ok("Connected".into());
        }

        #[cfg(not(windows))]
        {
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
    }

    pub fn stop(&self) -> Result<String, String> {
        #[cfg(windows)]
        {
            if let Some(pid) = self.elevated_pid.lock().unwrap().take() {
                Self::kill_pid(pid);
            }
        }

        let mut guard = self.process.lock().unwrap();
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }

        Ok("Disconnected".into())
    }

    pub fn is_running(&self) -> bool {
        #[cfg(windows)]
        {
            let mut guard = self.elevated_pid.lock().unwrap();
            if let Some(pid) = *guard {
                if Self::is_pid_running(pid) {
                    return true;
                }
                *guard = None;
            }
            return false;
        }

        #[cfg(not(windows))]
        {
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
}
