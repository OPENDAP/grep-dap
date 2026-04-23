"""Determine longitude origin and validate coordinates."""
from pydap.client import open_url
import numpy as np

url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

day_count = np.array(ds['day_pixel_count'][:,:].data)
day_sum = np.array(ds['day_sum_SST'][:,:].data)
mask = day_count > 0
day_mean = np.full_like(day_sum, np.nan)
day_mean[mask] = day_sum[mask] / day_count[mask]

# dim0 = longitude (360), dim1 = latitude (180)
# Latitude: col 0 = 90S, col 179 = 89N (1-degree grid, equator ~ col 90)
# So lat = -90 + col + 0.5 (cell centers)

# For longitude: need to determine if row 0 = 0E, 0.5E, or -179.5E, etc.
# Look at land patterns:
# - Rows 109-116 have least ocean. If this is Africa (~10E-50E), then row 0 ~ -100E (=260E)
# - But more commonly, global grids start at 0E or 0.5E or -180E

# Strategy: compare SST at known ocean locations
# Gulf Stream region: ~35N, ~-70E (=290E if 0-360, or row 290 if 0-indexed from 0E)
# Kuroshio region: ~35N, ~140E (row 140 if 0-indexed from 0E)

# If dim0 starts at 0E:
#   Gulf Stream = row 290, col ~125 (35N -> col 90+35=125)
#   Kuroshio = row 140, col 125
# If dim0 starts at 0.5E:
#   Gulf Stream = row 290, col 125
#   Kuroshio = row 140, col 125

# Actually, the equator sign flip was at col ~95, not col 90
# This suggests col 0 = -89.5 and col 90 = 0.5N (equator between col 89 and 90)
# Or col 0 = -90 and col 90 = 0 (equator at col 90)

print('='*60)
print('Equator location refinement')
print('='*60)

# Load July data
url_jul = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_07_2024.nc'
ds_jul = open_url(url_jul, protocol='dap2')
jul_count = np.array(ds_jul['day_pixel_count'][:,:].data)
jul_sum = np.array(ds_jul['day_sum_SST'][:,:].data)
jul_mask = jul_count > 0
jul_mean = np.full_like(jul_sum, np.nan)
jul_mean[jul_mask] = jul_sum[jul_mask] / jul_count[jul_mask]

jan_profile = np.nanmean(day_mean, axis=0)
jul_profile = np.nanmean(jul_mean, axis=0)
diff = jul_profile - jan_profile

# Fine-grained look around equator
print('Jul-Jan diff around equator (cols 85-105):')
for i in range(85, 106):
    d = diff[i]
    if not np.isnan(d):
        print(f'  col {i}: {d:+.3f}')

# The warmest latitude in January should be in SH tropics (~-15 to -20)
# The warmest latitude in July should be in NH tropics (~15 to 20)
jan_warmest_col = np.nanargmax(jan_profile)
jul_warmest_col = np.nanargmax(jul_profile)
print(f'\nWarmest column in Jan: {jan_warmest_col} (SST={jan_profile[jan_warmest_col]:.2f})')
print(f'Warmest column in Jul: {jul_warmest_col} (SST={jul_profile[jul_warmest_col]:.2f})')
print(f'If col=lat+90: Jan warmest at lat {jan_warmest_col-90}, Jul warmest at lat {jul_warmest_col-90}')

print('\n' + '='*60)
print('Longitude origin determination')
print('='*60)

# Key idea: the Mediterranean Sea (~30-45E, ~30-45N) is a warm enclosed sea
# It should show as an isolated warm spot
# If row 0 = 0E, Mediterranean = rows 30-45, cols 120-135

# Also: No-data rows are land-dominated longitudes
# Major land masses by longitude:
# Americas: ~60-120W = 240-300E
# Africa/Europe: ~10W-50E = 350-50
# Asia/Australia: ~60-180E = 60-180

