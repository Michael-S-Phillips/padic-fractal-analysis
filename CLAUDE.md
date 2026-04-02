# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**padic_fractal_analysis** is a data-driven analysis framework for studying fractal properties in terrain using p-adic mathematics. The project currently focuses on Mars topography data from the Jezero crater landing site (Mars 2020 rover mission).

### Current State
This is an early-stage project with directory structure and geospatial data in place, but no source code implemented yet. The `/src/` and `/notebooks/` directories are empty and awaiting code development.

### Data Resources
- **Mars DTM Data**: GeoTIFF raster (9.6 MB) - Jezero crater Digital Terrain Model at 20m resolution
- **Metadata**: USGS FGDC-compliant XML with accuracy specs (9.6m horizontal, 3.8m vertical)
- **Source**: USGS Astrogeology Science Center Mars 2020 program

## Project Structure

```
padic_fractal_analysis/
├── data/                    # Geospatial data files (GeoTIFF, XML metadata)
├── src/                     # Python source code (modules, utilities)
├── notebooks/               # Jupyter notebooks for analysis and computation
└── CLAUDE.md               # This file
```

## Development Setup

### Initial Setup
When starting development on this project, establish:
1. **Python environment**: Create a virtual environment with `python -m venv venv`
2. **Package management**: Set up `pyproject.toml` or `requirements.txt` with project dependencies
3. **Core dependencies** (suggested for p-adic math and geospatial work):
   - `numpy` - numerical computing
   - `scipy` - scientific computing
   - `rasterio` - reading/writing GeoTIFF files
   - `geopandas` - geospatial data handling
   - `jupyter` - interactive notebooks
   - `matplotlib` or `folium` - visualization

### Key Implementation Areas (To Be Developed)

**src/ Module Structure** (suggested):
- `src/padic/` - p-adic number theory and fractal computation
- `src/terrain/` - terrain analysis and processing
- `src/io/` - data loading and export utilities

**notebooks/ Analysis Path** (suggested):
- Data exploration and visualization
- p-adic fractal dimension calculations
- Terrain feature extraction
- Comparative analysis across regions

## Development Workflow (When Code Exists)

### Running Analysis
Once notebooks and modules are created:
- `jupyter notebook` - Launch interactive environment for exploration
- Notebooks should document analysis steps and visualizations

### Testing (When Test Suite Exists)
Setup test framework and add tests to validate:
- P-adic mathematics implementations
- Terrain processing algorithms
- Data I/O operations

### Code Quality (When CI/Linting Added)
- Use `black` or `ruff` for formatting
- Use `mypy` for type checking (if using type hints)
- Use `pytest` for unit testing

## Important Notes for Development

### Geospatial Data Handling
- The GeoTIFF file uses Equirectangular projection with MOLA datum (Mars-specific CRS)
- Use `rasterio` with proper CRS handling for Mars data
- Metadata XML contains important accuracy information for validation

### P-adic Mathematics
- This is a specialized mathematical domain - ensure implementations reference:
  - Proper p-adic norms and metrics
  - Fractal dimension calculations in p-adic spaces
  - Connection to traditional fractal analysis methods

### Git and Version Control
- This repository is not yet initialized with git - consider running `git init` and creating `.gitignore`
- Add standard Python ignores: `__pycache__/`, `.ipynb_checkpoints/`, `*.pyc`, `.venv/`

## Implementation Status

### Completed (Core Infrastructure)
- ✅ Full package structure with 8 core modules
- ✅ `preprocessing.py` - DEM loading, artifact removal, terrain attributes
- ✅ `pyramid.py` - Gaussian pyramid with O(n) storage
- ✅ `quadtree.py` - P-adic quadtree spatial index with ultrametric encoding
- ✅ `ultrametric.py` - Distance metrics and hierarchical clustering
- ✅ `wavelet.py` - P-adic wavelet transforms (O(n log n))
- ✅ `fractal_density.py` - Complexity metrics and density calculation
- ✅ `synthetic_terrain.py` - Test case generation for validation
- ✅ `visualization.py` - GeoTIFF export and analysis plotting
- ✅ `pyproject.toml` - Complete dependency configuration
- ✅ `README.md` - Comprehensive documentation

### Architecture Overview

```
padic/
├── __init__.py                 # Package initialization
├── preprocessing.py            # DEM I/O and preprocessing
├── pyramid.py                  # GaussianPyramid class
├── quadtree.py                 # PadicQuadtree spatial index
├── ultrametric.py              # Distance/clustering algorithms
├── wavelet.py                  # Wavelet transforms
├── fractal_density.py          # Density metrics
├── synthetic_terrain.py        # Test case generation
└── visualization.py            # Visualization/export
```

