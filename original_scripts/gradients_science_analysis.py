"""Analyze gradients_by_period to understand the processing pipeline
and science context for a descriptive writeup."""
from pydap.client import open_url
import numpy as np

url = 'https://sst-aqua.gso.uri.edu/opendap/gradients_by_period/augmented_monthly_stats_01_2024.nc'
ds = open_url(url, protocol='dap2')

# Load key variables
day_count = np.array(ds['day_pixel_count'][:,:].data)
day_sum_sst = np.array(ds['day_sum_SST'][:,:].data)
day_sum_mag = np.array(ds['day_sum_magnitude_gradient'][:,:].data)
day_as_count = np.array(ds['day_as_pixel_count'][:,:].data)
day_at_count = np.array(ds['day_at_pixel_count'][:,:].data)
day_sum_east = np.array(ds['day_sum_eastward_gradient'][:,:].data)
day_sum_north = np.array(ds['day_sum_northward_gradient'][:,:].data)
day_sum_as = np.array(ds['day_sum_grad_as_per_km'][:,:].data)
day_sum_at = np.array(ds['day_sum_grad_at_per_km'][:,:].data)
day_sum_mag_km = np.array(ds['day_sum_grad_mag_per_km'][:,:].data)

night_count = np.array(ds['night_pixel_count'][:,:].data)
night_sum_sst = np.array(ds['night_sum_SST'][:,:].data)

# Compute means where possible
mask = day_count > 0
mean_sst = np.full_like(day_sum_sst, np.nan)
mean_sst[mask] = day_sum_sst[mask] / day_count[mask]

mean_mag = np.full_like(day_sum_mag, np.nan)
mean_mag[mask] = day_sum_mag[mask] / day_count[mask]

mask_as = day_as_count > 0
mean_as = np.full_like(day_sum_as, np.nan)
mean_as[mask_as] = day_sum_as[mask_as] / day_as_count[mask_as]

mask_at = day_at_count > 0
mean_at = np.full_like(day_sum_at, np.nan)
mean_at[mask_at] = day_sum_at[mask_at] / day_at_count[mask_at]

mean_mag_km = np.full_like(day_sum_mag_km, np.nan)
mean_mag_km[mask_as] = day_sum_mag_km[mask_as] / day_as_count[mask_as]

mean_east = np.full_like(day_sum_east, np.nan)
mean_east[mask] = day_sum_east[mask] / day_count[mask]

mean_north = np.full_like(day_sum_north, np.nan)
mean_north[mask] = day_sum_north[mask] / day_count[mask]

print('='*60)
print('PART 1: Which pixel count goes with which gradient?')
print('='*60)

# The eastward/northward/magnitude gradients use day_pixel_count
# The as/at/mag_per_km gradients use day_as_pixel_count or day_at_pixel_count
# Let's check: are magnitude_gradient and grad_mag_per_km the same quantity?
# If so, they should have the same mean when using their respective counts

# For cells where both counts > 0
both = mask & mask_as
print(f'Cells with both SST and as counts: {np.sum(both)}')

# Compare magnitude_gradient/day_count vs grad_mag_per_km/as_count
mag1 = day_sum_mag[both] / day_count[both]
mag2 = day_sum_mag_km[both] / day_as_count[both]
close = np.abs(mag1 - mag2) < 0.001 * (np.abs(mag1) + 1e-10)
print(f'mag_gradient/day_count == grad_mag_km/as_count: {np.sum(close)}/{len(close)}')
print(f'  Correlation: {np.corrcoef(mag1[~np.isnan(mag1) & ~np.isnan(mag2)], mag2[~np.isnan(mag1) & ~np.isnan(mag2)])[0,1]:.6f}')
print(f'  Mean ratio: {np.nanmean(mag1/mag2):.4f}')

# So these are NOT the same. mag_gradient is computed per-pixel and summed with day_count
# grad_mag_per_km is computed from the as/at components with different sampling

print()
print('='*60)
print('PART 2: Where are the strongest gradients? (Science context)')
print('='*60)

# Identify gradient hotspots -- these should be western boundary currents
# lon[i] = -179.5 + i, lat[j] = -89.5 + j

# Top 20 cells by mean gradient magnitude
flat_idx = np.argsort(mean_mag.ravel())[::-1]
print('\nTop 20 cells by mean gradient magnitude:')
for k in range(20):
    idx = flat_idx[k]
    i, j = divmod(idx, 180)
    lon = -179.5 + i
    lat = -89.5 + j
    val = mean_mag.ravel()[idx]
    if np.isnan(val):
        continue
    print(f'  [{i},{j}] lon={lon:.1f}, lat={lat:.1f}: mag={val:.4f} C/km')

print()
print('='*60)
print('PART 3: Day vs Night comparison')
print('='*60)

# Day vs night pixel counts
night_mask = night_count > 0
mean_sst_night = np.full_like(night_sum_sst, np.nan)
mean_sst_night[night_mask] = night_sum_sst[night_mask] / night_count[night_mask]

