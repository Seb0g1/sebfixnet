mod singbox;

use std::sync::Mutex;

use singbox::SingBoxManager;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager, RunEvent, WindowEvent,
};

struct AppState {
    minimize_on_close: Mutex<bool>,
}

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
fn set_minimize_on_close(
    enabled: bool,
    app_state: tauri::State<'_, AppState>,
) -> Result<(), String> {
    *app_state.minimize_on_close.lock().unwrap() = enabled;
    Ok(())
}

#[tauri::command]
fn copy_to_clipboard(text: String) -> Result<(), String> {
    use std::io::Write;
    use std::process::Command;
    Command::new("cmd")
        .args(["/C", "clip"])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .and_then(|mut child| {
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

fn show_main_window(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

fn build_tray(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let show = MenuItem::with_id(app, "show", "Открыть", true, None::<&str>)?;
    let connect = MenuItem::with_id(app, "connect", "Подключить", true, None::<&str>)?;
    let disconnect = MenuItem::with_id(app, "disconnect", "Отключить", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Выход", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &connect, &disconnect, &quit])?;

    let icon = app
        .default_window_icon()
        .cloned()
        .ok_or("missing app icon")?;

    let _tray = TrayIconBuilder::new()
        .icon(icon)
        .menu(&menu)
        .tooltip("FixInet.ez")
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => show_main_window(app),
            "connect" => {
                let _ = app.emit("tray-connect", ());
                show_main_window(app);
            }
            "disconnect" => {
                let _ = app.emit("tray-disconnect", ());
            }
            "quit" => {
                if let Some(manager) = app.try_state::<SingBoxManager>() {
                    let _ = manager.stop();
                }
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main_window(tray.app_handle());
            }
        })
        .build(app)?;

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SingBoxManager::new())
        .manage(AppState {
            minimize_on_close: Mutex::new(true),
        })
        .invoke_handler(tauri::generate_handler![
            start_connection,
            stop_connection,
            get_connection_status,
            set_minimize_on_close,
            copy_to_clipboard,
            open_telegram,
        ])
        .setup(|app| {
            build_tray(app.handle())?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                let app_handle = window.app_handle().clone();
                let state = app_handle.state::<AppState>();
                let should_minimize = *state.minimize_on_close.lock().unwrap();
                if should_minimize {
                    let _ = window.hide();
                    api.prevent_close();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::ExitRequested { .. } = event {
            if let Some(manager) = app_handle.try_state::<SingBoxManager>() {
                let _ = manager.stop();
            }
        }
    });
}
