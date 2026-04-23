"""Explore gradients_by_period files from URI OPeNDAP server."""
from pydap.client import open_url
import numpy as np

# Open a gradients_by_period file
url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

print('=== Dataset keys ===')
keys = list(ds.keys())
print(f'{len(keys)} variables:')
for k in keys:
    print(f'  {k}')
print()

print('=== Dataset attributes ===')
for k, v in ds.attributes.items():
    vstr = str(v)
    if len(vstr) > 300:
        vstr = vstr[:300] + '...'
    print(f'  {k}: {vstr}')
print()

# Examine all variables
for vname in keys:
    v = ds[vname]
    print(f'--- {vname} ---')
    print(f'  shape: {v.shape}, dtype: {v.dtype}')
    for ak, av in v.attributes.items():
        avstr = str(av)
        if len(avstr) > 150:
            avstr = avstr[:150] + '...'
        print(f'  {ak}: {avstr}')
    print()
