"""Infer coordinate values and validate grid for gradients_by_period."""
from pydap.client import open_url
import numpy as np

url_jan = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
url_jul = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_07_2024.nc'

ds_jan = open_url(url_jan, protocol='dap2')
ds_jul = open_url(url_jul, protocol='dap2')

jan_count = np.array(ds_jan['day_pixel_count'][:,:].data)
jan_sum = np.array(ds_jan['day_sum_SST'][:,:].data)
jul_count = np.array(ds_jul['day_pixel_count'][:,:].data)
jul_sum = np.array(ds_jul['day_sum_SST'][:,:].data)

jan_mask = jan_count > 0
jul_mask = jul_count > 0
jan_mean = np.full_like(jan_sum, np.nan)
jul_mean = np.full_like(jul_sum, np.nan)
jan_mean[jan_mask] = jan_sum[jan_mask] / jan_count[jan_mask]
jul_mean[jul_mask] = jul_sum[jul_mask] / jul_count[jul_mask]

# dim0=lon(360), dim1=lat(180)
# Column-wise (lat) profile - average across all longitudes
jan_lat_profile = np.nanmean(jan_mean, axis=0)
jul_lat_profile = np.nanmean(jul_mean, axis=0)

print('='*60)
print('PART 2: Coordinate inference')
print('='*60)

# Determine lat direction: is col 0 south pole or north pole?
# In Jan (NH winter), NH should be cold, SH warm
# In Jul (NH summer), NH should be warm, SH cold
print('\nJanuary lat profile (col 0, 45, 90, 135, 179):')
for i in [0, 9, 45, 90, 135, 170, 179]:
    jv = f'{jan_lat_profile[i]:.2f}' if not np.isnan(jan_lat_profile[i]) else 'NaN'
    jlv = f'{jul_lat_profile[i]:.2f}' if not np.isnan(jul_lat_profile[i]) else 'NaN'
    print(f'  col {i}: Jan={jv}, Jul={jlv}')

# Seasonal difference (Jul - Jan) should be positive in NH, negative in SH
diff = jul_lat_profile - jan_lat_profile
print('\nJul-Jan difference by column:')
for i in range(0, 180, 10):
    if not np.isnan(diff[i]):
        print(f'  col {i}: {diff[i]:+.2f}')

# Find where the sign flips (equator)
print('\nSign of Jul-Jan difference:')
for i in range(0, 180):
    if not np.isnan(diff[i]):
        if i > 0 and not np.isnan(diff[i-1]):
            if np.sign(diff[i]) != np.sign(diff[i-1]):
                print(f'  Sign flip at col {i}: {diff[i-1]:+.2f} -> {diff[i]:+.2f}')

# Now determine longitude: check where data is absent (land masses)
# Row-wise data fraction
row_frac = np.sum(jan_count > 0, axis=1) / 180

print('\n\nLongitude inference from data fraction:')
# Find rows with lowest data fraction (most land)
low_frac_rows = np.argsort(row_frac)[:20]
print(f'Rows with least data: {sorted(low_frac_rows)}')
print(f'Their fractions: {row_frac[sorted(low_frac_rows)]}')

# Find rows with highest fraction (most ocean)
high_frac_rows = np.argsort(row_frac)[-10:]
print(f'Rows with most data: {sorted(high_frac_rows)}')
print(f'Their fractions: {row_frac[sorted(high_frac_rows)]}')

# The Pacific should be mostly ocean: if lon starts at 0E, Pacific is ~rows 120-240
# If lon starts at -180, Pacific is ~rows 0-60 and 300-360
# Let me check specific row patterns
print('\nRow data fraction pattern (every 20 rows):')
for i in range(0, 360, 20):
    print(f'  row {i}: {row_frac[i]:.3f}')

# Cross-reference with SST_Orbits to validate coordinates
print('\n' + '='*60)
print('PART 3: Cross-reference with SST_Orbits')
print('='*60)

# From SST_Orbits we know the coordinates explicitly
# Let me load a small SST orbit sample and bin it to 1-degree to compare
url_orbit = 'https://sst-aqua.gso.uri.edu/opendap/SST_Orbits/2024/01/AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4'
ds_orbit = open_url(url_orbit, protocol='dap2')

# Get nadir lat/lon to see orbit track
nadir_lat = np.array(ds_orbit['/nadir_latitude'][:].data)
nadir_lon = np.array(ds_orbit['/nadir_longitude'][:].data)
valid = (nadir_lat > -900) & (nadir_lon > -900)
print(f'Orbit nadir lat range: {nadir_lat[valid].min():.1f} to {nadir_lat[valid].max():.1f}')
print(f'Orbit nadir lon range: {nadir_lon[valid].min():.1f} to {nadir_lon[valid].max():.1f}')

# Check gradient variable relationships
print('\n' + '='*60)
print('PART 4: Variable relationship analysis')
print('='*60)

