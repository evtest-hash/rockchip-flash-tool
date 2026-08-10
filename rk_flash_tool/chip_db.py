from __future__ import annotations

from pathlib import Path

# Chip model -> the bootloader shipped for it in vendor/rkbin/. These are exact
# filenames: when a loader is updated there, update it here too.
_LOADERS: dict[str, str] = {
    "RK3588": "rk3588_spl_loader_v1.19.113.bin",
    "RK3576": "rk3576_spl_loader_v1.09.108.bin",
    "RK3568": "rk356x_spl_loader_v1.23.114.bin",
    "RK3562": "rk3562_spl_loader_v1.07.107.bin",
    "RK3506": "rk3506_spl_loader_v1.06.111.bin",
    "RK3399": "rk3399_loader_v1.30.130.bin",
    "RK3368": "rk3368_loader_v2.06.268.bin",
    "RK3366": "rk3366_loader_v1.00.102.bin",
    "RK3328": "rk3328_loader_v1.21.250.bin",
    "RK3326": "rk3326_loader_v2.11.140.bin",
    "RK3288": "rk3288_loader_v1.12.263.bin",
    "RK3229": "rk322x_loader_v1.10.256.bin",
    "RK3188": "rk3188_loader_v2.00.200.bin",
    "RK3128": "rk3128_loader_v2.12.263.bin",
    "RK3126": "rk3126_loader_v2.09.263.bin",
    "RK3036": "rk3036_loader_v1.11.257.bin",
    "RK1808": "rk1808_loader_v1.06.109.bin",
    "RV1126": "rv1126_spl_loader_v1.14.110.bin",
    "RV1109": "rv110x_loader_v1.12.126.bin",
}


def find_loader(model: str, search_dir: Path) -> Path | None:
    name = _LOADERS.get(model)
    if not name:
        return None
    loader = search_dir / name
    return loader if loader.exists() else None
