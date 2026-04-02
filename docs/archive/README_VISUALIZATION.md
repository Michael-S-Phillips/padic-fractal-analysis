# P-Adic Visualization - Quick Start

**Goal**: Visualize CTX terrain in p-adic quadtree form (Sierpinski-like point cloud)

## Run This Now

```bash
jupyter notebook notebooks/06_quadtree_build_inspect_visualize.ipynb
```

Execute all cells from top to bottom.

---

## What Happens

### Step 1: Build Quadtree (if not cached)
- Loads CTX DEM
- Builds p-adic quadtree (~5-10 minutes)
- Saves to cache for future use

### Step 2: Inspect Structure
- Shows quadtree statistics
- Verifies tree validity
- Displays level distribution

### Step 3: Visualize P-Adic Form
Creates three visualizations:

1. **padic_sierpinski_v2.png** (Like your reference!)
   - Left: Black points on blue (terrain structure)
   - Right: White points on black (binary form)

2. **padic_progressive_v2.png**
   - Shows how detail increases with tree levels
   - 6 panels: Levels 0-6, 0-8, 0-10, 0-11, 0-12, 0-13

3. **padic_comparison_v2.png** (6-panel figure)
   - P-adic structures
   - Original DEM
   - Variance/roughness at level 4

---

## What You'll See

The point cloud visualization shows:
- Each point = center of a quadtree node
- Higher density = more complex terrain
- Sierpinski-like hierarchical pattern
- P-adic ultrametric structure

---

## Key Points

✓ **Quadtree is cached** - no need to rebuild
✓ **Points are real** - not abstract, based on actual terrain
✓ **Hierarchical decomposition** - recursive quadtree subdivision
✓ **P-adic mathematics** - ultrametric distances and hierarchical scaling
✓ **Fractal-like patterns** - emerges from complexity variation

---

## If Something Goes Wrong

### Plot is blank
- Check: Are points being collected? (Cell 4 output)
- Try: Reduce `level_max` to fewer levels
- Check: Scatter parameters (size, color, alpha)

### Memory issues
- Use cached version (already exists)
- Don't rebuild quadtree unless necessary

### Need to rebuild cache
```bash
rm /Volumes/Fangorn/padic_fractal_analysis/cache/*
```

---

## Next

Run the notebook and let me know:
1. Do the visualizations appear?
2. Do you see the Sierpinski-like pattern?
3. Any errors or unexpected behavior?

Then we can:
- Adjust visualization parameters
- Inspect tree structure in detail
- Compare with other complexity measures
- Integrate with analysis pipelines

---

**Status**: Ready to run
**Expected runtime**: 5-15 minutes (depends on if rebuilding quadtree)
**Output files**: 3 PNG visualizations in project root

Go!
