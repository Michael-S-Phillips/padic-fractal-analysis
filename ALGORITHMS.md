# Core Algorithms: P-adic Fractal Analysis of Terrain

This document describes the conceptual computations performed in this repository and provides pseudocode for each major processing stage. The overall goal is to characterize the **fractal complexity** of terrain (specifically Mars DEMs) at every spatial scale simultaneously, using hierarchical data structures inspired by p-adic number theory.

---

## Table of Contents

1. [Overview and Motivation](#1-overview-and-motivation)
2. [Stage 1 — DEM Preprocessing](#2-stage-1--dem-preprocessing)
3. [Stage 2 — Gaussian Pyramid Construction](#3-stage-2--gaussian-pyramid-construction)
4. [Stage 3 — P-adic Quadtree Spatial Index](#4-stage-3--p-adic-quadtree-spatial-index)
5. [Stage 4 — P-adic Wavelet Transform](#5-stage-4--p-adic-wavelet-transform)
6. [Stage 5 — Fractal Density Calculation](#6-stage-5--fractal-density-calculation)
7. [Stage 6 — Ultrametric Distance and Clustering](#7-stage-6--ultrametric-distance-and-clustering)
8. [Stage 7 — P-adic Embedding (Chistyakov Algorithm)](#8-stage-7--p-adic-embedding-chistyakov-algorithm)
9. [Validation: Synthetic Terrain Generation](#9-validation-synthetic-terrain-generation)
10. [Full Pipeline Summary](#10-full-pipeline-summary)

---

## 1. Overview and Motivation

### What is a Digital Elevation Model (DEM)?

A DEM is a 2D raster grid where each cell stores an elevation value. The Jezero crater DEM used here is 20m/pixel resolution.

### What is Fractal Dimension?

Fractal dimension quantifies how "rough" or "complex" a surface is at different scales. For 2D terrain embedded in 3D:
- **D = 2.0** — perfectly smooth plane
- **D = 3.0** — infinitely rough surface filling all of 3D space
- **D ≈ 2.5** — typical natural terrain

The key insight is that fractal terrain obeys a **power law**: variance of elevation scales predictably with the spatial window size. If we measure the variance at window size `r`, then for fractal terrain:

```
variance(r)  ~  r^beta
```

From the slope `beta` of the log-log curve we recover fractal dimension `D = 3 - beta/2`.

### Why P-adic Mathematics?

P-adic numbers provide a natural framework for **hierarchical** analysis. In standard (Euclidean) analysis, distance decreases as you zoom in. In p-adic analysis, the "distance" between two points is defined by their position in a hierarchy: two pixels are "close" if they share a fine-grained common ancestor in a quadtree. This is the **ultrametric** property:

```
d(x, z)  ≤  max( d(x, y), d(y, z) )    [stronger than triangle inequality]
```

This metric captures the terrain's multi-scale structure in a mathematically principled way, enabling efficient O(n log n) algorithms for fractal analysis.

---

## 2. Stage 1 — DEM Preprocessing

**Module:** `src/padic/preprocessing.py`

Before analysis, raw DEMs must be cleaned and normalized. This stage prepares the data for hierarchical processing.

### 2.1 Loading

```
FUNCTION load_dem(filepath):
    open GeoTIFF file
    read band 1 as float32 array
    capture geospatial metadata:
        crs       <- coordinate reference system (Mars IAU2000)
        transform <- pixel-to-world coordinate mapping
        bounds    <- geographic bounding box
        nodata    <- sentinel value for missing data
    RETURN elevation_array, metadata
```

### 2.2 Masking Invalid Pixels

```
FUNCTION mask_invalid_pixels(dem, nodata_value):
    valid_mask = pixels that are:
        - finite (not NaN or Inf)
        - not equal to nodata_value
        - within 5 standard deviations of the mean  [outlier removal]
    
    dem[~valid_mask] = NaN
    RETURN dem, valid_mask
```

### 2.3 Depression Filling (Priority-Flood)

Hydrological "sinks" — pixels lower than all neighbors — can create artifacts in scale-space analysis. We fill them iteratively using morphological erosion:

```
FUNCTION fill_depressions(dem, max_iterations=1000):
    dem_filled = copy(dem)
    
    REPEAT up to max_iterations times:
        dem_eroded = grey_erosion(dem_filled, kernel_size=3)
            # grey_erosion: each pixel takes the minimum of its 3x3 neighborhood
        
        dem_filled = max(dem_filled, dem_eroded)
            # Raise any pixel below its eroded neighborhood back up
        
        IF dem_filled ≈ dem_eroded:   # converged
            BREAK
    
    RETURN dem_filled
```

The intuition: repeatedly propagating the maximum elevation outward from each pixel until no pixel is lower than its surroundings.

### 2.4 Jitter Removal (HiRISE-specific)

HiRISE instruments produce "washboard" striping artifacts along the flight track direction. These are removed with directional median filtering:

```
FUNCTION remove_jitter(dem, direction='vertical', window_size=5):
    FOR each row i in dem:
        dem[i, :] = median( dem[i - w//2 : i + w//2 + 1, :], axis=0 )
            # Replace each row with the median of its vertical neighborhood
    RETURN dem
```

### 2.5 Normalization

```
FUNCTION normalize_dem(dem, method='zscore'):
    IF method == 'zscore':
        dem_norm = (dem - mean(dem)) / std(dem)
    
    ELIF method == 'minmax':
        dem_norm = (dem - min(dem)) / (max(dem) - min(dem))
    
    RETURN dem_norm
```

Normalization is critical: without it, terrain at different absolute elevations would have incomparable variance profiles.

### 2.6 Terrain Attribute Computation

Secondary attributes are derived from the elevation values:

```
FUNCTION compute_slope(dem, cell_size):
    gx, gy = numerical gradient of dem           # finite differences
    slope = arctan( sqrt(gx^2 + gy^2) )          # gradient magnitude
    RETURN slope in degrees

FUNCTION compute_curvature(dem):
    gx, gy = gradient(dem)
    gxx, gxy, gyy = second derivatives
    
    plan_curvature    = -gyx / (gx^2 + gy^2)           # bends left/right
    profile_curvature = -(gxx*gy^2 + 2*gxy*gx*gy + gyy*gx^2) / magnitude^3
    RETURN plan_curvature, profile_curvature
```

---

## 3. Stage 2 — Gaussian Pyramid Construction

**Module:** `src/padic/pyramid.py`

The Gaussian pyramid is the foundational multi-scale data structure. It provides the same terrain viewed at exponentially coarser resolutions, enabling scale-space analysis.

### Concept

Level 0 is the original DEM. Each successive level is smoothed and downsampled by factor 2, so level k has `1/4^k` as many pixels as the base. A DEM of size N×N produces `log2(N) + 1` levels.

```
Level 0:  N × N   pixels  (finest, base resolution)
Level 1:  N/2 × N/2
Level 2:  N/4 × N/4
...
Level k:  N/2^k × N/2^k  (coarsest)
```

### Construction

```
FUNCTION build_pyramid(dem, num_levels):
    levels = [dem]           # Level 0 is the original DEM
    current = dem
    
    FOR k = 1 to num_levels - 1:
        sigma = sqrt(2^(2k) - 2^(2(k-1)))    # Anti-aliasing blur radius
        filtered = gaussian_filter(current, sigma)
        downsampled = filtered[::2, ::2]       # Take every other pixel
        levels.append(downsampled)
        current = downsampled
    
    RETURN levels
```

The sigma formula ensures each level's Gaussian has the correct cumulative smoothing so that level k exactly represents elevation averaged over a `2^k × 2^k` neighborhood.

### Differential (Laplacian) Pyramid

The detail information lost between adjacent levels is captured as a "detail pyramid":

```
FUNCTION compute_differential_pyramid(levels):
    differential = []
    
    FOR k = 0 to num_levels - 2:
        coarse_upsampled = zoom(levels[k+1], factor=2)    # Upsample coarser level
        detail = levels[k] - coarse_upsampled             # What fine level adds
        differential.append(detail)
    
    differential.append(levels[-1])   # Coarsest level appended as-is
    RETURN differential
```

Each differential level captures the terrain "detail" visible only at that particular scale — this is the wavelet interpretation of the pyramid.

### Variance Profile (Key to Fractal Analysis)

For any pixel (i, j), we measure how much elevation varies around it at each pyramid level:

```
FUNCTION compute_variance_profile(i, j, window_size=5):
    variance_profile = array of zeros, length = num_levels
    
    FOR k = 0 to num_levels - 1:
        i_k = i // 2^k              # Map base-resolution coords to level k
        j_k = j // 2^k
        
        window = extract (window_size × window_size) neighborhood
                 centered at (i_k, j_k) in levels[k]
        
        variance_profile[k] = variance(window)
    
    RETURN variance_profile
```

### Fractal Dimension from Variance Profile

```
FUNCTION compute_fractal_slope(variance_profile):
    # Remove zero-variance scales
    valid = indices where variance_profile > 0
    
    log_scales    = log(valid + 1)
    log_variances = log(variance_profile[valid])
    
    # Fit: log_variance = slope * log_scale + intercept
    slope, intercept = linear_regression(log_scales, log_variances)
    
    # Relationship: variance ~ scale^beta  =>  D = 3 - beta/2
    fractal_dimension = 3 - slope / 2
    
    RETURN slope, fractal_dimension
```

---

## 4. Stage 3 — P-adic Quadtree Spatial Index

**Module:** `src/padic/quadtree.py`

The quadtree encodes the DEM as a recursive spatial partition, creating an explicit tree hierarchy whose structure mirrors the p-adic ultrametric.

### Concept

The DEM is recursively split into four quadrants (NW, NE, SW, SE) until individual pixels are reached. Each tree node stores aggregated statistics for its spatial region. This creates a complete quaternary tree of depth `log2(max(height, width))`.

The tree level reflects spatial scale: level 0 is the root (entire DEM), level k covers `2^k × 2^k` pixel blocks.

### Construction (Top-Down Recursive)

```
FUNCTION build_tree(bounds=(0, H, 0, W), level=0, parent=None):
    region = dem[bounds]
    
    node = QuadtreeNode(
        level    = level,
        bounds   = bounds,
        mean     = mean(region),
        variance = var(region),
        min      = min(region),
        max      = max(region),
        roughness = std(region),
        parent   = parent
    )
    
    height = bounds.max_row - bounds.min_row
    width  = bounds.max_col - bounds.min_col
    
    IF height > 1 AND width > 1:       # Can still subdivide
        mid_row = (min_row + max_row) // 2
        mid_col = (min_col + max_col) // 2
        
        child_bounds = [
            (min_row, mid_row, min_col, mid_col),   # NW
            (min_row, mid_row, mid_col, max_col),   # NE
            (mid_row, max_row, min_col, mid_col),   # SW
            (mid_row, max_row, mid_col, max_col),   # SE
        ]
        
        FOR each child_bound in child_bounds:
            child = build_tree(child_bound, level+1, node)
            node.children.append(child)
    
    RETURN node
```

### Ultrametric Distance via Lowest Common Ancestor

Two pixels are "close" in the p-adic sense if their first common ancestor in the tree is at a *deep* level (fine-grained separation). The ultrametric distance is:

```
d_ultrametric(pixel_A, pixel_B) = 2^(-k)

where k = level of the Lowest Common Ancestor (LCA) of pixel_A and pixel_B
```

```
FUNCTION get_ultrametric_distance(i1, j1, i2, j2):
    IF (i1, j1) == (i2, j2):
        RETURN 0.0
    
    node1 = find_leaf_node(i1, j1)
    node2 = find_leaf_node(i2, j2)
    
    ancestors_of_1 = all ancestors of node1 (from leaf to root)
    
    current = node2
    WHILE current is not None:
        IF current is in ancestors_of_1:
            lca_level = current.level
            RETURN 2.0 ^ (-lca_level)
        current = current.parent
```

Pixels in the same 2×2 block are distance `2^(-max_depth)`. Pixels on opposite sides of the DEM share only the root, giving distance `2^0 = 1.0`.

### Locating a Node

```
FUNCTION find_node_at(i, j, target_level=None):
    current = root
    
    WHILE current is not a leaf:
        IF current.level >= target_level:
            RETURN current
        
        mid_row = (current.bounds.min_row + current.bounds.max_row) // 2
        mid_col = (current.bounds.min_col + current.bounds.max_col) // 2
        
        IF i < mid_row AND j < mid_col:  current = NW child
        IF i < mid_row AND j >= mid_col: current = NE child
        IF i >= mid_row AND j < mid_col: current = SW child
        IF i >= mid_row AND j >= mid_col: current = SE child
    
    RETURN current
```

---

## 5. Stage 4 — P-adic Wavelet Transform

**Module:** `src/padic/wavelet.py`

The wavelet transform decomposes the DEM into **approximation** (smooth) and **detail** (fine structure) components at each scale. Unlike standard Fourier analysis, wavelets are localized in both space and scale.

### Forward Transform

```
FUNCTION forward_transform(pyramid):
    approximation_coeffs = [pyramid.levels[0]]   # Start at finest level
    detail_coeffs = []
    
    FOR k = 1 to num_levels - 1:
        coarse = pyramid.levels[k]
        coarse_upsampled = zoom(coarse, factor=2)         # Expand to finer resolution
        coarse_upsampled = trim_to_shape(approximation_coeffs[-1].shape)
        
        detail = approximation_coeffs[-1] - coarse_upsampled
            # Detail = what the fine level adds beyond the coarse prediction
        
        detail_coeffs.append(detail)
        approximation_coeffs.append(coarse)
    
    RETURN approximation_coeffs, detail_coeffs
```

At each level, the detail coefficients capture the terrain texture at that specific scale. Large detail values at fine scales → high-frequency roughness. Large values at coarse scales → regional topographic variation.

### Inverse Transform (Reconstruction)

```
FUNCTION inverse_transform(approximation_coeffs, detail_coeffs):
    current = approximation_coeffs[-1]    # Start at coarsest approximation
    
    FOR k = num_levels - 2 DOWN TO 0:
        current_upsampled = zoom(current, factor=2)
        current_upsampled = trim_to_shape(approximation_coeffs[k].shape)
        current = current_upsampled + detail_coeffs[k]    # Add back detail
    
    RETURN current    # Reconstructed base-resolution DEM
```

### Energy Spectrum

```
FUNCTION compute_energy():
    energy = array of zeros, length = num_levels - 1
    
    FOR k, detail_level in enumerate(detail_coeffs):
        energy[k] = sum(detail_level^2) / num_pixels_at_level_k
            # Mean squared wavelet coefficient = energy at scale k
    
    RETURN energy
```

A flat energy spectrum implies "white noise" (no preferred scale). A power-law decaying spectrum is the signature of fractal terrain.

### Hölder Exponent (Local Regularity)

The Hölder exponent `α` at location (i, j) measures local smoothness. It is estimated from how wavelet coefficients decay across scales:

```
FUNCTION compute_holder_exponent(i, j):
    coefficients_across_scales = []
    scales = []
    
    FOR k, detail_level in enumerate(detail_coeffs):
        i_k = i // 2^k                       # Map pixel to scale-k coordinates
        j_k = j // 2^k
        modulus = |detail_level[i_k, j_k]|   # Absolute wavelet coefficient
        
        IF modulus > 0:
            coefficients_across_scales.append(log2(modulus))
            scales.append(k)
    
    # Fit: log|W(scale)| = alpha * scale + constant
    alpha, _ = linear_regression(scales, coefficients_across_scales)
    RETURN alpha

# Then local fractal dimension:
D_local = clip(3 - alpha, 2.0, 3.0)
```

- `α < 0` → coefficients grow with scale → smooth region (low-frequency dominated)
- `α > 0` → coefficients decay with scale → rough region (multi-scale complexity)

---

## 6. Stage 5 — Fractal Density Calculation

**Module:** `src/padic/fractal_density.py`

Fractal density is the final analysis product: a 2D map assigning each pixel a score in [0, 1] representing how "fractally complex" the terrain is at that location. High-density regions are candidates for rover exploration due to their complex geological structure.

### Three Components

The density metric combines three independent measurements:

#### Component 1: Local Fractal Dimension (Geometric Complexity)

```
FUNCTION compute_local_fractal_dimension(i, j, window_size=5):
    variance_profile = pyramid.compute_variance_profile(i, j, window_size)
    slope, D = pyramid.compute_fractal_slope(variance_profile)
    RETURN D    # Typically in [2.0, 3.0]
```

#### Component 2: Multi-Scale Persistence (Consistency of Scaling)

Measures whether the power-law scaling relationship holds consistently across all scales, not just on average:

```
FUNCTION compute_persistence(i, j, window_size=5, min_r2=0.95):
    variance_profile = pyramid.compute_variance_profile(i, j, window_size)
    valid_scales, valid_variances = remove_zeros(variance_profile)
    
    # Fit power law and measure goodness of fit (R²)
    slope, intercept = linear_regression(log(scales), log(variances))
    y_predicted = slope * log(scales) + intercept
    
    R_squared = 1 - SS_residual / SS_total
    
    # Persistence = fraction of scales consistent with power-law
    consistent_scales = count where R_squared >= min_r2 - 0.2
    persistence = consistent_scales / total_valid_scales
    
    RETURN persistence    # In [0.0, 1.0]
```

A flat plane has D ≈ 2, but persistence = 0 (no fractal scaling at any scale). A true fractal has D > 2 AND high persistence.

#### Component 3: Information Content (Gradient Entropy)

Measures how unpredictable the local gradient directions are — high entropy means terrain complexity comes from all directions equally:

```
FUNCTION compute_information_content(i, j, window_size=5):
    window = dem[i-w:i+w, j-w:j+w]
    
    gx, gy = gradient(window)
    gradient_directions = arctan2(gy, gx)
    
    # Bin directions into 8 compass directions
    bin_counts = histogram(gradient_directions, bins=8, range=[-π, π])
    probabilities = bin_counts / sum(bin_counts)
    
    # Shannon entropy
    entropy = -sum( p * log2(p) for p in probabilities if p > 0 )
    
    # Normalize: max entropy is log2(8) = 3 bits (all directions equally likely)
    information = entropy / log2(8)
    
    RETURN information    # In [0.0, 1.0]
```

#### Combining Into Fractal Density

```
FUNCTION compute_fractal_density():
    density = zeros_like(dem)
    
    FOR each pixel (i, j) in dem:    # Sampled at stride for efficiency
        D = compute_local_fractal_dimension(i, j)
        P = compute_persistence(i, j)
        I = compute_information_content(i, j)
        
        D_normalized = (D - 2.0) / 1.0    # Scale to [0, 1] from [2, 3]
        
        density[i, j] = w_D * D_normalized + w_P * P + w_I * I
    
    density = interpolate_to_full_resolution(density)
    density = density / max(density)    # Normalize to [0, 1]
    
    RETURN density
```

### Fast Variance-Based Density (Alternative)

A computationally cheaper approximation that accumulates normalized contributions from every pyramid level:

```
FUNCTION compute_fast_variance_based_density():
    density = zeros(H, W)
    
    FOR k = 0 to num_levels - 1:
        level_data = pyramid.levels[k]
        level_variance = var(level_data)
        
        # Upsample this level back to base resolution
        upsampled = repeat(level_data, 2^k, axes=[0,1])
        upsampled = trim_to(H, W)
        
        normalized = |upsampled| / level_variance
        density += normalized    # Sum contributions across all scales
    
    density = density / max(density)
    RETURN density    # In [0, 1]
```

---

## 7. Stage 6 — Ultrametric Distance and Clustering

**Module:** `src/padic/ultrametric.py`

### Combined Distance Metric

The full ultrametric distance between two terrain pixels combines their spatial separation (from quadtree hierarchy) with elevation difference:

```
FUNCTION combined_distance(i1, j1, i2, j2):
    d_spatial   = quadtree.get_ultrametric_distance(i1, j1, i2, j2)
                  # = 2^(-k) where k = LCA level in quadtree
    
    d_elevation = |dem[i1,j1] - dem[i2,j2]| / std(dem)
                  # Normalized absolute elevation difference
    
    # Ultrametric max norm — preserves the ultrametric property
    distance = max(w_spatial * d_spatial, w_elevation * d_elevation)
    
    RETURN distance
```

Note: The max operator (rather than sum) preserves the ultrametric triangle inequality.

### Validation of Ultrametric Property

```
FUNCTION validate_ultrametric(distance_matrix):
    violations = 0
    
    FOR all triples (i, j, k):
        d_ij = distance_matrix[i, j]
        d_jk = distance_matrix[j, k]
        d_ik = distance_matrix[i, k]
        
        IF d_ik > max(d_ij, d_jk) + tolerance:
            violations += 1     # Strong triangle inequality violated
    
    RETURN (violations == 0), violation_count, violation_rate
```

### Hierarchical Clustering (Terrain Segmentation)

```
FUNCTION cluster_terrain(distance_matrix, method='single'):
    condensed = squareform(distance_matrix)    # Convert to compact form
    linkage_matrix = scipy_linkage(condensed, method)
        # 'single':   merge clusters by minimum pairwise distance
        # 'complete': merge clusters by maximum pairwise distance
        # 'average':  merge clusters by mean pairwise distance
    RETURN linkage_matrix

FUNCTION segment_by_scale(quadtree, target_level):
    nodes = quadtree.get_all_nodes_at_level(target_level)
    
    segmentation = zeros(H, W)
    FOR cluster_id, node in enumerate(nodes):
        segmentation[node.bounds] = cluster_id
    
    RETURN segmentation    # Each pixel labeled with its quadtree region
```

---

## 8. Stage 7 — P-adic Embedding (Chistyakov Algorithm)

**Module:** `src/padic/padic_embedding.py`

This module implements a direct mathematical mapping from p-adic integers to the complex plane, producing Sierpinski-like fractal visualizations. This is based on Chistyakov (1996).

### Conceptual Background

A p-adic integer `x` is represented as an infinite sequence of base-p digits `[d_0, d_1, d_2, ...]` where `d_0` is the least significant. The **p-adic valuation** `v(x)` is the index of the first nonzero digit — it measures how "divisible by p" the number is.

### The Chistyakov Embedding `T_s^(m)`

```
T_s^(m)(x) = (1 - s^v(x)) / (1 - s)  +  Σ_{n=v(x)}^{l-1}  s^n * χ_n^(m)(x)
```

Where:
- `s` is a complex scaling parameter with `|s| < s_0 = sin(π/p) / (1 + sin(π/p))`
- `v(x)` is the p-adic valuation
- `χ_n^(m)(x) = exp(i * 2π/p * Σ_{k=0}^{m} x_{n-k} * p^{-k})` is an additive character

```
FUNCTION embed_padic_chistyakov(padic_int, p, l, s, m):
    digits = to_base_p(padic_int, p, l)     # [d_0, d_1, ..., d_{l-1}]
    v = first_nonzero_index(digits)          # p-adic valuation
    
    # Base term
    z = (1 - s^v) / (1 - s)
    
    # Character sum
    FOR n = v to l-1:
        chi_arg = 0
        FOR k = 0 to min(m, n):
            chi_arg += digits[n - k] * p^(-k)   # Weighted digit sum
        
        chi = exp(i * 2π * chi_arg / p)          # Complex character value
        z += s^n * chi                           # Contribution at depth n
    
    RETURN z    # Point in complex plane

FUNCTION embed_padic_cloud(integers, p, l, s=None, m=None):
    IF s is None:
        s_0 = sin(π/p) / (1 + sin(π/p))
        s = 0.9 * s_0                           # 90% of maximum stable value
    
    points = [embed_padic_chistyakov(x, p, l, s, m) for x in integers]
    RETURN [(Re(z), Im(z)) for z in points]     # 2D coordinates
```

### Parameter Selection

| Parameter | Effect |
|-----------|--------|
| `p = 2`   | Binary tree; produces Sierpinski square-like patterns |
| `p = 3`   | Ternary tree; produces Sierpinski triangle patterns |
| `s = 0.5` | Produces Sierpinski triangle (Chistyakov Fig 1.10) |
| `s = 0.46`| Produces Cantor set variant (Chistyakov Fig 1.12) |
| `\|s\| > s_0` | Violates isometry; embedding loses fractal structure |

The constraint `|s| < s_0` guarantees that `T_s^(m)` is an **isometry** — it preserves ultrametric distances.

---

## 9. Validation: Synthetic Terrain Generation

**Module:** `src/padic/synthetic_terrain.py`

Before applying algorithms to real Mars data, they are validated against synthetic terrains with **known** fractal dimensions.

### Weierstrass-Mandelbrot Surface

A fractal surface of dimension D is generated by superposing sinusoids with exponentially decaying amplitudes:

```
FUNCTION generate_WM_surface(size, fractal_dimension, num_harmonics=20):
    beta = 2 * (3 - fractal_dimension)    # Scaling exponent
    surface = zeros(size, size)
    
    FOR n = 1 to num_harmonics:
        amplitude = n ^ (-beta / 2)        # Amplitude decreases with frequency
        phase_x   = random in [0, 2π]
        phase_y   = random in [0, 2π]
        frequency = 2^n                    # Exponentially increasing frequency
        
        surface += amplitude * sin(frequency * cos(phase_x) * X
                              + frequency * sin(phase_y) * Y)
    
    surface = (surface - mean(surface)) / std(surface)    # Normalize
    RETURN surface
```

The resulting surface provably has:
- `variance(scale r) ~ r^beta`
- `fractal_dimension = 3 - beta/2`

### Validation

```
FUNCTION validate_dimension(surface):
    FOR scale = 1 to log2(size):
        block_size = 2^scale
        downsampled = surface[::block_size, ::block_size]
        measured_variance = var(downsampled)
    
    slope, _ = log_log_regression(scales, measured_variances)
    estimated_D = 3 - slope / 2
    
    RETURN estimated_D, R_squared
```

### Test Suite (Standard Cases)

| Test Case | Expected D | Description |
|-----------|-----------|-------------|
| `smooth` | 2.2 | Low-complexity terrain |
| `rough` | 2.7 | High-complexity terrain |
| `two_region` | mixed | Smooth + rough halves |
| `hierarchical` | [2.2, 2.5, 2.7] | Nested complexity levels |
| `craters` | ~2.4 | Impact-crater dominated terrain |
| `layers` | 2.3–2.6 | Stratified sedimentary deposits |
| `sublimation` | 2.71 | CO₂ pit-dominated terrain |

---

## 10. Full Pipeline Summary

The complete analysis workflow, from raw GeoTIFF to fractal density map:

```
PIPELINE(geotiff_path):

    # --- STAGE 1: Load and clean data ---
    dem, metadata = load_dem(geotiff_path)
    dem, mask     = mask_invalid_pixels(dem, metadata.nodata)
    dem           = fill_depressions(dem)
    dem           = remove_jitter(dem)           # Only for HiRISE data
    dem           = normalize_dem(dem, 'zscore')

    # --- STAGE 2: Build multi-scale pyramid ---
    pyramid = GaussianPyramid(dem)
        # levels[0] = dem at full resolution
        # levels[k] = dem smoothed and downsampled by 2^k

    # --- STAGE 3: Build spatial hierarchy ---
    quadtree = PadicQuadtree(dem)
        # Recursive quadrant subdivision to individual pixels
        # Each node stores elevation statistics for its region

    # --- STAGE 4: Wavelet decomposition ---
    wavelet = PadicWaveletTransform(pyramid)
    approx_coeffs, detail_coeffs = wavelet.forward_transform()
        # detail_coeffs[k] = terrain texture visible only at scale k
    energy_spectrum = wavelet.compute_energy()
        # energy[k] = mean squared detail at scale k

    # --- STAGE 5: Compute fractal density ---
    calculator = FractalDensityCalculator(dem)
    density = calculator.compute_fractal_density()
        # For each pixel: D_local, persistence, information → combined score
        # Output: 2D array in [0, 1], high = complex terrain

    # --- STAGE 6: Cluster terrain by structure ---
    distance = UltrametricDistance(quadtree, dem)
    D_matrix = distance.compute_distance_matrix(sample_pixels)
    clustering = HierarchicalClustering(D_matrix)
    linkage = clustering.single_linkage()
    segments = TerrainSegmentation(quadtree, dem).segment_by_scale(level=4)

    # --- OUTPUT ---
    RETURN density_map, segments, energy_spectrum
```

### Complexity Summary

| Stage | Algorithm | Time Complexity |
|-------|-----------|----------------|
| Preprocessing | Morphological operations | O(n) |
| Gaussian Pyramid | Iterative filtering + downsample | O(n) |
| Quadtree | Recursive subdivision | O(n log n) |
| Wavelet Transform | Pyramid difference | O(n log n) |
| Fractal Density | Per-pixel variance profiles | O(n log n) |
| Clustering | Single-linkage on sample | O(s² log s) where s = sample size |

Where `n` = total number of DEM pixels.

---

*Reference: D.V. Chistyakov, "Fractal Geometry for Images of Continuous Embeddings of p-Adic Numbers and Solenoids into Euclidean Spaces", Theoretical and Mathematical Physics, Vol. 109, No. 3 (1996)*
