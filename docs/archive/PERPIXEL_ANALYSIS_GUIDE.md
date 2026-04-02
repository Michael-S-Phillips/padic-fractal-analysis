# Per-Pixel P-Adic Fractal Complexity Maps

## Overview

This analysis extends the grid-based p-adic terrain analysis to **full resolution**, computing fractal complexity metrics for every pixel in the CTX DEM (2,413,152 pixels total).

**Key Innovation**: Instead of dividing terrain into regions, we analyze the local elevation structure around each pixel, revealing spatial patterns of terrain complexity.

---

## Method

### For Each Pixel at Position (x, y):

1. **Extract Local Window**
   - 3×3, 5×5, or 7×7 neighborhood of elevation values
   - Window size determines scale of analysis
   - Edge pixels use available neighborhood (truncated window)

2. **Normalize Elevation**
   - Min-max normalization to [0, 1] within window
   - Preserves relative structure while enabling p-adic encoding

3. **P-Adic Embedding**
   - Convert normalized elevations to p-adic integers (0 to 3^l - 1)
   - Apply Chistyakov algorithm: T_s^(m)(x) with s=0.5, m=0, p=3
   - Generate l=3 (27 possible values) embedding points in complex plane

4. **Compute Metrics**
   - **Complexity**: Shannon entropy of elevation distribution
     - High: Diverse elevations in window (rugged terrain)
     - Low: Similar elevations in window (smooth terrain)
   - **Clustering**: Density coefficient of variation in embedding
     - High: Points clustered in Sierpinski structure
     - Low: Points uniformly distributed
   - **Distance**: Mean pairwise distance between embedding points
     - High: Widely spread embedding structure
     - Low: Compressed embedding space

---

## Data Generated

### Per-Pixel Maps (3 window sizes × 3 metrics = 9 files)

#### Window Size 3×3 (Finest Local Scale)
```
perpixel/
├── perpixel_complexity_w3.npy      [1512 × 1596]  Min local entropy
├── perpixel_clustering_w3.npy
└── perpixel_distance_w3.npy
```

#### Window Size 5×5 (Standard Local Scale) ✓ **Recommended**
```
├── perpixel_complexity_w5.npy      [1512 × 1596]  Balanced scale
├── perpixel_clustering_w5.npy
└── perpixel_distance_w5.npy
```

#### Window Size 7×7 (Broader Local Scale)
```
├── perpixel_complexity_w7.npy      [1512 × 1596]  Coarser features
├── perpixel_clustering_w7.npy
└── perpixel_distance_w7.npy
```

### Generated From Scripts

| Script | Input | Output |
|--------|-------|--------|
| `perpixel_fractal_maps.py` | DEM 1512×1596 | 9 .npy arrays (cache/perpixel/) |
| `visualize_perpixel_maps.py` | Per-pixel arrays | 2 .png visualizations (results/) |

---

## Visualization Outputs

### Figure 04: Detailed Window Analysis (3 versions: w3, w5, w7)
```
File: 04_perpixel_fractal_w{3,5,7}.png

Layout:
  Top-Left:     DEM Hillshade (reference)
  Top-Middle:   Complexity Map (hot colormap)
  Top-Right:    Clustering Map (viridis colormap)
  Bottom-Left:  Distance Map (plasma colormap)
  Bottom-Right: Statistics panel
```

**File Size**: ~2-3 MB each at 150 dpi
**Interpretation**:
- Red regions (complexity): Rugged/rough terrain
- Blue regions (clustering): Strong Sierpinski structure
- Purple regions (distance): Spread-out embeddings

### Figure 05: Multi-Scale Comparison
```
File: 05_perpixel_multiscale_comparison.png

Layout:
  Row 1: Complexity at w3, w5, w7
  Row 2: Clustering at w3, w5, w7
```

**Insights**:
- Shows how metrics change with analysis window size
- Reveals scale-dependent terrain organization
- Smaller windows capture micro-topography
- Larger windows capture meso-scale features

---

## Interpretation Guide

### Complexity (Entropy)

