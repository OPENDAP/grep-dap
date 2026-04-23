"""Estimate the spatial range over which gradients were calculated."""
from pydap.client import open_url
import numpy as np

print('='*60)
print('PART 1: Pixel count ratios and what they imply')
print('='*60)

url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

day_count = np.array(ds['day_pixel_count'][:,:].data)
day_as_count = np.array(ds['day_as_pixel_count'][:,:].data)
day_at_count = np.array(ds['day_at_pixel_count'][:,:].data)

# Only look at cells with data
mask = day_count > 100  # exclude noisy low-count cells
ratio_as = day_as_count[mask] / day_count[mask]
ratio_at = day_at_count[mask] / day_count[mask]

print(f'day_as/day ratio: mean={ratio_as.mean():.4f}, median={np.median(ratio_as):.4f}')
print(f'day_at/day ratio: mean={ratio_at.mean():.4f}, median={np.median(ratio_at):.4f}')
print()

# If gradient uses forward difference (pixel i and i+1):
#   P(both valid) ≈ p for consecutive pixels on same scanline
#   So as_count/sst_count ≈ (N-1)/N where N = pixels per scanline in cell
# If gradient uses central difference (pixel i-1 and i+1):
#   P(both valid) ≈ p² where p = valid fraction
#   So ratio would be lower

# Along a 1-degree cell at equator: ~111 km / 1 km = ~111 pixels along track
# Forward diff: (111-1)/111 = 0.991 -- too high for the observed 0.67
# This means cloud masking is the dominant factor, not edge effects

# Actually, the ratio depends on whether BOTH neighbors must be valid
# For forward diff on orbit: need pixel(i) AND pixel(i+1) both valid
# If valid fraction per pixel = p, and independence:
#   P(pair valid) = p * p_neighbor ≈ p^2 (if independent)
# But adjacent pixels are highly correlated (cloud patches are spatial)
# So P(pair valid) is higher than p^2

# Let me check: what fraction of SST pixels also have a neighbor?
# ratio_as ≈ 0.67 means 2/3 of SST pixels have a valid along-swath neighbor
# ratio_at ≈ 0.33 means 1/3 have a valid across-track neighbor

print('Interpretation:')
print('  If along-swath gradient = diff between adjacent along-track pixels:')
print('  ratio_as ≈ 0.67 means 2/3 of SST pixels have a valid')
print('  along-track neighbor (reasonable given cloud masking)')
print()
print('  ratio_at ≈ 0.33 means only 1/3 of SST pixels have a valid')
print('  across-track neighbor. This is consistent with MODIS geometry:')
print('  across-track pixel spacing varies from 1 km (nadir) to')
print('  ~5-6 km (swath edge), and the bowtie effect causes overlap.')
print('  Also, cross-track neighbors may be more often on different')
print('  scanlines, increasing the chance of cloud gaps.')

print()
print('='*60)
print('PART 2: SST_Orbits gradient metadata -- what does it say?')
print('='*60)

url_orbit = 'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4'
ds_orbit = open_url(url_orbit, protocol='dap2')

# Check gradient attributes
for vname in ['/eastward_gradient', '/northward_gradient']:
    v = ds_orbit[vname]
    print(f'\n{vname}:')
    for ak, av in v.attributes.items():
        print(f'  {ak}: {av}')

# Check regridded variables for clues about pixel spacing
for vname in ['/regridded_sst', '/regridded_latitude', '/regridded_longitude']:
    v = ds_orbit[vname]
    print(f'\n{vname}:')
    for ak, av in v.attributes.items():
        avstr = str(av)
        if len(avstr) > 100:
            avstr = avstr[:100] + '...'
        print(f'  {ak}: {avstr}')

print()
print('='*60)
print('PART 3: Sample orbit-level gradients at known locations')
print('='*60)

# Get a small region of the orbit data to check gradient magnitudes
# Sample from mid-orbit where we have good data
sst = ds_orbit['/SST_In']
lat = ds_orbit['/latitude']
lon = ds_orbit['/longitude']
east_grad = ds_orbit['/eastward_gradient']
north_grad = ds_orbit['/northward_gradient']

# Get a small patch
row_start, row_end = 15000, 15020
col_start, col_end = 670, 690

sst_patch = np.array(sst[row_start:row_end, col_start:col_end].data) * 0.005
lat_patch = np.array(lat[row_start:row_end, col_start:col_end].data) * 0.001
lon_patch = np.array(lon[row_start:row_end, col_start:col_end].data) * 0.001
east_patch = np.array(east_grad[row_start:row_end, col_start:col_end].data) * 0.0001
north_patch = np.array(north_grad[row_start:row_end, col_start:col_end].data) * 0.0001

# Filter valid data
fill_sst = -32767 * 0.005
fill_grad = -2147483647 * 0.0001
fill_latlon = -2147483647 * 0.001

valid = (sst_patch > fill_sst + 1) & (east_patch > fill_grad + 1) & (lat_patch > fill_latlon + 1)
print(f'Valid pixels in patch: {np.sum(valid)} of {valid.size}')

