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

## Figure 4 Reproduction Status (Primary Active Goal)

The main open research goal is reproducing Figure 4 from Zúñiga-Galindo et al. (2023) (`references/ptad061.pdf`).

### What Figure 4 Shows
Left panel: all 3⁶=729 p-adic integers embedded as a Sierpinski triangle. Each point colored black (foreground pixel) or white (background pixel) from a 27×27 binary source image (MNIST digit "5"). Right panel: the source digit.

### What We Know (Confirmed)
- **The embedding works**: `embed_padic_cloud` with p=3, l=6, m=0, s=0.46 produces a clean Sierpinski triangle with uniform nearest-neighbor distances (std≈0, confirmed isometry).
- **s₀ = 0.4641** for p=3 (formula: sin(π/3)/(1+sin(π/3)) ≈ √3/(2+√3)). Earlier docs incorrectly stated 0.2679 — that was an arithmetic error (dropped the √3 numerator). Fixed in `CHISTYAKOV_ALGORITHM_REFERENCE.md`.
- **s=0.46 is correct**: the paper's stated value for the Sierpinski triangle, just below s₀=0.4641.
- **Prior scattered appearance was a visualization artifact**: an earlier notebook (19) used a 50/50 random noise image as source, making all 729 colored points look undifferentiated. The embedding itself was correct.
- **Coordinate mapping**: pixel (i,j) → p-adic int via interleaved base-3 digits works and produces a bijection over {0..728}. The interleaving order (j-first: j₀,i₀,j₁,i₁,...) affects which digit shape is readable inside the Sierpinski, but not the triangle geometry.

### Definitive Notebook
`notebooks/20_figure4_definitive.ipynb` — run this next. It uses:
- p=3, l=6, m=0, s=0.46
- MNIST digit "5" downsampled to 27×27
- Correct layout: Sierpinski LEFT, digit RIGHT
- Validation cell checking NN uniformity and comparing against `references/ptad061fig4.jpeg`

### Remaining Open Questions
1. **Coordinate mapping vs. paper**: The paper may specify a particular (i,j)→p-adic encoding. The current j-first interleaving produces a valid Sierpinski but may rotate/reflect the digit inside the triangle compared to the paper. Investigate by looking at what Figure 4 in the paper shows for the digit shape within the Sierpinski.
2. **Exact source image**: The paper uses a specific binary "5" image (not from MNIST). Close enough for validation, but worth finding the exact image if the paper describes it.
3. **Connect to terrain pipeline**: The p-adic embedding module (`padic_embedding.py`) is currently used only for digit/image visualization. The logical next step is embedding terrain patches (e.g., from the Jezero DEM quadtree nodes) in Sierpinski space to study their fractal geometry.

## Next Steps for Future Claude Instances

1. **Run notebook 20** (`20_figure4_definitive.ipynb`) in the `padic-fractal-analysis` conda env — this is the first thing to do.
2. **Compare output against paper figure** (`references/ptad061fig4.jpeg`) and assess whether the digit shape within the Sierpinski matches.
3. **Investigate coordinate mapping** if the digit orientation doesn't match the paper (try i-first interleaving vs. j-first, or check if the paper specifies the encoding).
4. **Terrain embedding**: once Figure 4 is confirmed, apply the same embedding to terrain patches from the Jezero DEM (cached at `cache/dem_clean.npy`).
5. **Run Gale crater validation** — the full Jezero pipeline exists; Gale crater comparison is the next scientific milestone.

## Environment

Run notebooks with: `conda activate padic-fractal-analysis`

The base anaconda Python has a broken scipy (BLAS/libgfortran issue on macOS). Always use the `padic-fractal-analysis` conda env.

---

**Last Updated**: 2026-04-02
**Implementation Level**: Core infrastructure complete. Figure 4 embedding confirmed working; definitive notebook written, needs execution and comparison against paper.
