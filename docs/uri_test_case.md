# URI OPeNDAP Server Test Case

## Scope

This note summarizes an exploratory analysis of the URI OPeNDAP server at:

- `https://sst-aqua.gso.uri.edu/opendap/`

The goal was not to inventory every dataset, but to characterize what kinds of data the server appears to hold, how strong or weak the metadata are, and what this implies for the broader `grep-dap` project.

## Executive Summary

The server appears to be centered on sea surface temperature and SST-front analysis, not on general-purpose ocean data distribution. Two accessible collections were confirmed during this exploration:

- `SST_Orbits`
- `gradients_by_period`

Many other collections are listed at the root but returned `403 Forbidden` when accessed directly, including `JAXA_Orbits`, `RSS_Orbits`, `matchups`, `iQuamBuoy`, and the `timeSeries` collections. That matters. It means the root catalog is only a partial guide to what is actually usable.

The strongest evidence comes from one representative orbit dataset:

- `SST_Orbits/2024/01/AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4`

Its metadata explicitly identify it as a conditioned 1 km MODIS Aqua SST product associated with the `SST Fronts` project at URI/GSO. It contains SST, gradients, quality flags, masks, swath geolocation, orbit time information, and a nested regridding group with AMSR-E comparison variables. This is much more specific than “some remote gridded geophysical data.”

The accessible `gradients_by_period` collection appears to contain monthly, global, coarse-grid accumulations of SST and SST-gradient statistics. Its variable names are semantically informative, but its DAS metadata are sparse. This is a useful contrast with the orbit files: the data are still interpretable, but mostly because of filename patterns, array structure, and variable naming rather than rich formal metadata.

## What The Server Contains

### 1. Orbit-level conditioned SST products

`SST_Orbits` is organized by year and month. For example:

- `SST_Orbits/2024/01/`

contains many files named like:

- `AQUA_MODIS_orbit_115220_20240101T011558_L2_SST-URI_24-2.nc4`

That naming pattern already suggests:

- platform and sensor: Aqua MODIS
- granularity: orbit-level products
- product family: SST
- provenance: URI-conditioned or URI-produced derivative

The DAP metadata confirm this interpretation. The representative file declares:

- title: `Conditioned 1km (L2) MODIS AQUA SST`
- project: `SST Fronts`
- institution: URI Graduate School of Oceanography
- source: `Satellite observation`
- `cdm_data_type`: `Grid`
- CF metadata conventions

Key variables include:

- `SST_In`
- `regridded_sst`
- `eastward_gradient`
- `northward_gradient`
- `qual_sst`
- `refined_mask`
- `latitude`
- `longitude`
- `DateTime`
- `time_from_start_orbit`
- `contributing_granules/...`
- `Regrid_to_L2eqa/...`

This looks like a front-oriented conditioned SST product, not a raw L2 swath in its original form.

### 2. Derived monthly gradient/statistics products

`gradients_by_period` contains files such as:

- `monthly_stats_07_2024.nc`
- `augmented_monthly_stats_01_2024.nc`

The representative `augmented_monthly_stats_01_2024.nc` dataset has `360 x 180` lon-lat arrays and variables including:

- `day_pixel_count`, `night_pixel_count`
- `day_sum_SST`, `night_sum_SST`
- `day_sum_eastward_gradient`, `day_sum_northward_gradient`
- `day_sum_magnitude_gradient`
- squared-sum companions
- additional `*_as_*`, `*_at_*`, and `*_mag_*` fields

The variable set strongly suggests monthly spatial accumulations for SST and front-related gradient statistics on a global coarse grid.

## Metadata Quality

### Stronger case: orbit products

The representative orbit product has useful global attributes and variable attributes:

- descriptive title and summary
- creator, institution, project, acknowledgement, license
- CF-like standard names and units
- scale factors and fill values
- explicit quality and mask fields

The semantic metadata are not perfect. The summary mentions fields that do not obviously match the exposed variable list, so some text may reflect an earlier processing description. But overall, the orbit metadata are good enough to identify the product family with high confidence.

### Weaker case: derived monthly products

The monthly gradient dataset’s DAS is almost empty. The data remain interpretable mostly because:

