"""Compare metadata across different files and years on URI server."""
from pydap.client import open_url
import requests
import re
import numpy as np

session = requests.Session()

# 1. Look at an early SST orbit file (2002)
print('='*60)
print('=== SST_Orbits: early file (2002) ===')
r = session.get('https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2002/07/contents.html', timeout=15)
hrefs = re.findall(r'href="([^"]+\.nc4\.dds)"', r.text)
if hrefs:
    # Get the base filename from first .dds href
    fname = hrefs[0].replace('.dds', '')
    print(f'First file: {fname}')
    url = f'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2002/07/{fname}'
    ds = open_url(url, protocol='dap2')
    print(f'Keys ({len(list(ds.keys()))}): {list(ds.keys())[:10]}...')
    h5g = ds.attributes.get('H5_GLOBAL', {})
    print(f'title: {h5g.get("title", "NONE")}')
    print(f'Conventions: {h5g.get("Conventions", "NONE")}')
    print(f'creator: {h5g.get("creator_name", "NONE")}')
    # Check SST_In attrs
    if '/SST_In' in ds.keys():
        sst = ds['/SST_In']
        print(f'SST_In shape: {sst.shape}')
        print(f'SST_In attributes: {sst.attributes}')
else:
    print('No .nc4 files found in 2002/07')
    # Try listing months
    r2 = session.get('https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2002/contents.html', timeout=15)
    months = re.findall(r'href="(\d+)/contents\.html', r2.text)
    print(f'Available months: {months}')
    if months:
        r3 = session.get(f'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2002/{months[0]}/contents.html', timeout=15)
        hrefs3 = re.findall(r'href="([^"]+\.nc4\.dds)"', r3.text)
        if hrefs3:
            fname = hrefs3[0].replace('.dds', '')
            print(f'First file in month {months[0]}: {fname}')

# 2. Examine gradients file naming pattern
print()
print('='*60)
print('=== gradients_by_period: file naming analysis ===')
r = session.get('https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/contents.html', timeout=15)
nc_files = sorted(set(re.findall(r'>([^<]+\.nc)<', r.text)))
print(f'Total unique files: {len(nc_files)}')
# Parse naming pattern
months = set()
years = set()
for f in nc_files:
    m = re.match(r'augmented_monthly_stats_(\d+)_(\d+)\.nc', f)
    if m:
        months.add(int(m.group(1)))
        years.add(int(m.group(2)))
print(f'Months: {sorted(months)}')
print(f'Years: {sorted(years)}')
print(f'Expected files: {len(months)} months x {len(years)} years = {len(months)*len(years)}')
print()

# 3. Compare an early vs late gradients file
print('='*60)
print('=== gradients_by_period: early (2003) vs late (2024) ===')
for year in [2003, 2024]:
    url = f'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_06_{year}.nc'
    ds = open_url(url, protocol='dap2')
    keys = list(ds.keys())
    print(f'Year {year}: {len(keys)} variables, attrs: {ds.attributes}')
    # Check if any vars have attributes
    has_attrs = sum(1 for k in keys if ds[k].attributes)
    print(f'  Variables with attributes: {has_attrs}/{len(keys)}')
    # Sample data
    day_count = np.array(ds['day_pixel_count'][:,:].data)
    print(f'  day_pixel_count: non-zero={np.sum(day_count>0)}, max={np.nanmax(day_count)}')
print()

# 4. SST orbit file naming pattern analysis
print('='*60)
print('=== SST_Orbits file naming analysis ===')
r = session.get('https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/contents.html', timeout=15)
hrefs = re.findall(r'href="([^"]+\.nc4\.dds)"', r.text)
fnames = [h.replace('.dds', '') for h in hrefs]
print(f'Files in 2024/01: {len(fnames)}')
if fnames:
    print(f'First: {fnames[0]}')
    print(f'Last: {fnames[-1]}')
    # Parse pattern
    m = re.match(r'AQUA_MODIS_orbit_(\d+)_(\d{8}T\d{6})_L2_SST-URI_(.+)\.nc4', fnames[0])
    if m:
        print(f'  Orbit number: {m.group(1)}')
        print(f'  DateTime: {m.group(2)}')
        print(f'  Version: {m.group(3)}')
    # Count orbits per day
    dates = {}
    for f in fnames:
        m = re.match(r'AQUA_MODIS_orbit_\d+_(\d{8})', f)
        if m:
            d = m.group(1)
            dates[d] = dates.get(d, 0) + 1
    print(f'  Unique dates: {len(dates)}')
    print(f'  Orbits per day: min={min(dates.values())}, max={max(dates.values())}, mean={np.mean(list(dates.values())):.1f}')
