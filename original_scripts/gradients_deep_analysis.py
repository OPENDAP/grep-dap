"""Deep analysis of gradients_by_period to infer COARDS metadata."""
from pydap.client import open_url
import numpy as np

url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

print('='*60)
print('PART 1: Grid orientation and coordinate inference')
print('='*60)

# Load pixel counts and SST sums
day_count = np.array(ds['day_pixel_count'][:,:].data)
day_sum = np.array(ds['day_sum_SST'][:,:].data)

# Where is the data?
print(f'Array shape: {day_count.shape}')  # (360, 180)

# Compute mean SST where data exists
mask = day_count > 0
day_mean = np.full_like(day_sum, np.nan)
day_mean[mask] = day_sum[mask] / day_count[mask]

# Check for latitude pattern: SST should be cold at poles, warm at equator
# If dim0=lat (360 rows), then rows near 0 and 359 should be cold, middle warm
# If dim0=lon (360 cols), then columns should show longitude variation

# Row-wise mean (average across columns for each row)
row_means = np.nanmean(day_mean, axis=1)
# Column-wise mean (average across rows for each column)
col_means = np.nanmean(day_mean, axis=0)

print('\nRow-wise mean SST (first 10, middle 10, last 10):')
print(f'  Rows 0-9: {row_means[:10]}')
print(f'  Rows 175-184: {row_means[175:185]}')
print(f'  Rows 350-359: {row_means[350:360]}')

print('\nColumn-wise mean SST (first 10, middle 10, last 10):')
print(f'  Cols 0-9: {col_means[:10]}')
print(f'  Cols 85-94: {col_means[85:95]}')
print(f'  Cols 170-179: {col_means[170:180]}')

# If 360 = longitude and 180 = latitude:
#   - Row means (avg over lat) should be ~constant (lon doesn't drive SST much)
#   - Col means (avg over lon) should show pole-equator-pole pattern

# If 360 = latitude and 180 = longitude:
#   - Row means should show pole-equator-pole
#   - Col means should be ~constant

row_std = np.nanstd(row_means)
col_std = np.nanstd(col_means)
print(f'\nRow mean std: {row_std:.2f}')
print(f'Col mean std: {col_std:.2f}')
print('If col_std >> row_std => dim0=lon(360), dim1=lat(180)')
print('If row_std >> col_std => dim0=lat(360), dim1=lon(180)')

# Look at where data is absent (land)
# Fraction of data per row and column
row_frac = np.sum(day_count > 0, axis=1) / 180
col_frac = np.sum(day_count > 0, axis=0) / 360

print(f'\nData fraction per row (first 5): {row_frac[:5]}')
print(f'Data fraction per row (middle 5, rows 175-179): {row_frac[175:180]}')
print(f'Data fraction per row (last 5): {row_frac[355:360]}')

print(f'\nData fraction per col (first 5): {col_frac[:5]}')
print(f'Data fraction per col (col 85-89): {col_frac[85:90]}')
print(f'Data fraction per col (last 5): {col_frac[175:180]}')
