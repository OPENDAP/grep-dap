"""Final validation of coordinates and variance computation."""
from pydap.client import open_url
import numpy as np

url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

day_count = np.array(ds['day_pixel_count'][:,:].data)
day_sum = np.array(ds['day_sum_SST'][:,:].data)
day_sum2 = np.array(ds['day_sum_SST_squared'][:,:].data)
mask = day_count > 1  # need >1 for variance

print('='*60)
print('PART 5: Variance computation validation')
print('='*60)

# Compute mean and variance
day_mean = day_sum[mask] / day_count[mask]
day_var = (day_sum2[mask] / day_count[mask]) - day_mean**2
day_std = np.sqrt(np.maximum(day_var, 0))

print(f'SST mean range: {day_mean.min():.2f} to {day_mean.max():.2f}')
print(f'SST std range: {day_std.min():.4f} to {day_std.max():.4f}')
print(f'SST std mean: {day_std.mean():.4f}')
print(f'SST std median: {np.median(day_std):.4f}')

# Typical SST standard deviation within a 1-degree cell over a month
# should be a few degrees at most
print(f'\nPhysically reasonable? SST std within 1-deg cell over a month:')
print(f'  <1 C would be tropics, 1-3 C mid-latitudes, up to 5 C frontal zones')

# Check gradient variance too
day_as_count = np.array(ds['day_as_pixel_count'][:,:].data)
day_grad_as = np.array(ds['day_sum_grad_as_per_km'][:,:].data)
day_grad_as2 = np.array(ds['day_sum_grad_as_per_km_squared'][:,:].data)
mask_as = day_as_count > 1

grad_mean = day_grad_as[mask_as] / day_as_count[mask_as]
grad_var = (day_grad_as2[mask_as] / day_as_count[mask_as]) - grad_mean**2
grad_std = np.sqrt(np.maximum(grad_var, 0))
print(f'\nAlong-swath gradient mean range: {grad_mean.min():.6f} to {grad_mean.max():.6f}')
print(f'Along-swath gradient std range: {grad_std.min():.6f} to {grad_std.max():.6f}')

print('\n' + '='*60)
print('PART 6: Geographic validation of coordinate hypothesis')
print('='*60)
print('Hypothesis: lon[i] = -179.5 + i, lat[j] = -89.5 + j')
print()

day_mean_full = np.full_like(day_sum, np.nan)
day_mean_full[day_count > 0] = day_sum[day_count > 0] / day_count[day_count > 0]

# Test well-known geographic SST patterns (January)
tests = [
    # (description, lon, lat, expected_SST_range, expect_data)
    ('Gulf Stream (off Cape Hatteras)', -75, 35, (15, 25), True),
    ('Labrador Sea', -55, 55, (-1, 5), True),
    ('Mediterranean', 15, 37, (13, 20), True),
    ('Arabian Sea', 60, 20, (24, 28), True),
    ('Kuroshio', 140, 35, (14, 22), True),
    ('Southern Ocean', -60, -55, (0, 8), True),
    ('Tropical W. Pacific', 160, 0, (28, 32), True),
    ('Amazon rainforest', -60, -5, None, False),  # land
    ('Sahara desert', 10, 25, None, False),  # land
    ('Himalayas', 85, 30, None, False),  # land
]

for desc, lon, lat, expected_range, expect_data in tests:
    # Convert to grid indices
    i = int(lon + 179.5)  # lon -> row
    j = int(lat + 89.5)   # lat -> col
    if 0 <= i < 360 and 0 <= j < 180:
        sst = day_mean_full[i, j]
        cnt = day_count[i, j]
        has_data = cnt > 0

        status = ''
        if expect_data and has_data:
            if expected_range and expected_range[0] <= sst <= expected_range[1]:
                status = 'PASS'
            elif expected_range:
                status = f'RANGE? (expected {expected_range[0]}-{expected_range[1]})'
            else:
                status = 'HAS DATA'
        elif not expect_data and not has_data:
            status = 'PASS (no data = land)'
        elif expect_data and not has_data:
            status = 'FAIL (expected data)'
        else:
            status = f'FAIL (land but has data, SST={sst:.1f})'

        sst_str = f'{sst:.2f}' if has_data else 'NaN'
        print(f'  {desc}: [{i},{j}] SST={sst_str}, n={cnt:.0f} -> {status}')

print('\n' + '='*60)
print('PART 7: Check relationship between gradient types')
print('='*60)

# For cells with count=1, all gradient types should agree on magnitude
single = day_count == 1
single_as = day_as_count == 1
both_single = single & single_as & (day_as_count > 0)

day_east = np.array(ds['day_sum_eastward_gradient'][:,:].data)
day_north = np.array(ds['day_sum_northward_gradient'][:,:].data)
day_mag = np.array(ds['day_sum_magnitude_gradient'][:,:].data)

# For single-pixel cells, sum = the single value
# magnitude_gradient vs grad_mag_per_km
day_mag_km = np.array(ds['day_sum_grad_mag_per_km'][:,:].data)

if np.sum(both_single) > 0:
    print(f'Cells with single pixel in both SST and as counts: {np.sum(both_single)}')
    # Check if magnitude_gradient == grad_mag_per_km for these
    mag1 = day_mag[both_single]
    mag2 = day_mag_km[both_single]
    close = np.abs(mag1 - mag2) < 0.0001 * (np.abs(mag1) + 1e-10)
    print(f'magnitude_gradient == grad_mag_per_km: {np.sum(close)}/{len(close)}')
    for i in range(min(5, len(mag1))):
        print(f'  mag_gradient={mag1[i]:.6f}, grad_mag_per_km={mag2[i]:.6f}')

    # Check east/north vs as/at
    grad_as = day_grad_as[both_single]
    grad_at_arr = np.array(ds['day_sum_grad_at_per_km'][:,:].data)
    grad_at = grad_at_arr[both_single]
    east = day_east[both_single]
    north = day_north[both_single]

    # as/at are rotated versions of east/north
    # mag should be the same: sqrt(as^2 + at^2) == sqrt(east^2 + north^2)
    mag_en = np.sqrt(east**2 + north**2)
    mag_asat = np.sqrt(grad_as**2 + grad_at**2)
    close2 = np.abs(mag_en - mag_asat) < 0.001 * (np.abs(mag_en) + 1e-10)
    print(f'\nsqrt(east^2+north^2) == sqrt(as^2+at^2): {np.sum(close2)}/{len(close2)}')
    for i in range(min(5, len(mag_en))):
        print(f'  east={east[i]:.6f}, north={north[i]:.6f}, mag_en={mag_en[i]:.6f}')
        print(f'  as={grad_as[i]:.6f}, at={grad_at[i]:.6f}, mag_asat={mag_asat[i]:.6f}')
