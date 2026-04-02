# P-Adic Quadtree Visualization Workflow

**Status**: Ready to use
**Method**: Jupyter notebook + Python scripts
**Purpose**: Build, inspect, and visualize the CTX terrain in p-adic form

---

## Overview

This workflow helps you:
1. **Build** the p-adic quadtree from the DEM (cached for reuse)
2. **Inspect** the tree structure and validate correctness
3. **Visualize** the terrain in p-adic form (Sierpinski-like)

---

## Quick Start

### Option 1: Jupyter Notebook (Recommended)

```bash
cd /Volumes/Fangorn/padic_fractal_analysis
jupyter notebook notebooks/06_quadtree_build_inspect_visualize.ipynb
```

Execute all cells sequentially:
- Cell 1: Setup and imports
- Cell 2: Build/load cached quadtree
- Cell 3: Inspect structure
- Cell 4: Collect node points
- Cell 5: Sierpinski-like visualization
- Cell 6: Progressive refinement
- Cell 7: Multi-panel comparison

**Advantages**:
- Visual feedback as it runs
- Easy to modify and experiment
- See plots inline
- Monitor progress

### Option 2: Python Scripts (For automation)

```bash
cd /Volumes/Fangorn/padic_fractal_analysis/scripts
bash 00_run_all.sh
```

Or run individually:
```bash
python3 01_build_and_save_quadtree.py  # Build and cache
python3 02_inspect_quadtree.py          # Inspect tree
python3 03_visualize_quadtree.py        # Create visualizations
```

**Note**: Requires working scipy (currently has library issues)

---

## What You'll Get

### Visualization 1: Sierpinski-like P-Adic Form
**File**: `padic_sierpinski_v2.png`

Shows the quadtree as a point cloud:
- **Left panel**: Black points on light blue background
- **Right panel**: White points on black background (like your reference)
- Points represent hierarchical centers of quadtree nodes
- Point density shows complexity structure
- Pattern follows p-adic ultrametric hierarchy

### Visualization 2: Progressive Refinement
**File**: `padic_progressive_v2.png`

Six panels showing gradual level refinement:
- Panel 1: Levels 0-6 (coarse)
- Panel 2: Levels 0-8
- Panel 3: Levels 0-10
- Panel 4: Levels 0-11
- Panel 5: Levels 0-12
- Panel 6: Levels 0-13 (fine)

Shows how detail increases with more tree levels.

### Visualization 3: Comprehensive Comparison
**File**: `padic_comparison_v2.png`

Six-panel figure:
1. **P-Adic Structure (0-10)**: Main Sierpinski-like visualization
2. **Extended P-Adic (0-12)**: More detailed version
3. **Point Density**: Heat map showing point concentration
4. **Original DEM**: CTX terrain (grayscale)
5. **Level 4 Variance**: Elevation variance at quadtree level 4
6. **Level 4 Roughness**: Terrain roughness at level 4

---

## Understanding the Quadtree Structure

### What It Shows
The p-adic quadtree hierarchically decomposes the terrain:

```
Level 0: 1 node (root, covers entire DEM)
Level 1: Up to 4 nodes (quadrants)
Level 2: Up to 16 nodes (sub-quadrants)
Level 3: Up to 64 nodes
...
Level N: Up to 4^N nodes
```

### Point Cloud Interpretation
- **Each point**: Center of a quadtree node
- **Position**: (col, row) normalized to [0, 1]
- **Level 0**: Single point at center
- **Level 1**: Four points in quadrants
- **Higher levels**: More points, finer resolution
- **Density pattern**: Shows terrain structure

### Sierpinski-like Pattern
The point cloud resembles a Sierpinski triangle because:
1. Quadtree recursively subdivides space into 4 quadrants
2. Some quadrants may be more densely subdivided than others
3. P-adic hierarchical scaling creates fractal-like patterns
4. High-complexity terrain → more subdivisions → denser points

---

## Inspecting the Quadtree

The inspection output shows:

### Level Distribution
```
Level | Count | Avg Var | Std Var | Min Pix | Max Pix | Avg Pix
  0   |   1   | 123.45  |  0.00   |   1024  |   1024  |  1024.0
  1   |   4   |  54.32  |  32.15  |   256   |   256   |   256.0
  2   |  16   |  21.87  |  15.64  |   64    |   64    |    64.0
  ...
```

**What it means**:
- **Count**: Number of nodes at this level
- **Avg Var**: Average elevation variance (terrain roughness)
- **Std Var**: How much variance varies between nodes
- **Pix**: Number of pixels each node covers

### Variance Progression
How variance changes as you go up the tree:
- Leaf nodes (level 0): Variance = 0 (single pixel)
- Level 1: Small variance (2×2 blocks)
- Higher levels: Larger variance (coarser resolution)
- Root node: Maximum variance (entire DEM)

**Key insight**: Variance tells you about local complexity!

---

## Cache Management

