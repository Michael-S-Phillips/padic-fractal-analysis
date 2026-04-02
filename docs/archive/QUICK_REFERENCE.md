# P-adic Fractal Analysis: Quick Reference

## Files at a Glance

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `src/padic/preprocessing.py` | DEM loading & cleanup | 300 | ✅ |
| `src/padic/pyramid.py` | Multi-scale decomposition | 250 | ✅ |
| `src/padic/quadtree.py` | Spatial indexing | 400 | ✅ |
| `src/padic/ultrametric.py` | Distance & clustering | 350 | ✅ |
| `src/padic/wavelet.py` | Wavelet transforms | 350 | ✅ |
| `src/padic/fractal_density.py` | Complexity metrics | 300 | ✅ |
| `src/padic/synthetic_terrain.py` | Test data generation | 350 | ✅ |
| `src/padic/visualization.py` | Output & visualization | 300 | ✅ |
| **Total Code** | **8 modules** | **2,500+** | **✅** |

## Basic Usage Examples

### Load and Preprocess Mars DEM
```python
from padic import preprocessing, pyramid, fractal_density

# Load data
dem, metadata = preprocessing.load_dem('mars_dem.tif')

# Clean and normalize
dem_clean, stats = preprocessing.preprocess_dem(dem)

# Build pyramid
pyr = pyramid.GaussianPyramid(dem_clean)

# Compute density
calc = fractal_density.FractalDensityCalculator(dem_clean)
density = calc.compute_fractal_density()

# Export results
from padic import visualization
exporter = visualization.GeoTIFFExporter()
exporter.save_density_tiff(density, 'output.tif',
                          transform=metadata['transform'],
                          crs=metadata['crs'])
```

### Generate Test Terrain
```python
from padic import synthetic_terrain

# Create smooth terrain (D=2.2)
gen = synthetic_terrain.WeierstrrassMandelbrot(256, 2.2)
terrain = gen.generate(num_harmonics=15)

# Validate dimension
est_dim, r2 = gen.validate(terrain)
print(f"Generated D={est_dim:.3f} (target 2.2)")
```

### Visualize Results
```python
from padic import visualization

fig = visualization.FractalDensityVisualizer.plot_dem_with_density_overlay(
    dem, density, figsize=(14, 6)
)
visualization.FractalDensityVisualizer.save_figure(fig, 'analysis.png')
```

## Key Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `GaussianPyramid` | pyramid | Multi-scale terrain |
| `PadicQuadtree` | quadtree | Spatial indexing |
| `UltrametricDistance` | ultrametric | Distance computation |
| `HierarchicalClustering` | ultrametric | Terrain segmentation |
| `PadicWaveletTransform` | wavelet | Wavelet decomposition |
| `FractalDensityCalculator` | fractal_density | Complexity metrics |
| `WeierstrrassMandelbrot` | synthetic_terrain | Test data |
| `FractalDensityVisualizer` | visualization | Plotting |
| `GeoTIFFExporter` | visualization | GIS output |

## Complexity Analysis

```
DEM preprocessing:      O(n)
Gaussian pyramid:       O(n)
Quadtree building:      O(n log n)
Wavelet transform:      O(n log n)
Fractal density:        O(n log n)
─────────────────────────────────
TOTAL PIPELINE:         O(n log n)  ✓ Scalable to Mars-scale
```

## Performance Estimates

```
10 km² (HiRISE, 1m):    ~2-5 minutes
50 km² (Jezero):        ~15-30 minutes
150 km² (Gale):         ~45-90 minutes
Global MOLA (500m):     ~6 hours
```

## Test Execution

### Synthetic Validation
```bash
# Run all tests
python tests/run_validation.py

# Run notebook
jupyter notebook notebooks/01_synthetic_terrain_validation.ipynb
```

### Expected Results
- ✓ Smooth terrain: low density (D=2.2)
- ✓ Rough terrain: high density (D=2.7)
- ✓ Two regions: clear boundary detection
- ✓ Mars features: correct identification

## Critical Imports

```python
# Core analysis
from padic import preprocessing, pyramid, fractal_density

# Spatial operations
from padic import quadtree, ultrametric

# Advanced analysis
from padic import wavelet, synthetic_terrain

# Output
from padic import visualization
```

## DEM Format Support

**Input**:
- GeoTIFF (.tif, .tiff) ✓
- HDF5 (.h5) ✓
- Raw arrays (NumPy) ✓

**Output**:
- GeoTIFF with metadata ✓
- Multi-band GeoTIFF ✓
- PNG visualization ✓

## Success Criteria

### Dimension Accuracy
```
|est_dimension - true_dimension| / true_dimension < 5%
```

### Segmentation Quality
```
Separation error < 10%  (for two-region detection)
```

### Density Ordering
```
density_rough > density_smooth  (always, if algorithm correct)
Ratio > 1.2
```

## Documentation Map

| Document | Content | For |
|----------|---------|-----|
| `README.md` | Full user guide | Users & researchers |
| `CLAUDE.md` | Implementation details | Developers |
| `VALIDATION_GUIDE.md` | Test procedures | QA & validation |
| `IMPLEMENTATION_SUMMARY.md` | Project overview | Project managers |
| `QUICK_REFERENCE.md` | Quick lookup | Everyone (this file) |

## Contact & Support

**For technical questions:**
- See `CLAUDE.md` (implementation)
- See `README.md` (usage)
- Review code comments (mathematical details)

**For validation issues:**
- See `VALIDATION_GUIDE.md`
- Check `tests/` directory
- Review `IMPLEMENTATION_SUMMARY.md`

## Common Tasks

### Compute density for a single region
```python
calc = FractalDensityCalculator(dem_clean)
density = calc.compute_fast_variance_based_density()  # Fast method
```

### Compare multiple terrains
```python
for dem_file in dem_files:
    dem, meta = preprocessing.load_dem(dem_file)
    dem_clean, _ = preprocessing.preprocess_dem(dem)
    calc = FractalDensityCalculator(dem_clean)
    density = calc.compute_fractal_density()
    # ... process results
```

### Generate publication figures
```python
fig = FractalDensityVisualizer.plot_dem_with_density_overlay(dem, density)
FractalDensityVisualizer.save_figure(fig, 'figure.pdf', dpi=300)
```

### Create test suite
```python
tests = TestSuite.create_test_cases()
for name, test_data in tests.items():
    result = run_algorithm(test_data['surface'])
    report = generate_validation_report(result, test_data)
```

## Key Equations

### Fractal Dimension
```
D = 3 - β/2    where variance ~ scale^β
```

### Ultrametric Distance
```
d(x,z) ≤ max{d(x,y), d(y,z)}  [strong triangle inequality]
```

### Fractal Density
```
ρ(x,y) = w₁·D_local(x,y) + w₂·P(x,y) + w₃·I(x,y)
```

## Development Status

```
Core implementation:    ✅ Complete (2,500+ lines)
Synthetic validation:   ✅ Ready (8 test cases)
Real Mars validation:   ⏳ Pending (data acquisition)
Deployment:             📋 Planned (Q2 2026)
```

## Quick Checklist

Before deploying to Mars rover:
- [ ] All 8 synthetic tests pass
- [ ] Dimension accuracy < 5% error
- [ ] Jezero crater validation > 70% precision
- [ ] Gale crater validation > 80% recall
- [ ] Expert panel agreement κ > 0.5
- [ ] GeoTIFF output verified
- [ ] Performance benchmarks met
- [ ] Documentation complete

---

**Quick Ref v0.1** | Last updated: 2025-11-22 | [Full docs →](README.md)
