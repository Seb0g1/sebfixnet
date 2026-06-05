mod singbox;

use singbox::SingBoxManager;
use tauri::Manager;

#[tauri::command]
fn start_connection(
    app: tauri::AppHandle,
    config_json: String,
    state: tauri::State<'_, SingBoxManager>,
) -> Result<String, String> {
    state.start(&app, &config_json)
}

#[tauri::command]
fn stop_connection(state: tauri::State<'_, SingBoxManager>) -> Result<String, String> {
    state.stop()
}

#[tauri::command]
fn get_connection_status(state: tauri::State<'_, SingBoxManager>) -> bool {
    state.is_running()
}

#[tauri::command]
fn copy_to_clipboard(text: String) -> Result<(), String> {
    use std::process::Command;
    Command::new("cmd")
        .args(["/C", "clip"])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .and_then(|mut child| {
            use std::io::Write;
            if let Some(stdin) = child.stdin.as_mut() {
                stdin.write_all(text.as_bytes()).map_err(|e| {
                    std::io::Error::new(std::io::ErrorKind::Other, e)
                })?;
            }
            child.wait()?;
            Ok(())
        })
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn open_telegram() -> Result<(), String> {
    open::that("https://t.me/Seb0g1").map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SingBoxManager::new())
        .invoke_handler(tauri::generate_handler![
            start_connection,
            stop_connection,
            get_connection_status,
            copy_to_clipboard,
            open_telegram,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