# Rows with LEAST data (from previous run):
# Rows 109-116 and 199-210
# If row 0 = 0.5E:
#   rows 109-116 -> 109.5-116.5E (Southeast Asia/Indonesia) - MATCHES!
#   rows 199-210 -> 199.5-210.5E = same but this doesn't work
# Hmm, 199-210E doesn't correspond to major land

# If row 0 = -179.5 (i.e., starting from dateline):
#   rows 109-116 -> -70.5 to -63.5 (South America/Andes) - possible
#   rows 199-210 -> 19.5 to 30.5E (Africa) - MATCHES!

# If row 0 = 0.5E (standard):
#   rows 109-116 -> 109.5-116.5E (Indonesia/Borneo/Java) - YES, very low ocean
#   rows 199-210 -> 199.5-210.5E (not meaningful, wraps around?)
# Wait, 360 rows, 0-indexed: if row 0 = 0.5E, row 359 = 359.5E
# Row 199 = 199.5E. But 199.5E = 199.5-360 = -160.5E? No, that's already in range.
# Actually... 199.5E is in the western Pacific. That IS ocean.
# Let me recheck.

# Actually the rows wrap around. If 0E-360E:
#   Row 199 = 199.5E (western Pacific) should be ocean
#   But rows 200-210 have LEAST data - that's mid-Pacific, should be pure ocean!
# This doesn't work for 0E start.

# If row 0 = -179.5 (grid from -180 to 180):
#   Row 109 = -70.5 (South America)
#   Row 200 = 20.5E (central Africa) - YES!
#   Row 201 = 21.5E, Row 210 = 31.5E (eastern Africa/Middle East) - YES!

# This fits! Let me verify: row 0 = -179.5E
# Most data rows: 0, 37, 152-163
# Row 0 = -179.5E (dateline, mid-Pacific = ocean)
# Row 37 = -142.5E (south Pacific = ocean)
# Row 152 = -27.5E (mid-Atlantic = ocean)
# Row 160 = -19.5E (Atlantic = ocean)

# These all check out!

# Or: row 0 = 0.5E
# Row 200 = 200.5E = -159.5W (mid-Pacific) but this IS ocean, so low data fraction doesn't match.

# Conclusion: dim0 starts at -179.5 or -180 (i.e., the grid runs from -180 to 180)

print('Testing hypothesis: row 0 = -179.5E (grid from -180E to 180E)')
print()

# Mediterranean test: ~15E = row 194-195, lat ~35N = col 125
# Should be warm and isolated
for label, row, col in [
    ('Mediterranean (~15E, 35N)', 194, 125),
    ('Gulf Stream (~-70E=row 110, 35N)', 110, 125),
    ('Kuroshio (~140E=row 319, 35N)', 319, 125),
    ('S. Pacific (~-160E=row 20, 45S)', 20, 45),
    ('Arabian Sea (~60E=row 239, 20N)', 239, 110),
]:
    if 0 <= row < 360 and 0 <= col < 180:
        sst = day_mean[row, col]
        cnt = day_count[row, col]
        print(f'  {label}: SST={f"{sst:.2f}" if not np.isnan(sst) else "NaN"}, count={cnt:.0f}')

print()
# Also test 0.5E start hypothesis
print('Testing hypothesis: row 0 = 0.5E (grid from 0E to 360E)')
for label, row, col in [
    ('Mediterranean (~15E=row 15, 35N)', 15, 125),
    ('Gulf Stream (~290E=row 290, 35N)', 290, 125),
    ('Kuroshio (~140E=row 140, 35N)', 140, 125),
    ('Indonesia (~110E=row 110, 0N)', 110, 90),
    ('Central Africa (~20E=row 20, 0N)', 20, 90),
]:
    if 0 <= row < 360 and 0 <= col < 180:
        sst = day_mean[row, col]
        cnt = day_count[row, col]
        print(f'  {label}: SST={f"{sst:.2f}" if not np.isnan(sst) else "NaN"}, count={cnt:.0f}')
