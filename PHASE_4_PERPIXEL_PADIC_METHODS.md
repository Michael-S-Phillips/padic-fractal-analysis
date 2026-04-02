# Phase 4: Per-Pixel P-Adic Fractal Complexity Methods

**Date**: 2025-11-22  
**Status**: PLANNING  
**Objective**: Explore advanced p-adic mathematical approaches for computing per-pixel fractal complexity

---

## Overview

The current implementation computes global/regional fractal density using aggregated wavelet transforms. This phase explores **per-pixel** complexity measures derived from p-adic mathematics, offering finer spatial resolution and different mathematical perspectives on fractal behavior.

---

## Mathematical Foundation

### P-Adic Mathematics Background

P-adic metrics are non-Archimedean distances used to analyze hierarchical data structures:

```
d_p(x,y) = p^(-v_p(x-y))
where v_p(n) = highest power of p dividing n
```

For spatial hierarchies (p=2, quaternary trees):
- Distance = 2^(-level) where level is deepest common ancestor
- Ultrametric property: d(x,z) ≤ max(d(x,y), d(y,z))

### Hierarchical Wavelet Decomposition

Current approach:
1. Build Gaussian pyramid (coarse hierarchy)
2. Compute wavelet detail coefficients
3. Aggregate across scales

New approach:
- Extract per-pixel statistics from quadtree
- Use wavelet coefficients at each spatial location
- Compute p-adic metrics at pixel resolution

---

## Four Novel Per-Pixel Methods

### Method 1: P-Adic Local Roughness (2^-k Scaling)

**Concept**: Measure elevation variability in p-adic balls around each pixel

**Mathematical Basis**:
```
At pixel (i,j), examine p-adic balls of radius 2^(-k):
- k=0: Single pixel
- k=1: 2×2 neighborhood (4 pixels)
- k=2: 4×4 neighborhood (16 pixels)
- k=3: 8×8 neighborhood (64 pixels)
- etc.

Roughness = Σ(variance at radius k) / Σ(2^k)
```

**Advantage**: Exploits natural p-adic scaling (powers of 2)

**Implementation**:
```python
def padic_local_roughness(dem, i, j, max_radius=4):
    """
    Measure roughness at pixel using p-adic ball hierarchy
    """
    roughness = 0.0
    for k in range(max_radius):
        radius = 2**k  # p-adic: powers of 2
        # Extract neighborhood
        # Compute variance
        # Weight by 1/2^k (smaller balls more important)
    return roughness
```

### Method 2: P-Adic Hierarchical Variance Ratio

**Concept**: Measure how elevation variance distributes across p-adic scales

**Mathematical Basis**:
```
For pixel (i,j):
var_k = variance in 2^k × 2^k neighborhood

Normalize by total: ratio_k = var_k / Σ(var_k)

Complexity = Σ(k * ratio_k) (weighted by scale)
or use entropy: H = -Σ(ratio_k * log(ratio_k))
```

**Advantage**: Captures multi-scale structure at pixel level

**Implementation**:
```python
def padic_variance_hierarchy(dem, i, j, max_level=5):
    """
    Compute variance distribution across p-adic scales
    """
    variances = []
    for level in range(max_level):
        radius = 2**level
        window = extract_padic_ball(dem, i, j, radius)
        var = np.var(window)
        variances.append(var)
    
    # Normalize
    total_var = sum(variances)
    ratios = [v / total_var for v in variances]
    
    # Entropy
    entropy = -sum(r * np.log(r) for r in ratios if r > 0)
    return entropy
```

### Method 3: P-Adic Wavelet Spectral Entropy

**Concept**: Use wavelet coefficients from pyramid decomposition to compute per-pixel energy spectrum

**Mathematical Basis**:
```
For each pixel location, compute wavelet coefficient magnitudes 
at each pyramid level k:

W_k(i,j) = wavelet detail coefficient at scale k, pixel (i,j)

Energy spectrum: E_k = |W_k(i,j)|² 

Normalized: p_k = E_k / Σ(E_k)

Spectral Entropy: H = -Σ(p_k * log(p_k))

High entropy = fractal complexity
Low entropy = smooth terrain
```

**Advantage**: Direct mathematical measure of fractal regularity

**Implementation**:
```python
def padic_wavelet_spectral_entropy(pyramid, i, j):
    """
    Compute spectral entropy from wavelet coefficients
    """
    energies = []
    for level in range(pyramid.num_levels):
        # Extract wavelet coefficient at (i,j)
        coeff = pyramid.detail_coeffs[level][i, j]
        energy = coeff ** 2
        energies.append(energy)
    
    # Normalize
    total_energy = sum(energies)
    probs = [e / total_energy for e in energies]
    
    # Shannon entropy
    entropy = -sum(p * np.log(p) for p in probs if p > 0)
    return entropy
```