**High Complexity (Red)**
- Diverse elevation range in local window
- Indicates rough, varied terrain
- Often corresponds to:
  - Impact crater edges
  - Erosional scarps
  - Ridge systems
  - Valley walls

**Low Complexity (Dark)**
- Similar elevations in local window
- Indicates smooth, uniform terrain
- Often corresponds to:
  - Crater floors
  - Smooth plains
  - Sediment-filled basins
  - Gradual slopes

### Clustering (Density CV)

**High Clustering (Blue-Purple)**
- P-adic points concentrated in Sierpinski pattern
- Strong hierarchical organization
- Suggests:
  - Natural terrain regionalization
  - Sharp topographic boundaries
  - Discrete terrain units

**Low Clustering (Yellow-Green)**
- P-adic points spread uniformly
- Weak hierarchical structure
- Suggests:
  - Gradual elevation transitions
  - Smooth topography
  - Homogeneous terrain

### Distance (Mean Pairwise Distance)

**Large Distance (Purple)**
- Wide separation in embedding space
- Complex elevation relationships
- Indicates:
  - Diverse terrain types
  - High elevation range
  - Complex morphology

**Small Distance (Yellow)**
- Close clustering in embedding space
- Simple elevation relationships
- Indicates:
  - Uniform terrain
  - Limited elevation range
  - Simple morphology

---

## Interactive Notebook

**File**: `notebooks/18_perpixel_fractal_maps.ipynb`

### Cells Included:

1. **Setup & Loading**
   - Verifies per-pixel data availability
   - Lists generated .npy files

2. **Method Overview**
   - Explains per-pixel embedding process
   - Shows pseudocode

3. **Load Per-Pixel Maps**
   - Dynamically loads available arrays
   - Handles partial completion gracefully

4. **Complexity Map (Window 5×5)**
   - 2×2 panel showing DEM + 3 metrics
   - Full statistics and correlation analysis

5. **Multi-Scale Comparison**
   - Side-by-side comparison of all window sizes
   - Cross-scale statistics

6. **High-Complexity Regions**
   - Identifies top 10% complexity pixels
   - Analyzes clustering in high-complexity zones
   - Creates overlay visualizations

---

## Computational Details

### Processing Time Estimate
- 2,413,152 pixels total
- ~0.1 ms per pixel (with p-adic embedding)
- **Total**: ~4-8 hours for all 3 window sizes
  - Window 3×3: ~2 hours
  - Window 5×5: ~3 hours
  - Window 7×7: ~4 hours

### Memory Requirements
- Input DEM: 9.65 MB
- Per output array: ~9.2 MB (float32)
- Total outputs: 82.8 MB (9 arrays)
- Peak memory: ~100 MB

### Storage
- All files cached in `cache/perpixel/`
- Visualizations saved to `results/`
- Each visualization: 2-3 MB at 150 dpi

---

## Use Cases

### Scientific Analysis

**1. Terrain Classification**
- Use complexity + clustering to classify terrain types
- Low complexity, high clustering = smooth structured terrain
- High complexity, low clustering = rugged unstructured terrain

**2. Feature Detection**
- Edges/boundaries: High complexity + high clustering
- Basin floors: Low complexity
- Ridge systems: High complexity + low clustering

**3. Scale-Dependent Organization**
- Compare w3 vs w5 vs w7 to understand multi-scale structure
- Identify features at specific scales
- Study hierarchical terrain organization

**4. Crater Analysis**
- Map crater edge complexity (high)
- Identify ejecta blankets (medium)
- Locate crater floors (low)

### Practical Applications

**Landing Site Assessment**
- Complexity map → roughness for rover navigation
- Clustering map → natural terrain regions
- Distance map → topographic diversity

**Regional Geology**
- Group pixels by p-adic metrics
- Identify similar terrain types across region
- Understand process signatures

**Climate/Erosion Models**
- Complexity correlates with erosion susceptibility
- Validate terrain evolution predictions
- Study slope stability

---

## Comparison to Traditional Metrics

