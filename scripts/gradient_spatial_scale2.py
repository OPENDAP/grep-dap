"""Estimate gradient spatial scale using orbit-level data."""
from pydap.client import open_url
import numpy as np

url_orbit = 'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4'
ds = open_url(url_orbit, protocol='dap2')

# We know rows ~20000, cols ~600 had data from earlier sampling
# Let's get a bigger patch there
row_s, row_e = 19990, 20020
col_s, col_e = 595, 625

sst = np.array(ds['/SST_In'][row_s:row_e, col_s:col_e].data) * 0.005
lat = np.array(ds['/latitude'][row_s:row_e, col_s:col_e].data) * 0.001
lon = np.array(ds['/longitude'][row_s:row_e, col_s:col_e].data) * 0.001
east = np.array(ds['/eastward_gradient'][row_s:row_e, col_s:col_e].data) * 0.0001
north = np.array(ds['/northward_gradient'][row_s:row_e, col_s:col_e].data) * 0.0001

# Also get the regridded versions
rsst = np.array(ds['/regridded_sst'][row_s:row_e, col_s:col_e].data) * 0.005
rlat = np.array(ds['/regridded_latitude'][row_s:row_e, col_s:col_e].data) * 0.001
rlon = np.array(ds['/regridded_longitude'][row_s:row_e, col_s:col_e].data) * 0.001

# Fill values (after scaling)
fill_sst = -32767 * 0.005  # -163.835
fill_grad = -2147483647 * 0.0001  # -214748.3647
fill_ll = -2147483647 * 0.001  # -2147483.647

v_sst = sst > -100
v_grad = (east > -1000) & (north > -1000)
v_ll = lat > -1000
v_rsst = rsst > -100
v_rll = rlat > -1000

print(f'Valid SST: {np.sum(v_sst)} of {sst.size}')
print(f'Valid gradients: {np.sum(v_grad)} of {east.size}')
print(f'Valid lat/lon: {np.sum(v_ll)} of {lat.size}')
print(f'Valid regridded SST: {np.sum(v_rsst)} of {rsst.size}')
print(f'Valid regridded lat/lon: {np.sum(v_rll)} of {rlat.size}')

if np.sum(v_sst) > 0:
    print(f'\nSST range: {sst[v_sst].min():.2f} to {sst[v_sst].max():.2f} C')
    print(f'Lat range: {lat[v_ll].min():.2f} to {lat[v_ll].max():.2f}')
    print(f'Lon range: {lon[v_ll].min():.2f} to {lon[v_ll].max():.2f}')

print()
print('='*60)
print('Along-track pixel spacing')
print('='*60)
# Measure pixel spacing along the track (row direction)
spacings_along = []
for ci in range(col_e - col_s):
    for ri in range(row_e - row_s - 1):
        if v_ll[ri, ci] and v_ll[ri+1, ci]:
            dlat = lat[ri+1, ci] - lat[ri, ci]
            dlon = lon[ri+1, ci] - lon[ri, ci]
            mean_lat_r = (lat[ri, ci] + lat[ri+1, ci]) / 2
            dy = dlat * 111.32
            dx = dlon * 111.32 * np.cos(np.radians(mean_lat_r))
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0.01 and dist < 10:
                spacings_along.append(dist)

if spacings_along:
    sa = np.array(spacings_along)
    print(f'Along-track spacing: mean={sa.mean():.3f} km, median={np.median(sa):.3f} km')
    print(f'  std={sa.std():.3f} km, min={sa.min():.3f} km, max={sa.max():.3f} km')
    print(f'  N samples: {len(sa)}')

print()
print('='*60)
print('Cross-track pixel spacing')
print('='*60)
spacings_cross = []
for ri in range(row_e - row_s):
    for ci in range(col_e - col_s - 1):
        if v_ll[ri, ci] and v_ll[ri, ci+1]:
            dlat = lat[ri, ci+1] - lat[ri, ci]
            dlon = lon[ri, ci+1] - lon[ri, ci]
            mean_lat_r = (lat[ri, ci] + lat[ri, ci+1]) / 2
            dy = dlat * 111.32
            dx = dlon * 111.32 * np.cos(np.radians(mean_lat_r))
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0.01 and dist < 10:
                spacings_cross.append(dist)

if spacings_cross:
    sc = np.array(spacings_cross)
    print(f'Cross-track spacing: mean={sc.mean():.3f} km, median={np.median(sc):.3f} km')
    print(f'  std={sc.std():.3f} km, min={sc.min():.3f} km, max={sc.max():.3f} km')
    print(f'  N samples: {len(sc)}')

