"""Sample gradient data and explore 5day gradients."""
from pydap.client import open_url
import numpy as np

# Sample data from gradients_by_period
url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

print('=== Sampling gradients_by_period data ===')

# Pixel counts
day_count = np.array(ds['day_pixel_count'][:,:].data)
night_count = np.array(ds['night_pixel_count'][:,:].data)
print(f'Day pixel count: min={np.nanmin(day_count)}, max={np.nanmax(day_count)}, shape={day_count.shape}')
print(f'Night pixel count: min={np.nanmin(night_count)}, max={np.nanmax(night_count)}')
print()

# SST sums -- can compute mean SST
day_sum = np.array(ds['day_sum_SST'][:,:].data)
# Where count > 0, compute mean
mask = day_count > 0
day_mean_sst = np.full_like(day_sum, np.nan)
day_mean_sst[mask] = day_sum[mask] / day_count[mask]
print(f'Day mean SST (computed): min={np.nanmin(day_mean_sst):.2f}, max={np.nanmax(day_mean_sst):.2f}')
print(f'Day mean SST overall mean: {np.nanmean(day_mean_sst):.2f}')
print()

# Gradient magnitude
day_grad_mag = np.array(ds['day_sum_magnitude_gradient'][:,:].data)
day_mean_grad = np.full_like(day_grad_mag, np.nan)
day_as_count = np.array(ds['day_as_pixel_count'][:,:].data)
mask_as = day_as_count > 0
day_mean_grad[mask_as] = day_grad_mag[mask_as] / day_as_count[mask_as]
print(f'Day mean gradient magnitude: min={np.nanmin(day_mean_grad):.4f}, max={np.nanmax(day_mean_grad):.4f}')
print(f'Day mean gradient magnitude overall mean: {np.nanmean(day_mean_grad):.4f}')
print()

# Grid interpretation: 360x180 is 1-degree global
print('Grid interpretation:')
print(f'  Shape: {day_count.shape} -> likely 1-degree global grid')
print(f'  360 columns (longitude), 180 rows (latitude)')
print(f'  Non-zero day pixels: {np.sum(day_count > 0)} of {day_count.size} cells')
print(f'  Non-zero night pixels: {np.sum(night_count > 0)} of {night_count.size} cells')
print()

# Now explore gradients_by_period_5day
print('='*60)
print('=== gradients_by_period_5day ===')
url5 = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period_5day/augmented_5day_stats_001_2024.nc'
try:
    ds5 = open_url(url5, protocol='dap2')
    print(f'Keys: {list(ds5.keys())}')
    print(f'Attributes: {ds5.attributes}')
    for vname in list(ds5.keys())[:5]:
        v = ds5[vname]
        print(f'  {vname}: shape={v.shape}, dtype={v.dtype}, attrs={v.attributes}')
except Exception as e:
    print(f'Error with 001: {e}')
    # Try different naming
    for name in ['augmented_5day_stats_01_2024.nc', 'augmented_5day_stats_2024_001.nc']:
        try:
            url5b = f'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period_5day/{name}'
            ds5b = open_url(url5b, protocol='dap2')
            print(f'Found with name: {name}')
            print(f'Keys: {list(ds5b.keys())[:10]}')
            break
        except Exception as e2:
            print(f'  {name}: {e2}')
