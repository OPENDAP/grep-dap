"""Explore SST orbit file metadata and data from URI OPeNDAP server."""
from pydap.client import open_url
import numpy as np

# Open an SST orbit file with DAP2
url = 'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4'
ds = open_url(url, protocol='dap2')

# Full H5_GLOBAL attributes
h5g = ds.attributes.get('H5_GLOBAL', {})
print('=== H5_GLOBAL attributes ===')
for k, v in h5g.items():
    vstr = str(v)
    if len(vstr) > 300:
        vstr = vstr[:300] + '...'
    print(f'  {k}: {vstr}')
print()

# Remaining key variables
remaining_vars = ['/refined_mask', '/qual_sst', '/nadir_latitude',
                  '/nadir_longitude', '/DateTime', '/time_from_start_orbit',
                  '/i', '/nx']
for vname in remaining_vars:
    if vname in ds.keys():
        v = ds[vname]
        print(f'--- {vname} ---')
        print(f'  shape: {v.shape}, dtype: {v.dtype}')
        for ak, av in v.attributes.items():
            avstr = str(av)
            if len(avstr) > 100:
                avstr = avstr[:100] + '...'
            print(f'  {ak}: {avstr}')
        print()

# Sample some actual data
print('=== Sampling SST data ===')
sst = ds['/SST_In']
# Get a small subset from middle of orbit
subset = sst[20000:20010, 600:610]
data = np.array(subset.data)
# Apply scale_factor
data_scaled = data * 0.005
print(f'SST subset (10x10, scaled to C):')
print(f'  min: {np.min(data_scaled[data_scaled > -100]):.2f}')
print(f'  max: {np.max(data_scaled[data_scaled > -100]):.2f}')
print(f'  mean (valid): {np.mean(data_scaled[data_scaled > -100]):.2f}')
print()

# Sample lat/lon
lat = ds['/latitude']
lon = ds['/longitude']
lat_sub = np.array(lat[20000:20010, 600:610].data) * 0.001
lon_sub = np.array(lon[20000:20010, 600:610].data) * 0.001
print(f'Lat range: {np.min(lat_sub[lat_sub > -900]):.2f} to {np.max(lat_sub[lat_sub > -900]):.2f}')
print(f'Lon range: {np.min(lon_sub[lon_sub > -900]):.2f} to {np.max(lon_sub[lon_sub > -900]):.2f}')
print()

# Nadir track
nadir_lat = ds['/nadir_latitude']
nadir_lon = ds['/nadir_longitude']
nl = np.array(nadir_lat[0:100].data)
print(f'Nadir lat (first 100): {np.min(nl[nl > -900]):.2f} to {np.max(nl[nl > -900]):.2f}')
nlo = np.array(nadir_lon[0:100].data)
print(f'Nadir lon (first 100): {np.min(nlo[nlo > -900]):.2f} to {np.max(nlo[nlo > -900]):.2f}')

# Regrid_to_L2eqa variables
print()
print('=== Regrid_to_L2eqa group variables ===')
regrid_vars = [k for k in ds.keys() if 'Regrid_to_L2eqa' in k]
for vname in regrid_vars:
    v = ds[vname]
    print(f'  {vname}: shape={v.shape}, dtype={v.dtype}')
    if 'long_name' in v.attributes:
        print(f'    long_name: {v.attributes["long_name"]}')
    if 'units' in v.attributes:
        print(f'    units: {v.attributes["units"]}')
