from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydap.client import open_url


BASE_URL = "https://sst-aqua.gso.uri.edu/opendap/"
TOP_LEVEL_COLLECTIONS = [
    "JAXA_Orbits",
    "JAXA_Orbits_OLD",
    "RSS_Orbits",
    "RSS_Orbits_OLD",
    "RSS_Orbits_REALLY_OLD",
    "SST_Orbits",
    "gradients_by_period",
    "gradients_by_period_5day",
    "iQuamBuoy",
    "matchups",
    "matchups_v2",
    "matchups_v3",
    "timeSeries",
    "timeSeries_10km",
    "timeSeries_10km_old",
]
ORBIT_DATASET = (
    "SST_Orbits/2024/01/"
    "AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4"
)
GRADIENT_DATASET = "gradients_by_period/augmented_monthly_stats_01_2024.nc"


@dataclass
class FetchResult:
    url: str
    status: int
    text: str


def fetch_text(url: str) -> FetchResult:
    request = Request(url, headers={"User-Agent": "grep-dap exploratory probe"})
    try:
        with urlopen(request, timeout=60) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            text = response.read().decode(charset, errors="replace")
            return FetchResult(url=url, status=response.status, text=text)
    except HTTPError as err:
        charset = err.headers.get_content_charset() or "utf-8"
        text = err.read().decode(charset, errors="replace")
        return FetchResult(url=url, status=err.code, text=text)
    except URLError as err:
        return FetchResult(url=url, status=-1, text=str(err))


def parse_catalog_refs(catalog_text: str) -> list[str]:
    ns = {"thredds": "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"}
    root = ET.fromstring(catalog_text)
    refs = []
    for element in root.findall(".//thredds:catalogRef", ns):
        name = element.attrib.get("name")
        if name:
            refs.append(name)
    return refs


def summarize_orbit_das(das_text: str) -> dict[str, str]:
    patterns = {
        "title": r'String title "([^"]+)"',
        "summary": r'String Summary "([^"]+)"',
        "creator_name": r'String creator_name "([^"]+)"',
        "project": r'String project "([^"]+)"',
        "cdm_data_type": r'String cdm_data_type "([^"]+)"',
    }
    values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, das_text)
        values[key] = match.group(1) if match else ""
    return values


def extract_dataset_names(catalog_text: str, limit: int = 8) -> list[str]:
    names = re.findall(r'<thredds:dataset name="([^"]+)"', catalog_text)
    cleaned = [name for name in names if "/" not in name]
    return cleaned[:limit]


def sample_orbit_data(dataset_url: str) -> dict[str, object]:
    dataset = open_url(dataset_url)

    datetime_value = float(dataset["DateTime"][:].data)
    time_from_start = [float(value) for value in dataset["time_from_start_orbit"][0:5].data]

    latitude = dataset["latitude"][0:3, 0:5].data.tolist()
    longitude = dataset["longitude"][0:3, 0:5].data.tolist()
    sst_in = dataset["SST_In"][0:3, 0:5].data.tolist()
    qual_sst = dataset["qual_sst"][0:3, 0:5].data.tolist()

    granule_names = dataset["contributing_granules"]["filenames"][0:5, 0:2].data.tolist()

    return {
        "DateTime_raw": datetime_value,
        "time_from_start_orbit_raw": time_from_start,
        "latitude_raw": latitude,
        "longitude_raw": longitude,
        "SST_In_raw": sst_in,
        "qual_sst_raw": qual_sst,
        "contributing_granules_sample": granule_names,
    }


def sample_gradient_data(dataset_url: str) -> dict[str, object]:
    dataset = open_url(dataset_url)
    sample = {
        "day_pixel_count": dataset["day_pixel_count"][0:3, 0:5].data.tolist(),
        "night_pixel_count": dataset["night_pixel_count"][0:3, 0:5].data.tolist(),
        "day_sum_SST": dataset["day_sum_SST"][0:3, 0:5].data.tolist(),
        "day_sum_magnitude_gradient": dataset["day_sum_magnitude_gradient"][0:3, 0:5].data.tolist(),
    }
    return sample


