from __future__ import annotations

import re
import numpy as np
from urllib.parse import quote
from urllib.request import urlopen


URL = (
    "https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/"
    "AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4"
)


def km_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    mean_lat = (lat1 + lat2) / 2.0
    dy = (lat2 - lat1) * 111.32
    dx = (lon2 - lon1) * 111.32 * np.cos(np.radians(mean_lat))
    return float(np.sqrt(dx**2 + dy**2))


def summarize(name: str, values: np.ndarray) -> None:
    if values.size == 0:
        print(f"{name}: no valid samples")
        return
    print(
        f"{name}: mean={values.mean():.3f}, median={np.median(values):.3f}, "
        f"std={values.std():.3f}, min={values.min():.3f}, max={values.max():.3f}, "
        f"N={len(values)}"
    )


def fetch_ascii(var_path: str, row_s: int, row_e: int, col_s: int, col_e: int) -> np.ndarray:
    query = f"{var_path}[{row_s}:{row_e - 1}][{col_s}:{col_e - 1}]"
    encoded = quote(query, safe="/")
    with urlopen(f"{URL}.ascii?{encoded}", timeout=60) as response:
        text = response.read().decode()

    rows = []
    for line in text.splitlines():
        if not line.startswith(var_path + "["):
            continue
        _, values = line.split(",", 1)
        row = [float(token.strip()) for token in values.split(",")]
        rows.append(row)

    array = np.array(rows, dtype=float)
    if array.shape != (row_e - row_s, col_e - col_s):
        raise ValueError(f"unexpected shape for {var_path}: {array.shape}")
    return array


def main() -> int:
    candidates = [
        (8000, 8030, 600, 630),
        (10000, 10030, 600, 630),
        (12000, 12030, 600, 630),
        (14000, 14030, 620, 650),
        (15000, 15030, 670, 700),
        (17000, 17030, 620, 650),
        (19990, 20020, 595, 625),
        (22000, 22030, 620, 650),
        (24000, 24030, 620, 650),
    ]

    patch_data = []
    for row_s, row_e, col_s, col_e in candidates:
        sst = fetch_ascii("/SST_In", row_s, row_e, col_s, col_e) * 0.005
        lat = fetch_ascii("/latitude", row_s, row_e, col_s, col_e) * 0.001
        lon = fetch_ascii("/longitude", row_s, row_e, col_s, col_e) * 0.001
        east = fetch_ascii("/eastward_gradient", row_s, row_e, col_s, col_e) * 0.0001
        north = fetch_ascii("/northward_gradient", row_s, row_e, col_s, col_e) * 0.0001

        valid_grad = (east > -1000) & (north > -1000)
        patch_data.append((row_s, row_e, col_s, col_e, sst, lat, lon, east, north, int(np.sum(valid_grad))))

    usable = [patch for patch in patch_data if patch[-1] > 0]
    if not usable:
        raise RuntimeError("no patch with valid gradients found")

    along = []
    cross = []
    fd_along_ratio = []
    fd_cross_ratio = []
    total_valid_grad = 0
    total_valid_sst = 0

    for row_s, row_e, col_s, col_e, sst, lat, lon, east, north, grad_count in usable:
        print(f"patch=rows[{row_s}:{row_e}) cols[{col_s}:{col_e}) valid_grad={grad_count}")
        valid_sst = sst > -100
        valid_grad = (east > -1000) & (north > -1000)
        valid_ll = lat > -1000
        total_valid_grad += int(np.sum(valid_grad))
        total_valid_sst += int(np.sum(valid_sst))

        n_rows, n_cols = sst.shape

        for c in range(n_cols):
            for r in range(n_rows - 1):
                if valid_ll[r, c] and valid_ll[r + 1, c]:
                    dist = km_distance(lat[r, c], lon[r, c], lat[r + 1, c], lon[r + 1, c])
                    if 0.01 < dist < 10:
                        along.append(dist)
                if (
                    valid_sst[r, c]
                    and valid_sst[r + 1, c]
                    and valid_grad[r, c]
                    and valid_ll[r, c]
                    and valid_ll[r + 1, c]
                ):
                    dist = km_distance(lat[r, c], lon[r, c], lat[r + 1, c], lon[r + 1, c])
                    if dist > 0.1:
                        fd_mag = abs(sst[r + 1, c] - sst[r, c]) / dist
                        stored_mag = float(np.sqrt(east[r, c] ** 2 + north[r, c] ** 2))
                        if stored_mag > 1e-4:
                            fd_along_ratio.append(fd_mag / stored_mag)

        for r in range(n_rows):
            for c in range(n_cols - 1):
                if valid_ll[r, c] and valid_ll[r, c + 1]:
                    dist = km_distance(lat[r, c], lon[r, c], lat[r, c + 1], lon[r, c + 1])
                    if 0.01 < dist < 10:
                        cross.append(dist)
                if (
                    valid_sst[r, c]
                    and valid_sst[r, c + 1]
                    and valid_grad[r, c]
                    and valid_ll[r, c]
                    and valid_ll[r, c + 1]
                ):
                    dist = km_distance(lat[r, c], lon[r, c], lat[r, c + 1], lon[r, c + 1])
                    if dist > 0.1:
                        fd_mag = abs(sst[r, c + 1] - sst[r, c]) / dist
                        stored_mag = float(np.sqrt(east[r, c] ** 2 + north[r, c] ** 2))
                        if stored_mag > 1e-4:
                            fd_cross_ratio.append(fd_mag / stored_mag)

    print(f"total_valid_sst={total_valid_sst} total_valid_grad={total_valid_grad}")

    along = np.array(along)
    cross = np.array(cross)
    fd_along_ratio = np.array(fd_along_ratio)
    fd_cross_ratio = np.array(fd_cross_ratio)

    summarize("along_track_spacing_km", along)
    summarize("cross_track_spacing_km", cross)
    summarize("fd_along_to_stored_ratio", fd_along_ratio)
    summarize("fd_cross_to_stored_ratio", fd_cross_ratio)

    print("interpretation:")
    print("  ratio ~ 1.0 -> 1-pixel gradient stencil")
    print("  ratio ~ 0.5 -> 2-pixel gradient stencil")
    print("  ratio ~ 0.33 -> 3-pixel gradient stencil")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