both_dn = mask & night_mask
day_night_diff = mean_sst[both_dn] - mean_sst_night[both_dn]
valid = ~np.isnan(day_night_diff)
print(f'Day-Night SST difference (where both exist):')
print(f'  Mean: {np.nanmean(day_night_diff):.3f} C')
print(f'  Median: {np.nanmedian(day_night_diff):.3f} C')
print(f'  Std: {np.nanstd(day_night_diff):.3f} C')
print(f'  Range: {np.nanmin(day_night_diff):.3f} to {np.nanmax(day_night_diff):.3f} C')
print()
print(f'Day pixel coverage: {np.sum(mask)} cells')
print(f'Night pixel coverage: {np.sum(night_mask)} cells')
print(f'Both: {np.sum(both_dn)} cells')

print()
print('='*60)
print('PART 4: "Augmented" -- what was added?')
print('='*60)

# Variable grouping by pixel count denominator
print('Variables grouped by pixel count denominator:')
print()
print('Group 1: day_pixel_count (SST + geographic gradients)')
print('  day_pixel_count, day_sum_SST, day_sum_SST_squared')
print('  day_sum_eastward_gradient, day_sum_eastward_gradient_squared')
print('  day_sum_northward_gradient, day_sum_northward_gradient_squared')
print('  day_sum_magnitude_gradient, day_sum_magnitude_gradient_squared')
print()
print('Group 2: day_as_pixel_count (along-swath + satellite magnitude)')
print('  day_as_pixel_count')
print('  day_sum_grad_as_per_km, day_sum_grad_as_per_km_squared')
print('  day_sum_grad_mag_per_km, day_sum_grad_mag_per_km_squared')
print()
print('Group 3: day_at_pixel_count (across-track)')
print('  day_at_pixel_count')
print('  day_sum_grad_at_per_km, day_sum_grad_at_per_km_squared')
print()
print('Hypothesis: "augmented" means the original files had only')
print('  Group 1 (SST + geographic gradients), and Groups 2 & 3')
print('  (satellite-frame gradients) were added later.')

print()
print('='*60)
print('PART 5: Temporal coverage estimation')
print('='*60)

# How many L2 orbits contribute to one monthly file?
# ~14.5 orbits/day * 31 days = ~450 orbits/month
# Each orbit covers a swath across the globe
# At 1km resolution, one 1-degree cell has ~111km x 111km = ~12321 pixels potential
# But clouds reduce coverage

print(f'Max day pixels in a cell: {day_count.max():.0f}')
print(f'Max night pixels: {night_count.max():.0f}')
print(f'If ~450 orbits/month, ~1354 cross-track pixels per orbit:')
print(f'  Max possible overpasses per cell ~ 2-3 per day * 31 = ~90')
print(f'  Each overpass contributes up to ~111 pixels in a 1-deg cell')
print(f'  Max theoretical: ~90 * 111 = ~10000 (equatorial)')
print(f'  Observed max: {day_count.max():.0f} (much higher at high latitudes)')
print(f'  This makes sense: polar orbits overlap more at high latitudes')
print()

# Compare equatorial vs high-latitude counts
eq_counts = day_count[:, 85:95]  # near equator
hi_counts = day_count[:, 140:160]  # 50-70N
print(f'Equatorial mean count (where >0): {np.mean(eq_counts[eq_counts>0]):.0f}')
print(f'High-latitude mean count (where >0): {np.mean(hi_counts[hi_counts>0]):.0f}')

print()
print('='*60)
print('PART 6: Cross-check with SST_Orbits processing')
print('='*60)

# The SST_Orbits files contain:
# - SST_In: the input SST (after quality masking)
# - eastward_gradient, northward_gradient: geographic gradients
# - regridded_sst, regridded_latitude, regridded_longitude: regridded to equal spacing
# - qual_sst: quality flags
# - refined_mask: additional masking

# The pipeline is likely:
# 1. Start with L2 MODIS AQUA granules from GSFC
# 2. Apply Fix_MODIS_Mask to quality-filter (SST_Orbits step)
# 3. Compute eastward/northward gradients on the orbit grid (SST_Orbits)
# 4. Compute along-swath/across-track gradients on the orbit grid
# 5. Bin all values to 1-degree global grid
# 6. Accumulate sums, sums-of-squares, and counts per month

print('Inferred processing pipeline:')
print('  1. L2 MODIS AQUA SST granules from NASA GSFC')
print('  2. Quality masking (Fix_MODIS_Mask, URI processing)')
print('  3. Orbit-level gradient computation:')
print('     - Geographic: eastward/northward SST gradients (C/km)')
print('     - Satellite: along-swath/across-track gradients (C/km)')
print('     - Magnitude: sqrt(east^2 + north^2) and sqrt(as^2 + at^2)')
print('  4. Binning to 1-degree global grid')
print('  5. Monthly accumulation of sums, sums-of-squares, counts')
print('  6. Separate day/night tracking')
print()
print('The "augmented" prefix likely indicates enrichment with')
print('satellite-frame gradient statistics (Groups 2 & 3) beyond')
print('the original geographic-frame statistics (Group 1).')