if np.sum(valid) > 0:
    print(f'SST range: {sst_patch[valid].min():.2f} to {sst_patch[valid].max():.2f} C')
    print(f'Lat range: {lat_patch[valid].min():.2f} to {lat_patch[valid].max():.2f}')
    print(f'Lon range: {lon_patch[valid].min():.2f} to {lon_patch[valid].max():.2f}')
    print(f'Eastward gradient range: {east_patch[valid].min():.4f} to {east_patch[valid].max():.4f} C/km')
    print(f'Northward gradient range: {north_patch[valid].min():.4f} to {north_patch[valid].max():.4f} C/km')

    # Estimate pixel spacing from lat/lon differences
    # Along-track (row direction): diff between consecutive rows at same column
    for col in range(col_start, min(col_start+3, col_end)):
        ci = col - col_start
        dlat = np.diff(lat_patch[:, ci])
        dlon = np.diff(lon_patch[:, ci])
        v = (lat_patch[:-1, ci] > fill_latlon + 1) & (lat_patch[1:, ci] > fill_latlon + 1)
        if np.sum(v) > 0:
            # Approximate distance in km
            mean_lat = np.mean(lat_patch[v, ci])
            dx = dlon[v] * 111.32 * np.cos(np.radians(mean_lat))
            dy = dlat[v] * 111.32
            dist = np.sqrt(dx**2 + dy**2)
            print(f'\n  Along-track pixel spacing (col {col}):')
            print(f'    mean: {dist.mean():.3f} km, std: {dist.std():.3f} km')

    # Cross-track (column direction): diff between consecutive columns at same row
    for row in range(row_start, min(row_start+3, row_end)):
        ri = row - row_start
        dlat = np.diff(lat_patch[ri, :])
        dlon = np.diff(lon_patch[ri, :])
        v = (lat_patch[ri, :-1] > fill_latlon + 1) & (lat_patch[ri, 1:] > fill_latlon + 1)
        if np.sum(v) > 0:
            mean_lat = np.mean(lat_patch[ri, v])
            dx = dlon[v] * 111.32 * np.cos(np.radians(mean_lat))
            dy = dlat[v] * 111.32
            dist = np.sqrt(dx**2 + dy**2)
            print(f'\n  Cross-track pixel spacing (row {row}):')
            print(f'    mean: {dist.mean():.3f} km, std: {dist.std():.3f} km')

    # Now check: can we verify that the stored gradient matches
    # a finite difference over 1 pixel?
    # eastward_gradient at pixel (i,j) should be ≈ dSST/dx
    # If computed as (SST[i,j+1] - SST[i,j]) / distance:
    print('\n  Checking if gradient ≈ finite difference over 1 pixel:')
    for ri in range(min(5, row_end - row_start)):
        for ci in range(min(5, col_end - col_start - 1)):
            s1 = sst_patch[ri, ci]
            s2 = sst_patch[ri, ci+1]
            eg = east_patch[ri, ci]
            ng = north_patch[ri, ci]

            if s1 > fill_sst + 1 and s2 > fill_sst + 1 and eg > fill_grad + 1:
                lat1 = lat_patch[ri, ci]
                lon1 = lon_patch[ri, ci]
                lat2 = lat_patch[ri, ci+1]
                lon2 = lon_patch[ri, ci+1]
                if lat1 > fill_latlon + 1 and lat2 > fill_latlon + 1:
                    dx = (lon2 - lon1) * 111.32 * np.cos(np.radians((lat1+lat2)/2))
                    dy = (lat2 - lat1) * 111.32
                    dist = np.sqrt(dx**2 + dy**2)
                    dsst = s2 - s1
                    if dist > 0.01:
                        fd_east = dsst * dx / (dist * dist) if dist > 0 else 0
                        fd_north = dsst * dy / (dist * dist) if dist > 0 else 0
                        print(f'    [{ri},{ci}]: SST diff={dsst:.4f}, dist={dist:.3f}km')
                        print(f'      stored: east={eg:.4f}, north={ng:.4f}')
                        print(f'      cross-track FD: east≈{dsst/dist * dx/dist:.4f}, north≈{dsst/dist * dy/dist:.4f}')
                        break
        else:
            continue
        break

print()
print('='*60)
print('PART 4: Compare along-track gradients')
print('='*60)

# Along-track finite difference
for ri in range(min(10, row_end - row_start - 1)):
    ci = 10  # pick a column near center
    s1 = sst_patch[ri, ci]
    s2 = sst_patch[ri+1, ci]
    eg = east_patch[ri, ci]
    ng = north_patch[ri, ci]

    if s1 > fill_sst + 1 and s2 > fill_sst + 1 and eg > fill_grad + 1:
        lat1 = lat_patch[ri, ci]
        lon1 = lon_patch[ri, ci]
        lat2 = lat_patch[ri+1, ci]
        lon2 = lon_patch[ri+1, ci]
        if lat1 > fill_latlon + 1 and lat2 > fill_latlon + 1:
            dx = (lon2 - lon1) * 111.32 * np.cos(np.radians((lat1+lat2)/2))
            dy = (lat2 - lat1) * 111.32
            dist = np.sqrt(dx**2 + dy**2)
            dsst = s2 - s1
            if dist > 0.01:
                print(f'  [{ri},{ci}]: SST diff={dsst:.4f}C, dist={dist:.3f}km')
                print(f'    stored gradient: east={eg:.4f}, north={ng:.4f} C/km')
                print(f'    mag={np.sqrt(eg**2+ng**2):.4f} C/km')
                if np.abs(dsst) > 0.001:
                    print(f'    FD along-track: {dsst/dist:.4f} C/km')