- the filenames are informative
- the variable names are informative
- the structure is regular and geospatial
- the values behave like accumulations and counts

This is closer to the challenging case the project cares about: interpretation is possible, but only if the system uses multiple weak signals together.

## Data Samples And Reasoning

### Orbit sample

Using DAP2 ASCII, a small subset of the orbit file returned:

- raw `SST_In` values around `-3529` to `-3691`
- scale factor `0.005`
- inferred SST around `-17.6 C` to `-18.5 C`
- raw latitude values around `-69652`, implying about `-69.652 degrees`
- raw longitude values around `-100060`, implying about `-100.060 degrees`
- `DateTime = 1704071758.233`, which is `2024-01-01T01:15:58.233Z`
- `qual_sst` values of `3` in the small sample

This is internally consistent with a high-latitude Southern Hemisphere swath. The data values agree with the metadata rather than contradicting them.

The `contributing_granules` group also exposed granule timing and filename characters consistent with `AQUA_...`, reinforcing the MODIS Aqua interpretation.

### Monthly gradient sample

The first few grid cells of the monthly gradient product were all zero, but a mid-grid sample contained large nonzero values:

- `day_pixel_count` roughly `28k` to `55k`
- `night_pixel_count` roughly `43k` to `59k`
- `day_sum_SST` roughly `8e5` to `1.5e6`
- `day_sum_magnitude_gradient` roughly `1105` to `2328`

This supports the interpretation that these are accumulators or summary statistics over many observations, not single-scene fields.

One sampled `day_sum_SST` value was `NaN`, which is another realistic signal: downstream characterization should expect valid structured products to include missing or undefined cells.

## Operational Behavior

Two server behaviors are worth calling out because they matter for automated characterization:

1. The root catalog lists many collections that are not directly accessible. A system that trusts the root listing without checking access will overestimate what the server actually offers.
2. Metadata retrieval was reliable during this exploration, but pydap-based data access returned `503 Service Unavailable` once. Direct DAP2 ASCII subsetting did work.

There was another useful quirk: DAP2 ASCII constraint expressions worked when variables were referenced with absolute paths like `/SST_In`, not with bare names like `SST_In`.

## What I Think The Server Is

Based on the accessible evidence, I would describe the server as follows:

It is an SST-front-oriented OPeNDAP server centered on URI/GSO-derived products built from Aqua MODIS orbit data and related gradient/statistical analyses. It is not just a mirror of raw satellite products. It includes both conditioned orbit-scale SST fields and derived monthly spatial statistics that summarize SST and gradient behavior over time.

That conclusion is supported by:

- root collection names
- file naming conventions
- explicit global metadata in the orbit products
- variable names and units
- actual sampled values
- nested provenance-like groups such as `contributing_granules`
- the presence of gradient and AMSR-E comparison variables

## Relevance To `grep-dap`

This is a good test case for the project because it mixes:

- strong syntactic metadata
- partial but useful semantic metadata
- rich filename semantics
- derived products whose meaning is only partly explicit
- inconsistent server accessibility
- real remote-subsetting behavior

For GenAI-assisted interpretation, this server suggests a practical inference strategy:

- use catalog and filename patterns first
- verify with structural metadata from DDS
- lift semantics from DAS when available
- sample a tiny amount of data to test whether values match the inferred meaning
- record access failures as part of the server characterization

In other words, this server supports the project framing well: meaningful characterization is possible, but only if the system combines names, structure, attributes, sampled values, and operational behavior rather than relying on any single metadata source.

## Deeper Inference For `gradients_by_period`

### What changed in the augmented product

A direct comparison of:

- `monthly_stats_01_2024.nc`
- `augmented_monthly_stats_01_2024.nc`

is very informative.

The non-augmented file has 14 variables:

- `day_pixel_count`, `night_pixel_count`
- day/night sums of:
  - eastward gradient
  - northward gradient
  - gradient magnitude
- day/night sums of squares for those three gradient quantities

The augmented file has 34 variables. It keeps all 14 of the original variables and adds 20 more:

