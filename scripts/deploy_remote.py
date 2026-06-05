#!/usr/bin/env python3
"""Deploy sebfixnet to remote server via SSH."""
import base64
import sys
from pathlib import Path

import paramiko

import os

HOST = os.environ.get("DEPLOY_HOST", "5.129.238.210")
USER = os.environ.get("DEPLOY_USER", "root")
PASSWORD = os.environ.get("DEPLOY_PASSWORD", "")
APP_DIR = "/opt/sebfixnet"
ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if not PASSWORD:
        print("Set DEPLOY_PASSWORD env var", file=sys.stderr)
        return 1

    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Missing .env", file=sys.stderr)
        return 1

    env_b64 = base64.b64encode(env_path.read_bytes()).decode("ascii")
    deploy_script = (ROOT / "server" / "deploy.sh").read_text(encoding="utf-8")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    sftp = client.open_sftp()
    try:
        sftp.mkdir(APP_DIR)
    except OSError:
        pass

    with sftp.file("/tmp/sebfixnet-deploy.sh", "w") as f:
        f.write(deploy_script)
    sftp.chmod("/tmp/sebfixnet-deploy.sh", 0o755)
    sftp.close()

    cmd = f"export DEPLOY_ENV_B64='{env_b64}'; bash /tmp/sebfixnet-deploy.sh"
    print("Running deploy script (may take a few minutes)...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()

    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    client.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