def fetch_ascii(dataset_path: str, variables: list[str]) -> FetchResult:
    expression = ",".join(variables)
    encoded = quote(expression, safe=",/")
    return fetch_text(f"{BASE_URL}{dataset_path}.ascii?{encoded}")


def print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def main() -> int:
    root_catalog = fetch_text(f"{BASE_URL}catalog.xml")
    if root_catalog.status != 200:
        print(f"Root catalog fetch failed with status {root_catalog.status}", file=sys.stderr)
        return 1

    top_level_refs = parse_catalog_refs(root_catalog.text)
    print_lines(
        [
            "URI root catalog references:",
            *[f"  - {name}" for name in top_level_refs],
            "",
        ]
    )

    print("Top-level collection access status:")
    for collection in TOP_LEVEL_COLLECTIONS:
        result = fetch_text(f"{BASE_URL}{collection}/catalog.xml")
        print(f"  - {collection}: {result.status}")
    print("")

    orbit_dds = fetch_text(f"{BASE_URL}{ORBIT_DATASET}.dds")
    orbit_das = fetch_text(f"{BASE_URL}{ORBIT_DATASET}.das")
    orbit_meta = summarize_orbit_das(orbit_das.text)
    print("Representative orbit dataset:")
    print(f"  - path: {ORBIT_DATASET}")
    print(f"  - dds status: {orbit_dds.status}")
    print(f"  - das status: {orbit_das.status}")
    for key, value in orbit_meta.items():
        print(f"  - {key}: {value}")
    print("")

    gradient_catalog = fetch_text(f"{BASE_URL}gradients_by_period/catalog.xml")
    gradient_names = extract_dataset_names(gradient_catalog.text, limit=10)
    print("Representative gradient catalog entries:")
    for name in gradient_names:
        print(f"  - {name}")
    print("")

    gradient_dds = fetch_text(f"{BASE_URL}{GRADIENT_DATASET}.dds")
    gradient_das = fetch_text(f"{BASE_URL}{GRADIENT_DATASET}.das")
    print("Representative gradient dataset:")
    print(f"  - path: {GRADIENT_DATASET}")
    print(f"  - dds status: {gradient_dds.status}")
    print(f"  - das status: {gradient_das.status}")
    print("")

    print("Sampling orbit dataset...")
    try:
        orbit_sample = sample_orbit_data(f"{BASE_URL}{ORBIT_DATASET}")
        for key, value in orbit_sample.items():
            print(f"  - {key}: {value}")
    except Exception as err:  # noqa: BLE001
        print(f"  - pydap sampling failed: {err}")
        orbit_ascii = fetch_ascii(
            ORBIT_DATASET,
            [
                "/DateTime",
                "/latitude[0:2][0:4]",
                "/longitude[0:2][0:4]",
                "/SST_In[0:2][0:4]",
                "/qual_sst[0:2][0:4]",
                "/time_from_start_orbit[0:4]",
            ],
        )
        print(f"  - ascii fallback status: {orbit_ascii.status}")
        print(orbit_ascii.text)
    print("")

    print("Sampling gradient dataset...")
    try:
        gradient_sample = sample_gradient_data(f"{BASE_URL}{GRADIENT_DATASET}")
        for key, value in gradient_sample.items():
            print(f"  - {key}: {value}")
    except Exception as err:  # noqa: BLE001
        print(f"  - pydap sampling failed: {err}")
        gradient_ascii = fetch_ascii(
            GRADIENT_DATASET,
            [
                "day_pixel_count[150:152][80:84]",
                "night_pixel_count[150:152][80:84]",
                "day_sum_SST[150:152][80:84]",
                "day_sum_magnitude_gradient[150:152][80:84]",
            ],
        )
        print(f"  - ascii fallback status: {gradient_ascii.status}")
        print(gradient_ascii.text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