| Metric | TRI | TPI | Slope | P-Adic |
|--------|-----|-----|-------|--------|
| **Window size** | Fixed | Fixed | Local gradient | Configurable (3-7 px) |
| **Complexity measure** | Roughness | Position | Steepness | Entropy + Clustering |
| **Hierarchy** | No | No | No | Yes (Sierpinski) |
| **Scale-aware** | Limited | Limited | No | Yes |
| **Elevation-independent** | No | No | No | Yes |
| **Computational** | Fast | Fast | Very fast | Moderate |

**Advantages of P-Adic**:
- ✓ Multi-scale naturally
- ✓ Captures structural organization
- ✓ Independent of elevation magnitude
- ✓ Hierarchical decomposition
- ✓ Combines geometry with information theory

---

## Code Structure

### Main Scripts

**`perpixel_fractal_maps.py`** (Data Generation)
```python
def generate_perpixel_maps(dem_path, output_dir, window_sizes=[3,5,7], l=3)
    ├── Load DEM
    ├── For each pixel:
    │   ├── Extract window
    │   ├── Normalize elevation
    │   ├── Embed in p-adic space
    │   ├── Compute metrics
    │   └── Store in result maps
    └── Save .npy files
```

**`visualize_perpixel_maps.py`** (Visualization)
```python
def visualize_perpixel_maps(cache_dir, results_dir, dem_path)
    ├── Wait for .npy files
    ├── Load per-pixel arrays
    ├── Create figure 04 (3 versions)
    ├── Create figure 05 (comparison)
    └── Save PNG visualizations
```

---

## File Locations

```
/Volumes/Fangorn/padic_fractal_analysis/

├── scripts/
│   ├── perpixel_fractal_maps.py      ← Data generation (running)
│   └── visualize_perpixel_maps.py    ← Visualization

├── cache/
│   └── perpixel/                     ← Output arrays (generating)
│       ├── perpixel_complexity_w3.npy
│       ├── perpixel_complexity_w5.npy
│       ├── perpixel_complexity_w7.npy
│       └── (+ clustering & distance variants)

├── results/
│   ├── 04_perpixel_fractal_w3.png    ← Visualizations (pending)
│   ├── 04_perpixel_fractal_w5.png
│   ├── 04_perpixel_fractal_w7.png
│   └── 05_perpixel_multiscale_comparison.png

└── notebooks/
    └── 18_perpixel_fractal_maps.ipynb ← Interactive analysis
```

---

## Next Steps

### While Data Generates:
1. Review notebook `18_perpixel_fractal_maps.ipynb`
2. Understand per-pixel method (cells 1-2)
3. Read this guide (you're doing it!)
4. Prepare for visualization (cell 3)

### After Data Complete:
1. Run notebook cell 4 → Complexity maps
2. Run notebook cell 5 → Multi-scale comparison
3. Run notebook cell 6 → High-complexity analysis
4. View results in `results/04_perpixel_fractal_*.png`
5. View comparison in `results/05_perpixel_multiscale_comparison.png`

### Extended Analysis:
1. Correlate complexity with elevation (geology)
2. Identify specific terrain types
3. Compare regions (within and between craters)
4. Validate with geological maps
5. Export high-complexity regions for study

---

## Status

**Current**: Per-pixel maps generating in background
- Process ID: 3b9a06
- ETA: 4-8 hours depending on window sizes
- Progress: Check `cache/perpixel/` directory for .npy files

**Next**: Automatic visualization generation once data is ready
- Monitors for completion of .npy files
- Generates PNG visualizations
- Updates results/ directory

**Notebook**: Ready to use (interactive, handles partial data)

---

## Reference

- **Algorithm**: Chistyakov (1996) p-adic embedding
- **Implementation**: `src/padic/padic_embedding.py`
- **Parameters**: p=3, l=3, s=0.5, m=0 (corrected)
- **Theory**: Sierpinski carpets, p-adic numbers, fractal geometry
- **Application**: Terrain complexity assessment

---

**Generated**: 2025-11-24
**Status**: Per-pixel analysis in progress ✓
**Estimated Completion**: ~2-4 hours from start time