### Module Dependencies (Dependency Graph)
```
preprocessing → (GDAL, NumPy)
pyramid → preprocessing, NumPy
quadtree → pyramid
ultrametric → quadtree, scipy
wavelet → pyramid, scipy
fractal_density → pyramid, quadtree, wavelet
synthetic_terrain → numpy
visualization → rasterio, matplotlib, numpy
```

### Key Classes and Functions

**Core Data Structures:**
- `GaussianPyramid(dem, num_levels)` - Multi-scale pyramid
- `PadicQuadtree(dem, base_resolution)` - Spatial hierarchy
- `PadicWaveletTransform(pyramid)` - Wavelet decomposition

**Analysis Pipeline:**
- `FractalDensityCalculator(dem)` - Compute density maps
- `UltrametricDistance(quadtree, dem)` - Distance metrics
- `HierarchicalClustering(distance_matrix)` - Clustering

**Validation:**
- `TestSuite.create_test_cases()` - Standard test cases
- `WeierstrrassMandelbrot(size, dimension)` - Synthetic fractals

**Visualization:**
- `FractalDensityVisualizer` - Plotting methods
- `GeoTIFFExporter` - GIS-compatible export

## Common Development Tasks

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific module test
python -m pytest tests/test_pyramid.py -v

# Run with coverage
python -m pytest tests/ --cov=padic
```

### Building Documentation
```bash
# Build Sphinx docs
cd docs
make html
```

### Quick Algorithm Test
```python
from padic import preprocessing, pyramid, fractal_density
import numpy as np

# Create synthetic test DEM
dem = np.random.randn(256, 256) * 10
dem_clean, _ = preprocessing.preprocess_dem(dem)

# Build pyramid and compute density
pyr = pyramid.GaussianPyramid(dem_clean)
calc = fractal_density.FractalDensityCalculator(dem_clean)
density = calc.compute_fractal_density()

print(f"Density range: [{density.min():.3f}, {density.max():.3f}]")
```

### Working with Mars DEMs
```python
from padic import preprocessing, visualization
import rasterio

# Load Mars DEM from GeoTIFF
dem, metadata = preprocessing.load_dem('mars_hirise.tif')

# Process for analysis
dem_clean, stats = preprocessing.preprocess_dem(
    dem,
    fill_depressions_flag=True,
    remove_jitter_flag=True,  # For HiRISE data
    normalize_flag=True
)

# Export results preserving geospatial metadata
exporter = visualization.GeoTIFFExporter()
exporter.save_density_tiff(
    density_map,
    'output_density.tif',
    transform=metadata['transform'],
    crs=metadata['crs']
)
```

## Performance Considerations

**Complexity Analysis:**
- DEM preprocessing: O(n)
- Pyramid construction: O(n)
- Quadtree building: O(n log n)
- Wavelet transform: O(n log n)
- Fractal density: O(n log n)
- **Total**: O(n log n) where n = number of pixels

**Memory Requirements (per 10km × 10km HiRISE region at 1m resolution):**
- Raw DEM: ~400 MB
- Gaussian pyramid: ~530 MB
- Quadtree structure: ~200 MB
- Wavelet coefficients: ~150 MB
- Total working: ~1.3 GB

**Processing Times (estimates):**
- 10km² at 1m resolution: ~2 minutes
- 50km² (Jezero): ~20 minutes
- 150km² (Gale): ~1 hour
- Global MOLA (500m): ~6 hours on HPC

## Key Implementation Notes

1. **Ultrametric Property**: Distance matrices should satisfy d(x,z) ≤ max{d(x,y), d(y,z)}. Use `HierarchicalClustering.validate_ultrametric()` to verify.

2. **Normalization Importance**: Elevation data must be normalized before analysis. Use `preprocessing.preprocess_dem()` with `normalize_flag=True`.

3. **Mars CRS Handling**: Mars DEMs use IAU2000 coordinates (different from Earth). Preserve metadata when loading/saving with GDAL.

4. **Pyramid Level Mapping**: Pyramid level k has resolution 2^k times coarser than base. Map base-resolution coordinates (i,j) to level k: (i//2^k, j//2^k).

5. **Synthetic Terrain Validation**: Use `TestSuite.create_test_cases()` to validate new algorithms before applying to real Mars data.

## Next Steps for Future Claude Instances

When working on this project:

1. **Check implementation status** - Review completed modules listed above
2. **Load Mars data** - Use `preprocessing.load_dem()` with actual GeoTIFF files from `/data/`
3. **Test on synthetic cases** - Start with `synthetic_terrain.TestSuite` before Mars data
4. **Implement validation pipelines** - Next phase: Jezero and Gale crater validation (marked pending in todo list)
5. **Create analysis notebooks** - Jupyter notebooks demonstrating the full workflow
6. **Profile performance** - Use Python profiler to optimize bottlenecks
7. **Integrate GPU acceleration** - Optional: add CUDA support via CuPy for large datasets

---

**Last Updated**: 2025-11-22
**Implementation Level**: Core infrastructure complete, validation pipelines pending
