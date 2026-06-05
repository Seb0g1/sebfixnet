import json
from pathlib import Path
from typing import Any

from config import settings


def load_services() -> dict[str, Any]:
    path = settings.services_path
    if not path.exists():
        alt = Path("/app/shared/services.json")
        path = alt if alt.exists() else path
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def domains_for_services(service_ids: list[str]) -> list[str]:
    catalog = load_services()
    domains: list[str] = []
    for sid in service_ids:
        entry = catalog.get(sid)
        if entry:
            domains.extend(entry.get("domains", []))
    return sorted(set(domains))


def build_singbox_config(
    vless_uuid: str,
    mode: str = "combined",
    selected_services: list[str] | None = None,
) -> dict[str, Any]:
    selected_services = selected_services or ["telegram", "discord", "youtube"]
    proxy_domains = domains_for_services(selected_services) if mode == "combined" else []

    vless_outbound = {
        "type": "vless",
        "tag": "proxy",
        "server": settings.vless_server,
        "server_port": settings.vless_port,
        "uuid": vless_uuid,
        "flow": settings.vless_flow,
        "tls": {
            "enabled": True,
            "server_name": settings.vless_sni,
            "utls": {"enabled": True, "fingerprint": "chrome"},
            "reality": {
                "enabled": True,
                "public_key": settings.vless_public_key,
                "short_id": settings.vless_short_id,
            },
        },
    }

    route_rules: list[dict[str, Any]] = [
        {"protocol": "dns", "outbound": "dns-out"},
        {"ip_is_private": True, "outbound": "direct"},
    ]

    if mode == "combined" and proxy_domains:
        route_rules.insert(1, {"domain": proxy_domains, "outbound": "proxy"})
        final_outbound = "direct"
    else:
        final_outbound = "proxy"

    return {
        "log": {"level": "info", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "remote", "address": "1.1.1.1", "detour": "proxy"},
                {"tag": "local", "address": "223.5.5.5", "detour": "direct"},
            ],
            "rules": [{"outbound": "any", "server": "local"}],
            "final": "remote",
            "strategy": "prefer_ipv4",
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "interface_name": "InetFix",
                "inet4_address": "172.19.0.1/30",
                "auto_route": True,
                "strict_route": True,
                "stack": "mixed",
                "sniff": True,
                "sniff_override_destination": True,
            }
        ],
        "outbounds": [
            vless_outbound,
            {"type": "direct", "tag": "direct"},
            {"type": "dns", "tag": "dns-out"},
        ],
        "route": {
            "auto_detect_interface": True,
            "final": final_outbound,
            "rules": route_rules,
        },
    }
