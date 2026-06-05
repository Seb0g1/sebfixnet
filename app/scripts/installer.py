"""Minimal InetFix installer - packages as exe via PyInstaller."""
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


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def main() -> None:
    install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "InetFix"
    zip_path = resource_path("InetFix-Portable-1.0.0.zip")

    if not zip_path.exists():
        msg = f"Package not found: {zip_path}"
        if tk:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("InetFix Setup", msg)
        else:
            print(msg)
        sys.exit(1)

    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)
    install_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(install_dir)

    desktop = Path.home() / "Desktop" / "InetFix.lnk"
    target = install_dir / "InetFix" / "InetFix.bat"
    try:
        import win32com.client  # type: ignore

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(desktop))
        shortcut.Targetpath = str(target)
        shortcut.WorkingDirectory = str(target.parent)
        shortcut.save()
    except Exception:
        pass

    msg = f"InetFix установлен!\n\nПапка: {install_dir / 'InetFix'}\nЗапустите InetFix.bat"
    if tk:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("InetFix (By Seb0g1)", msg)
    else:
        print(msg)


if __name__ == "__main__":
    main()