### Method 4: Ultrametric Fractal Dimension from Quadtree

**Concept**: Use p-adic quadtree to compute local fractal dimension based on ultrametric distances

**Mathematical Basis**:
```
For pixel (i,j) and its p-adic neighbors:

1. Find all pixels at each quadtree level: P_k = {pixels at level k}
2. Compute ultrametric distances: d_k(i, neighbor) = 2^(-k)
3. Count neighbors at each distance: N_k

Fractal dimension approximation:
D ≈ log(N_k) / log(2^k)  (log/log of count vs. distance)

Alternative: Use quadtree variance scaling
- Var(neighbors_at_level_k) scales as 2^(-α*k)
- D ≈ α (related to Hurst exponent)
```

**Advantage**: Pure p-adic perspective using quadtree structure

**Implementation**:
```python
def ultrametric_fractal_dimension(quadtree, dem, i, j):
    """
    Estimate fractal dimension from ultrametric distances
    """
    # Get neighbors at each level
    level_neighbors = []
    for level in range(quadtree.max_depth):
        # Find all nodes at this level overlapping pixel (i,j)
        neighbors = quadtree.get_neighbors_at_level(i, j, level)
        level_neighbors.append(len(neighbors))
    
    # Fit log(count) vs log(distance)
    # D = slope (fractal dimension)
    levels = np.arange(len(level_neighbors))
    distances = 2.0 ** (-levels)  # ultrametric distances
    
    # Linear regression in log-log space
    log_counts = np.log(level_neighbors)
    log_distances = np.log(distances)
    
    slope = np.polyfit(log_distances, log_counts, 1)[0]
    return slope  # Fractal dimension
```

---

## Implementation Strategy

### Step 1: Create `per_pixel_complexity.py` Module

New module with four methods:

```python
class PerPixelComplexity:
    def __init__(self, dem, pyramid, quadtree):
        self.dem = dem
        self.pyramid = pyramid
        self.quadtree = quadtree
        self.height, self.width = dem.shape
    
    def padic_local_roughness(self, max_radius=4):
        """Compute per-pixel roughness using p-adic balls"""
    
    def padic_variance_hierarchy(self, max_level=5):
        """Compute per-pixel hierarchical variance entropy"""
    
    def wavelet_spectral_entropy(self):
        """Compute per-pixel spectral entropy from wavelets"""
    
    def ultrametric_fractal_dimension(self):
        """Compute per-pixel fractal dimension from quadtree"""
```

### Step 2: Integration Points

**Input requirements**:
- DEM (elevation data)
- GaussianPyramid (for wavelet coefficients)
- PadicQuadtree (for ultrametric distances)
- All already computed in existing code

**Output format**:
- 4 output arrays (one per method)
- Shape: (height, width)
- Values: 0-1 normalized or raw fractal dimension

### Step 3: Testing Strategy

**Test 1**: Synthetic terrain
- Compare per-pixel methods to known complexity
- Verify p-adic ball scaling (powers of 2)

**Test 2**: Mars 2020 samples
- Extract values at 4 sample locations
- Compare to current method
- Assess which method best correlates with geological interest

**Test 3**: Visual comparison
- Generate heatmaps for each method
- Overlay on Jezero crater
- Identify high-complexity regions

---

## Expected Outputs

### For Each Method:

**1. Per-Pixel Complexity Map**
- Shape: (1512, 1596) for Jezero
- Values: 0-1 or raw dimension estimates
- 4 independent maps for comparison

**2. Statistical Analysis**
- Mean, std dev, percentiles
- Correlation matrix between methods
- Spearman rank correlation with current density

**3. Validation Results**
- Mars 2020 sample values for each method
- Comparison to expected HIGH complexity
- Ranking of methods by performance

**4. Computational Performance**
- Runtime per method
- Memory usage
- Scalability

---

## Success Criteria

**Technical Success**:
- ✓ All 4 methods implemented
- ✓ Per-pixel outputs generated
- ✓ No NaN or infinity values
- ✓ Consistent with p-adic theory

**Methodological Success**:
- ✓ At least one method shows better agreement with Mars 2020 expectations
- ✓ Methods provide different/complementary perspectives
- ✓ Clear advantages of at least one p-adic approach vs. current method

**Algorithmic Success**:
- ✓ Proper utilization of quadtree structure
- ✓ Correct wavelet coefficient extraction
- ✓ Valid p-adic ball scaling (2^k neighborhoods)

---

## Timeline

