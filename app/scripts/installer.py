"""FixInet.ez installer — packages as exe via PyInstaller."""
import os
import shutil
import sys
import zipfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None

APP_NAME = "FixInet.ez"
ZIP_NAME = "FixInet.ez-Portable-1.0.0.zip"
INSTALL_SUBDIR = "FixInet.ez"


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def main() -> None:
    install_root = Path(os.environ.get("LOCALAPPDATA", "")) / APP_NAME
    zip_path = resource_path(ZIP_NAME)

    if not zip_path.exists():
        msg = f"Package not found: {zip_path}"
        if tk:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(f"{APP_NAME} Setup", msg)
        else:
            print(msg)
        sys.exit(1)

    if install_root.exists():
        shutil.rmtree(install_root, ignore_errors=True)
    install_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(install_root)

    app_dir = install_root / INSTALL_SUBDIR
    target = app_dir / "FixInet.ez.bat"
    desktop = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
    try:
        import win32com.client  # type: ignore

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(desktop))
        shortcut.Targetpath = str(target)
        shortcut.WorkingDirectory = str(app_dir)
        shortcut.save()
    except Exception:
        pass

    msg = (
        f"{APP_NAME} установлен!\n\n"
        f"Папка: {app_dir}\n"
        f"Запустите FixInet.ez.bat\n\n"
        "При первом запуске введите ключ из Telegram-бота."
    )
    if tk:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(f"{APP_NAME} (By Seb0g1)", msg)
        if target.exists():
            os.startfile(str(target))
    else:
        print(msg)


if __name__ == "__main__":
    main()