- `day_sum_SST`, `night_sum_SST`
- `day_sum_SST_squared`, `night_sum_SST_squared`
- `day_as_pixel_count`, `night_as_pixel_count`
- `day_at_pixel_count`, `night_at_pixel_count`
- day/night sums and sums of squares for:
  - `grad_as_per_km`
  - `grad_at_per_km`
  - `grad_mag_per_km`

That comparison supports a stronger interpretation than my first pass:

- `monthly_stats_*` is the original geographic-frame gradient climatology product.
- `augmented_monthly_stats_*` adds SST sufficient statistics plus a second gradient frame tied to the sensor geometry.

### Best semantic guess for `as` and `at`

My earlier write-up was too loose about these names. After rechecking the orbit-product metadata, I think the better guess is:

- `as` = along-scan
- `at` = along-track

Reasoning:

- the source orbit product explicitly describes one axis as along-scan and the other as along-track
- the abbreviations `as` and `at` match those terms directly
- this is a cleaner fit than alternatives like “along-swath” or “across-track”
- the separate `*_as_pixel_count` and `*_at_pixel_count` variables make sense if the two sensor-frame derivatives have different stencil-validity populations

I am moderately confident in this inference. It is still a guess because the server does not expose formal semantic metadata for these variables.

### Stronger structural inference

The DDS already names the dimensions:

- `lon = 360`
- `lat = 180`

So the file is not only “probably” lon-lat gridded; the dimension names already tell us that. What is missing are COARDS-style coordinate variables. The most plausible inferred coordinate system is:

- `lon(lon)` with cell centers `-179.5, -178.5, ..., 179.5`
- `lat(lat)` with cell centers `-89.5, -88.5, ..., 89.5`

Reasoning:

- 360 by 180 strongly suggests a 1-degree global grid
- the variables are aggregated monthly statistics, so cell-centered gridding is more plausible than edge coordinates
- sampled data windows show sparse-to-zero values in some cells and large oceanic accumulations in others, which is consistent with global ocean binning on a coarse grid

### Sufficient-statistics interpretation

The dataset appears to store sufficient statistics, not monthly means directly. For a variable `x`:

- mean = `sum_x / pixel_count`
- variance = `(sum_x_squared / pixel_count) - mean^2`

This interpretation is strongly supported by the variable naming and by the numeric behavior of the sampled cells.

## Guessed COARDS Metadata

### Global attributes

These are my best guesses for a COARDS-oriented cleanup of `augmented_monthly_stats_01_2024.nc`. “Confidence” refers to the semantic guess, not to whether the attribute is literally present now.

| Attribute | Guessed value | Confidence | Explanation |
| --- | --- | --- | --- |
| `Conventions` | `COARDS` | High | The file is a rectilinear lon-lat grid and can be made COARDS-compliant with coordinate variables and units. |
| `title` | `Monthly sea surface temperature and SST gradient statistics on a 1-degree global grid from Aqua MODIS` | High | Supported by file naming, variable content, and the source orbit product metadata. |
| `institution` | `University of Rhode Island, Graduate School of Oceanography` | High | Matches the accessible orbit-product metadata on the same server. |
| `source` | `Aqua MODIS Level-2 sea surface temperature products processed by URI-GSO` | High | Supported by the orbit collection that feeds the derived product family. |
| `history` | `Monthly accumulation of SST and SST-gradient sufficient statistics from URI-GSO conditioned Aqua MODIS orbit products.` | Medium | This is an inferred processing summary, not a quoted attribute. |
| `references` | `http://www.sstfronts.org` | Medium | The orbit products point to this project site, and the server theme is consistent with it. |
| `comment` | `Augmented files extend the original monthly gradient statistics with SST sufficient statistics and sensor-frame gradient statistics.` | High | Directly supported by the variable-set comparison between `monthly_stats_*` and `augmented_monthly_stats_*`. |
| `grid_type` | `1-degree global lon-lat grid` | High | Strongly implied by `lon=360`, `lat=180`. |
| `temporal_coverage` | `one calendar month per file` | High | Strongly implied by the filename pattern `*_MM_YYYY.nc`. |
| `processing_level` | `derived monthly statistics` | High | The file stores monthly accumulations and sufficient statistics, not swath pixels. |

### Guessed coordinate variables needed for COARDS