**Phase 4A**: Implementation (3-5 days)
- Method 1: Local roughness (1 day)
- Method 2: Variance hierarchy (1 day)
- Method 3: Wavelet spectral entropy (1 day)
- Method 4: Ultrametric dimension (1 day)
- Integration & testing (1 day)

**Phase 4B**: Validation & Analysis (2-3 days)
- Test on synthetic terrain
- Test on Mars 2020 samples
- Generate visualizations
- Compare to current algorithm
- Document findings

**Phase 4C**: Decision (1 day)
- Evaluate which methods work best
- Decide on algorithm investigation approach
- Plan Phase 5 (Gale validation)

---

## Mathematical Rigor

Each method is grounded in p-adic theory:

1. **Local Roughness**: Direct application of p-adic ball hierarchy (2^k scaling)
2. **Variance Hierarchy**: Uses information theory on p-adic scales
3. **Spectral Entropy**: Wavelet decomposition theory (Mallat, Meyer)
4. **Ultrametric Dimension**: P-adic ultrametric distances and fractal dimension theory

All methods produce outputs in [0,1] or meaningful dimensions.

---

## Comparison to Current Method

**Current Approach**:
- Global/regional aggregation
- Single normalized output
- Variances across scales combined uniformly
- Loses spatial resolution

**New Approaches**:
- Per-pixel computation
- Multiple perspectives (4 methods)
- Different weighting of scales
- Full spatial resolution

**Expected Benefits**:
- Finer detail in complexity maps
- Multiple viewpoints may reveal overlooked features
- Better performance on Mars 2020 samples
- Stronger theoretical grounding in p-adic mathematics

---

## Detailed Algorithm Descriptions

### Algorithm 1: P-Adic Local Roughness

```
Input: DEM, pixel (i,j), max_radius=4
Output: roughness ∈ [0,1]

FOR k = 0 TO max_radius:
  radius = 2^k
  Extract (2*radius × 2*radius) window centered at (i,j)
  Compute variance V_k
  Weight = 1.0 / 2^k
  roughness += V_k * weight

Normalize: roughness = roughness / sum(weights)
Return: min(roughness, 1.0)
```

### Algorithm 2: P-Adic Variance Hierarchy Entropy

```
Input: DEM, pixel (i,j), max_level=5
Output: entropy ∈ [0, log(max_level)]

variances = []
FOR k = 0 TO max_level:
  radius = 2^k
  window = extract centered window of size (2^k+1 × 2^k+1)
  var_k = variance(window)
  variances.append(var_k)

total = sum(variances)
FOR each v in variances:
  p_k = v / total
  IF p_k > 0:
    entropy -= p_k * log(p_k)

Return: entropy / log(max_level)  # normalize to [0,1]
```

### Algorithm 3: Wavelet Spectral Entropy

```
Input: GaussianPyramid, detail_coefficients, pixel (i,j)
Output: entropy ∈ [0,1]

energies = []
FOR level = 0 TO pyramid.num_levels-1:
  coeff = detail_coefficients[level][i, j]
  energy = coeff^2
  energies.append(energy)

total_energy = sum(energies)
FOR each e in energies:
  p_level = e / total_energy
  IF p_level > 0:
    entropy -= p_level * log(p_level)

Return: entropy / log(num_levels)  # normalize to [0,1]
```

### Algorithm 4: Ultrametric Fractal Dimension

```
Input: PadicQuadtree, pixel (i,j)
Output: dimension ∈ [2.0, 3.0]  (typically)

neighbor_counts = []
FOR level = 0 TO max_depth:
  distance = 2^(-level)  # ultrametric distance
  
  # Find all pixels covered by quadtree nodes at this level
  # that contain or are near (i,j)
  nodes = quadtree.get_nodes_at_level(i, j, level)
  
  count = 0
  FOR node in nodes:
    count += node.num_pixels  # or just count = 1 per node
  
  neighbor_counts.append(count)

# Linear regression: log(count) vs log(distance)
levels = [0, 1, 2, ..., max_depth]
distances = [2^0, 2^(-1), 2^(-2), ...]
log_distances = log(distances)
log_counts = log(neighbor_counts)

slope, intercept = linear_fit(log_distances, log_counts)
dimension = slope  # or 3 + slope for elevation-based dimension

Return: dimension
```

---

## Next Steps After Implementation

1. **If methods improve over current**: Use best method for Phase 5
2. **If methods are similar**: Combined ensemble for robustness
3. **If methods diverge**: Investigate why and develop hybrid approach
4. **In any case**: Document mathematical foundations for publication

---

**Status**: Ready to implement  
**Next Action**: Begin Method 1 (P-Adic Local Roughness)  
**Estimated Completion**: 1 week (Phase 4A + 4B + 4C)