print()
print('='*60)
print('Regridded pixel spacing')
print('='*60)
# Check if regridded data has different spacing
spacings_reg_along = []
for ci in range(col_e - col_s):
    for ri in range(row_e - row_s - 1):
        if v_rll[ri, ci] and v_rll[ri+1, ci]:
            dlat = rlat[ri+1, ci] - rlat[ri, ci]
            dlon = rlon[ri+1, ci] - rlon[ri, ci]
            mean_lat_r = (rlat[ri, ci] + rlat[ri+1, ci]) / 2
            dy = dlat * 111.32
            dx = dlon * 111.32 * np.cos(np.radians(mean_lat_r))
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0.001 and dist < 10:
                spacings_reg_along.append(dist)

if spacings_reg_along:
    sra = np.array(spacings_reg_along)
    print(f'Regridded along-track: mean={sra.mean():.3f} km, median={np.median(sra):.3f} km')
    print(f'  std={sra.std():.3f} km, min={sra.min():.3f} km, max={sra.max():.3f} km')
    print(f'  N samples: {len(sra)}')

# Now check if stored gradient matches finite difference
print()
print('='*60)
print('Gradient verification: stored vs finite difference')
print('='*60)

# Check along-track finite difference
count = 0
diffs_ratio = []
for ci in range(5, col_e - col_s - 5):
    for ri in range(row_e - row_s - 1):
        if (v_sst[ri, ci] and v_sst[ri+1, ci] and
            v_grad[ri, ci] and v_ll[ri, ci] and v_ll[ri+1, ci]):
            s1 = sst[ri, ci]
            s2 = sst[ri+1, ci]
            dlat = lat[ri+1, ci] - lat[ri, ci]
            dlon = lon[ri+1, ci] - lon[ri, ci]
            mean_lat_r = (lat[ri, ci] + lat[ri+1, ci]) / 2
            dy = dlat * 111.32
            dx = dlon * 111.32 * np.cos(np.radians(mean_lat_r))
            dist = np.sqrt(dx**2 + dy**2)

            if dist > 0.1:
                dsst = s2 - s1
                fd_mag = abs(dsst) / dist
                stored_mag = np.sqrt(east[ri, ci]**2 + north[ri, ci]**2)
                if stored_mag > 0.0001:
                    diffs_ratio.append(fd_mag / stored_mag)
                    if count < 8:
                        print(f'  [{ri},{ci}]: SST={s1:.2f}->{s2:.2f}, dist={dist:.2f}km')
                        print(f'    along-track FD: |dSST/ds|={fd_mag:.4f} C/km')
                        print(f'    stored |grad|={stored_mag:.4f} C/km')
                        print(f'    ratio FD/stored={fd_mag/stored_mag:.3f}')
                    count += 1

if diffs_ratio:
    dr = np.array(diffs_ratio)
    print(f'\n  N comparisons: {len(dr)}')
    print(f'  FD/stored ratio: mean={dr.mean():.3f}, median={np.median(dr):.3f}')
    print(f'  std={dr.std():.3f}')
    print()
    print('  If ratio ≈ 1: gradient computed over 1-pixel spacing (~1 km)')
    print('  If ratio ≈ 0.5: gradient computed over 2-pixel spacing (~2 km)')
    print('  If ratio ≈ 0.33: gradient computed over 3-pixel spacing (~3 km)')

# Also try cross-track finite difference vs stored gradient
print()
print('Cross-track finite difference vs stored gradient:')
count2 = 0
diffs_ratio2 = []
for ri in range(5, row_e - row_s - 5):
    for ci in range(col_e - col_s - 1):
        if (v_sst[ri, ci] and v_sst[ri, ci+1] and
            v_grad[ri, ci] and v_ll[ri, ci] and v_ll[ri, ci+1]):
            s1 = sst[ri, ci]
            s2 = sst[ri, ci+1]
            dlat = lat[ri, ci+1] - lat[ri, ci]
            dlon = lon[ri, ci+1] - lon[ri, ci]
            mean_lat_r = (lat[ri, ci] + lat[ri, ci+1]) / 2
            dy = dlat * 111.32
            dx = dlon * 111.32 * np.cos(np.radians(mean_lat_r))
            dist = np.sqrt(dx**2 + dy**2)

            if dist > 0.1:
                dsst = s2 - s1
                fd_mag = abs(dsst) / dist
                stored_mag = np.sqrt(east[ri, ci]**2 + north[ri, ci]**2)
                if stored_mag > 0.0001:
                    diffs_ratio2.append(fd_mag / stored_mag)
                    if count2 < 5:
                        print(f'  [{ri},{ci}]: dist={dist:.2f}km, FD={fd_mag:.4f}, stored={stored_mag:.4f}')
                    count2 += 1

if diffs_ratio2:
    dr2 = np.array(diffs_ratio2)
    print(f'\n  N comparisons: {len(dr2)}')
    print(f'  FD/stored ratio: mean={dr2.mean():.3f}, median={np.median(dr2):.3f}')