The file is not fully COARDS-compliant as served because it has dimensions named `lon` and `lat` but no visible coordinate variables. The most plausible additions would be:

| Variable | Guessed values | Guessed attributes | Explanation |
| --- | --- | --- | --- |
| `lon(lon)` | `-179.5` to `179.5` by `1.0` | `long_name="longitude of grid-cell center"`, `units="degrees_east"` | 360 longitudes on a global 1-degree grid. |
| `lat(lat)` | `-89.5` to `89.5` by `1.0` | `long_name="latitude of grid-cell center"`, `units="degrees_north"` | 180 latitudes on a global 1-degree grid. |

### Variable-by-variable guesses

The tables below are what I would add if I had to retrofit semantic metadata. I use a single `Guessed attributes` column so the format matches the coordinate-variable table more closely. I include `standard_name` only where a plausible CF-style name exists; it is not required by COARDS.

#### Core count variables

| Variable | Guessed attributes | Explanation |
| --- | --- | --- |
| `day_pixel_count` | `long_name="daytime count of valid SST pixels contributing to monthly geographic-frame statistics"`, `units="1"` | Present in both original and augmented files; likely the denominator for SST and geographic-gradient monthly sums. |
| `night_pixel_count` | `long_name="nighttime count of valid SST pixels contributing to monthly geographic-frame statistics"`, `units="1"` | Night counterpart of `day_pixel_count`. |
| `day_as_pixel_count` | `long_name="daytime count of valid along-scan gradient samples contributing to monthly sensor-frame statistics"`, `units="1"` | Added only in augmented files, so it likely belongs to the sensor-frame additions. |
| `night_as_pixel_count` | `long_name="nighttime count of valid along-scan gradient samples contributing to monthly sensor-frame statistics"`, `units="1"` | Night counterpart of `day_as_pixel_count`. |
| `day_at_pixel_count` | `long_name="daytime count of valid along-track gradient samples contributing to monthly sensor-frame statistics"`, `units="1"` | Same reasoning as above, but for the second sensor axis. |
| `night_at_pixel_count` | `long_name="nighttime count of valid along-track gradient samples contributing to monthly sensor-frame statistics"`, `units="1"` | Night counterpart of `day_at_pixel_count`. |

#### SST sufficient statistics

| Variable | Guessed attributes | Explanation |
| --- | --- | --- |
| `day_sum_SST` | `long_name="daytime sum of sea surface temperature within grid cell for the month"`, `units="degree_Celsius"`, `standard_name="sea_surface_temperature"` | Added only in augmented files; dividing by `day_pixel_count` gives a plausible monthly mean SST. |
| `night_sum_SST` | `long_name="nighttime sum of sea surface temperature within grid cell for the month"`, `units="degree_Celsius"`, `standard_name="sea_surface_temperature"` | Night counterpart of `day_sum_SST`. |
| `day_sum_SST_squared` | `long_name="daytime sum of squared sea surface temperature within grid cell for the month"`, `units="degree_Celsius2"` | This is a sufficient-statistics variable. The units are awkward for strict UDUNITS because Celsius is an offset unit; this is a pragmatic guess, not a perfect one. |
| `night_sum_SST_squared` | `long_name="nighttime sum of squared sea surface temperature within grid cell for the month"`, `units="degree_Celsius2"` | Night counterpart of `day_sum_SST_squared`. |

#### Geographic-frame gradient statistics