### Location
```
/Volumes/Fangorn/padic_fractal_analysis/cache/
├── quadtree.pkl          # Serialized quadtree (large ~100+ MB)
├── dem_clean.npy         # Preprocessed DEM
└── dem_metadata.txt      # Basic info
```

### Reusing Cached Data
```python
import pickle
import numpy as np
from pathlib import Path

cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')

# Load quadtree
with open(cache_dir / 'quadtree.pkl', 'rb') as f:
    qtree = pickle.load(f)

# Load DEM
dem_clean = np.load(cache_dir / 'dem_clean.npy')

# Now use qtree and dem_clean
print(f"Max depth: {qtree.max_depth}")
print(f"DEM shape: {dem_clean.shape}")
```

### Cache Size
- **quadtree.pkl**: ~100-200 MB (depends on DEM size)
- **dem_clean.npy**: ~10-20 MB
- **Total**: ~120-220 MB

Delete cache if you want to rebuild:
```bash
rm /Volumes/Fangorn/padic_fractal_analysis/cache/*.pkl
rm /Volumes/Fangorn/padic_fractal_analysis/cache/*.npy
```

---

## Troubleshooting

### Blank Visualization
**Problem**: Points don't show up in plot
**Solutions**:
1. Check that points are being collected:
   ```python
   print(f"Total points: {sum(len(p) for p in points_all.values())}")
   ```
2. Verify scatter parameters are correct (size, alpha, color)
3. Check axes limits and inversion

### Memory Issues
**Problem**: Python runs out of memory when building quadtree
**Solutions**:
1. Use cached version (don't rebuild)
2. Load cache in smaller chunks if possible
3. Consider downsampling DEM first

### Slow Visualization
**Problem**: Plotting takes too long
**Solutions**:
1. Reduce `level_max` to fewer levels
2. Use `rasterized=True` in scatter plots
3. Save and view PNG instead of showing interactive plot

---

## Interpreting the Visualizations

### Color and Alpha
- **Alpha (transparency)**: Increases at deeper levels
  - Lower levels (coarse): More transparent
  - Higher levels (fine): More opaque
- **Size**: Decreases at deeper levels
  - Lower levels: Larger points
  - Higher levels: Smaller points

### Spatial Patterns
- **Dense clusters**: High-complexity terrain
- **Sparse areas**: Smooth, simple terrain
- **Hierarchical nesting**: P-adic structure preservation

### Comparison with Reference
Your reference figure shows:
- Left: Sierpinski triangle (abstract pattern)
- Right: White on black (binary visualization)

Our visualization:
- Shows **actual CTX terrain structure**
- Points represent **real hierarchical decomposition**
- Pattern reflects **actual spatial complexity**
- Similar fractal-like structure due to **p-adic mathematics**

---

## Mathematical Background

### P-Adic Ultrametric Structure
The quadtree encodes p-adic ultrametric distances:
```
d(pixel_1, pixel_2) = 2^(-level)
where level = deepest tree level containing both pixels
```

### Hierarchy Visualization
P-adic form shows:
1. **Spatial partitioning**: Quadtree recursive division
2. **Ultrametric distances**: Level-based scaling
3. **Terrain complexity**: Variance distribution
4. **Fractal properties**: Self-similarity at multiple scales

### Why Sierpinski-like?
```
Sierpinski:       P-Adic Terrain:
  /\                  *
 /  \            *  *  *  *
/____\         *  *    *  *
      \        ...hierarchical points...
```

Both are generated by recursive subdivision + selective inclusion based on complexity.

---

## Next Steps

### After Visualization
1. **Inspect the generated images**
   - Do they show expected patterns?
   - Is the Sierpinski-like structure visible?
   - Does density match complexity expectations?

2. **Modify if needed**
   - Change `level_max` values
   - Adjust point size or alpha
   - Try different colormaps

3. **Integrate with analysis**
   - Use quadtree for fractal dimension
   - Compare with other complexity measures
   - Validate against geological expectations

---

## Files Created

### Python Scripts
```
scripts/
├── 00_run_all.sh                           # Master script
├── 01_build_and_save_quadtree.py           # Build and cache
├── 02_inspect_quadtree.py                  # Inspect structure
└── 03_visualize_quadtree.py                # Create visuals
```

### Jupyter Notebooks
```
notebooks/
└── 06_quadtree_build_inspect_visualize.ipynb  # Complete workflow
```

### Generated Visualizations
```
/results/
├── padic_sierpinski_v2.png                 # Main Sierpinski form
├── padic_progressive_v2.png                # Progressive refinement
└── padic_comparison_v2.png                 # 6-panel comparison
```

---

## Summary

You now have a complete workflow to:
1. ✓ **Build** a p-adic quadtree from CTX DEM
2. ✓ **Cache** it for fast reuse
3. ✓ **Inspect** structure and validity
4. ✓ **Visualize** in p-adic form (Sierpinski-like)

**Recommended**: Use the Jupyter notebook for interactive exploration and to debug/fix any visualization issues.

---

**Ready to run**: `jupyter notebook notebooks/06_quadtree_build_inspect_visualize.ipynb`