# Compare different pixel counts
day_as = np.array(ds_jan['day_as_pixel_count'][:,:].data)
day_at = np.array(ds_jan['day_at_pixel_count'][:,:].data)
print(f'\nday_pixel_count range: {jan_count.min():.0f} to {jan_count.max():.0f}')
print(f'day_as_pixel_count range: {day_as.min():.0f} to {day_as.max():.0f}')
print(f'day_at_pixel_count range: {day_at.min():.0f} to {day_at.max():.0f}')

# Are they the same?
print(f'\nday_count == day_as? {np.allclose(jan_count, day_as)}')
print(f'day_count == day_at? {np.allclose(jan_count, day_at)}')
print(f'day_as == day_at? {np.allclose(day_as, day_at)}')

# Ratio
mask_all = (jan_count > 0) & (day_as > 0) & (day_at > 0)
ratio_as = jan_count[mask_all] / day_as[mask_all]
ratio_at = jan_count[mask_all] / day_at[mask_all]
print(f'day_count/day_as ratio: mean={ratio_as.mean():.3f}, min={ratio_as.min():.3f}, max={ratio_as.max():.3f}')
print(f'day_count/day_at ratio: mean={ratio_at.mean():.3f}, min={ratio_at.min():.3f}, max={ratio_at.max():.3f}')

# Check gradient magnitude vs eastward/northward components
day_east = np.array(ds_jan['day_sum_eastward_gradient'][:,:].data)
day_north = np.array(ds_jan['day_sum_northward_gradient'][:,:].data)
day_mag = np.array(ds_jan['day_sum_magnitude_gradient'][:,:].data)
day_grad_as = np.array(ds_jan['day_sum_grad_as_per_km'][:,:].data)
day_grad_at = np.array(ds_jan['day_sum_grad_at_per_km'][:,:].data)
day_grad_mag = np.array(ds_jan['day_sum_grad_mag_per_km'][:,:].data)

# Where all are non-zero
m = mask_all & (day_east != 0) & (day_north != 0)
print(f'\nGradient analysis (cells with all non-zero):')

# Are eastward/northward and as/at related?
# "as" likely = along-swath, "at" likely = across-track (satellite terms)
# These would be in the satellite coordinate system
# "eastward"/"northward" would be in geographic coordinates

# Check if magnitude = sqrt(east^2 + north^2) (per-pixel, not on sums)
# Can't check exactly on sums, but for single cells with count=1
single = jan_count == 1
print(f'Cells with exactly 1 pixel: {np.sum(single)}')
if np.sum(single) > 0:
    s_east = day_east[single]
    s_north = day_north[single]
    s_mag = day_mag[single]
    computed_mag = np.sqrt(s_east**2 + s_north**2)
    close = np.abs(computed_mag - s_mag) < 0.001 * np.abs(s_mag + 1e-10)
    print(f'  mag == sqrt(east^2+north^2): {np.sum(close)}/{len(close)}')
    # Show a few
    for i in range(min(5, len(s_east))):
        print(f'    east={s_east[i]:.6f}, north={s_north[i]:.6f}, mag={s_mag[i]:.6f}, computed={computed_mag[i]:.6f}')

# Check units - what are the typical gradient values?
# Mean gradient = sum / count
day_mean_east = np.full_like(day_east, np.nan)
day_mean_east[jan_mask] = day_east[jan_mask] / jan_count[jan_mask]
day_mean_north = np.full_like(day_north, np.nan)
day_mean_north[jan_mask] = day_north[jan_mask] / jan_count[jan_mask]

print(f'\nMean eastward gradient range: {np.nanmin(day_mean_east):.6f} to {np.nanmax(day_mean_east):.6f}')
print(f'Mean northward gradient range: {np.nanmin(day_mean_north):.6f} to {np.nanmax(day_mean_north):.6f}')

# Compare with SST_Orbits gradient units (C/km with scale 0.0001)
# So orbit gradients are in C/km. Are the monthly sums also in C/km?
day_mean_mag = np.full_like(day_mag, np.nan)
day_mean_mag[jan_mask] = day_mag[jan_mask] / jan_count[jan_mask]
print(f'Mean magnitude gradient range: {np.nanmin(day_mean_mag):.6f} to {np.nanmax(day_mean_mag):.6f}')

# grad_as and grad_at mean values
day_mean_as = np.full_like(day_grad_as, np.nan)
m_as = day_as > 0
day_mean_as[m_as] = day_grad_as[m_as] / day_as[m_as]
day_mean_at = np.full_like(day_grad_at, np.nan)
m_at = day_at > 0
day_mean_at[m_at] = day_grad_at[m_at] / day_at[m_at]
day_mean_mag2 = np.full_like(day_grad_mag, np.nan)
# grad_mag_per_km uses which count?
# Try day_as_pixel_count first
day_mean_mag2[m_as] = day_grad_mag[m_as] / day_as[m_as]

print(f'Mean grad_as_per_km range: {np.nanmin(day_mean_as):.6f} to {np.nanmax(day_mean_as):.6f}')
print(f'Mean grad_at_per_km range: {np.nanmin(day_mean_at):.6f} to {np.nanmax(day_mean_at):.6f}')
print(f'Mean grad_mag_per_km range: {np.nanmin(day_mean_mag2):.6f} to {np.nanmax(day_mean_mag2):.6f}')