| Variable | Guessed attributes | Explanation |
| --- | --- | --- |
| `day_sum_eastward_gradient` | `long_name="daytime sum of eastward sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"`, `standard_name="eastward_sea_surface_temperature_gradient"` | Present in original and augmented files; matches the geographic-frame gradient variables in the orbit product. |
| `night_sum_eastward_gradient` | `long_name="nighttime sum of eastward sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"`, `standard_name="eastward_sea_surface_temperature_gradient"` | Night counterpart. |
| `day_sum_northward_gradient` | `long_name="daytime sum of northward sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"`, `standard_name="northward_sea_surface_temperature_gradient"` | Present in original and augmented files; geographic frame. |
| `night_sum_northward_gradient` | `long_name="nighttime sum of northward sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"`, `standard_name="northward_sea_surface_temperature_gradient"` | Night counterpart. |
| `day_sum_magnitude_gradient` | `long_name="daytime sum of geographic-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius km-1"` | Most likely the magnitude derived from eastward and northward components before monthly accumulation. |
| `night_sum_magnitude_gradient` | `long_name="nighttime sum of geographic-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius km-1"` | Night counterpart. |
| `day_sum_eastward_gradient_squared` | `long_name="daytime sum of squared eastward SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_eastward_gradient`. |
| `night_sum_eastward_gradient_squared` | `long_name="nighttime sum of squared eastward SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |
| `day_sum_northward_gradient_squared` | `long_name="daytime sum of squared northward SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_northward_gradient`. |
| `night_sum_northward_gradient_squared` | `long_name="nighttime sum of squared northward SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |
| `day_sum_magnitude_gradient_squared` | `long_name="daytime sum of squared geographic-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_magnitude_gradient`. |
| `night_sum_magnitude_gradient_squared` | `long_name="nighttime sum of squared geographic-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |

#### Sensor-frame gradient statistics added by augmentation

| Variable | Guessed attributes | Explanation |
| --- | --- | --- |
| `day_sum_grad_as_per_km` | `long_name="daytime sum of along-scan sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"` | `as` most plausibly means along-scan, based on the source orbit geometry vocabulary. |
| `night_sum_grad_as_per_km` | `long_name="nighttime sum of along-scan sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"` | Night counterpart. |
| `day_sum_grad_at_per_km` | `long_name="daytime sum of along-track sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"` | `at` most plausibly means along-track. |
| `night_sum_grad_at_per_km` | `long_name="nighttime sum of along-track sea surface temperature gradient within grid cell for the month"`, `units="degree_Celsius km-1"` | Night counterpart. |
| `day_sum_grad_mag_per_km` | `long_name="daytime sum of sensor-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius km-1"` | Likely the magnitude derived from the along-scan and along-track components. |
| `night_sum_grad_mag_per_km` | `long_name="nighttime sum of sensor-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius km-1"` | Night counterpart. |
| `day_sum_grad_as_per_km_squared` | `long_name="daytime sum of squared along-scan SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_grad_as_per_km`. |
| `night_sum_grad_as_per_km_squared` | `long_name="nighttime sum of squared along-scan SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |
| `day_sum_grad_at_per_km_squared` | `long_name="daytime sum of squared along-track SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_grad_at_per_km`. |
| `night_sum_grad_at_per_km_squared` | `long_name="nighttime sum of squared along-track SST gradient within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |
| `day_sum_grad_mag_per_km_squared` | `long_name="daytime sum of squared sensor-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Sufficient-statistics companion to `day_sum_grad_mag_per_km`. |
| `night_sum_grad_mag_per_km_squared` | `long_name="nighttime sum of squared sensor-frame SST gradient magnitude within grid cell for the month"`, `units="degree_Celsius2 km-2"` | Night counterpart. |

## What I would say in plain language

`gradients_by_period` is best understood as a monthly, global, 1-degree summary dataset built from many orbit-level Aqua MODIS SST retrievals. Each file is not a map of SST itself in the ordinary sense. It is a map of monthly sufficient statistics: counts, sums, and sums of squares. Those sufficient statistics make it possible to reconstruct monthly means and variances for SST and for several SST-gradient quantities.

The original `monthly_stats_*` product seems to have focused on geographic-frame gradients only. The `augmented_monthly_stats_*` files add SST itself and a second set of gradients expressed in the sensor frame. My best guess is that those sensor-frame variables use along-scan and along-track directions inherited from the orbit-level source files.

## Description Of The Data And How It Was Generated

### Description of the data

The `gradients_by_period` collection is best described as a monthly archive of gridded summary statistics for SST-front analysis. Each file appears to represent one calendar month on a global `360 x 180` longitude-latitude grid, which is most naturally interpreted as a 1-degree cell-centered grid.

The data are not raw satellite observations and they are not simple monthly mean maps. Instead, each grid cell contains sufficient statistics accumulated from many contributing observations during the month. In the augmented product these statistics include:

