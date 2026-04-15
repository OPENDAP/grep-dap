"""Check accessibility of all directories and find actual files."""
import requests
import re

session = requests.Session()
base = 'https://sst-aqua.gso.uri.edu/opendap'

dirs = ['JAXA_Orbits', 'JAXA_Orbits_OLD', 'RSS_Orbits', 'RSS_Orbits_OLD',
        'RSS_Orbits_REALLY_OLD', 'SST_Orbits', 'gradients_by_period',
        'gradients_by_period_5day', 'iQuamBuoy', 'matchups',
        'matchups_v2', 'matchups_v3']

for d in dirs:
    url = f'{base}/{d}/contents.html'
    try:
        r = session.get(url, timeout=15)
        # Count .nc files
        nc_files = set(re.findall(r'>([^<]+\.nc[4]?)<', r.text))
        subdirs = re.findall(r'href="([^"]+)/contents\.html', r.text)
        subdirs = [s for s in subdirs if '@' not in s and 'mailto' not in s]
        print(f'{d}: status={r.status_code}, subdirs={len(subdirs)}, nc_files={len(nc_files)}')
        if nc_files:
            for f in sorted(nc_files)[:3]:
                print(f'  e.g., {f}')
        if subdirs:
            for s in subdirs[:5]:
                print(f'  subdir: {s}')
    except Exception as e:
        print(f'{d}: ERROR {e}')
    print()