- counts of contributing daytime and nighttime observations
- sums and sums of squares of sea surface temperature
- sums and sums of squares of geographic-frame SST gradients
- sums and sums of squares of sensor-frame SST gradients

This structure means a user can derive monthly cellwise means, variances, and standard deviations for SST and multiple gradient quantities without having to revisit all of the underlying orbit files.

Scientifically, the dataset looks designed to support questions such as:

- where strong SST fronts occur most often
- how frontal intensity varies seasonally and interannually
- how daytime and nighttime statistics differ
- how gradient behavior differs between geographic and sensor-oriented reference frames

### Inferred processing pipeline

Given the accessible orbit-level metadata in `SST_Orbits` and the structure of the monthly files, the most plausible generation pipeline is:

1. Start with Aqua MODIS Level-2 SST granules.
   The source orbit product explicitly points to L2 MODIS Aqua SST inputs obtained from NASA Goddard Ocean Color infrastructure.

2. Apply URI/GSO conditioning and quality masking.
   The representative orbit product is titled `Conditioned 1km (L2) MODIS AQUA SST` and describes a `Fix_MODIS_Mask` step that removes or flags low-quality SST values.

3. Build orbit-level derived fields.
   At the orbit level, the server exposes:
   - SST
   - geolocation
   - eastward and northward gradients
   - masks and quality fields
   This strongly suggests that front-oriented derivatives are computed before monthly binning.

4. Compute gradient quantities in at least two reference frames.
   The original monthly product stores only geographic-frame gradients:
   - eastward
   - northward
   - magnitude

   The augmented monthly product adds:
   - along-scan gradient
   - along-track gradient
   - sensor-frame gradient magnitude

   My best guess is that the augmentation step extended the original monthly product with SST statistics and sensor-frame gradient statistics.

5. Separate daytime and nighttime contributions.
   Every major statistic is duplicated in day and night form, so the processing stream must preserve a day/night classification before monthly aggregation.

6. Bin the orbit-level values onto a monthly 1-degree global grid.
   The `lon=360`, `lat=180` structure, plus the large per-cell counts, support a coarse global aggregation step rather than storage on the original swath geometry.

7. Accumulate sufficient statistics within each grid cell.
   For each relevant variable, the file stores some combination of:
   - pixel count
   - sum
   - sum of squares

   That is exactly the information needed to reconstruct moments such as mean and variance for the month.

### What “augmented” most likely means

The direct variable-set comparison is especially useful here.

`monthly_stats_*` contains only:

- pixel counts
- geographic-frame gradient sums
- geographic-frame gradient sums of squares

`augmented_monthly_stats_*` adds:

- SST sums and sums of squares
- separate counts for the added sensor-frame gradient populations
- along-scan and along-track gradient sums
- sensor-frame gradient magnitude sums
- corresponding sums of squares

So the most defensible interpretation is:

the augmented product is an enriched version of the original monthly gradient climatology, extended to support direct reconstruction of SST moments and sensor-frame gradient moments in addition to the original geographic-frame gradient moments.

### Concise product description

If I had to describe `gradients_by_period` in one paragraph, I would say:

`gradients_by_period` is a monthly global 1-degree SST-front statistics product derived from URI/GSO-conditioned Aqua MODIS Level-2 SST orbit data. Rather than storing individual observations, each file stores day/night counts, sums, and sums of squares for SST and several SST-gradient measures, including geographic-frame and likely sensor-frame gradients. The product appears intended to support climatological and statistical analyses of sea surface temperature fronts and their variability through time.

If I had to patch this dataset for discovery and interoperability, I would not start by inventing a large ontology. I would first add:

- explicit `lon` and `lat` coordinate variables
- `Conventions="COARDS"`
- a title and source statement
- `long_name` and `units` for every variable
- a short global comment explaining that the variables are sufficient statistics rather than monthly means

That relatively small metadata layer would make the dataset far easier for both conventional tooling and an AI-assisted characterization pipeline to interpret.

## Limits

This was an exploratory pass, not a complete crawl. I did not enumerate every accessible file, and several collections were unavailable due to `403` responses. Also, pydap-based programmatic access failed with a `503` during one run, so the direct data-serving path may be intermittent.
