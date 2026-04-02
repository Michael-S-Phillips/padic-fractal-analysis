# Setup Instructions for P-adic Fractal Analysis

## Quick Start

### Option 1: Using conda (Recommended)

```bash
# Create the conda environment
conda env create -f environment.yml

# Activate the environment
conda activate padic-fractal-analysis

# Install the package in development mode
pip install -e .
```

### Option 2: Using pip with pyproject.toml

```bash
# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package and dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Option 3: Using pip with requirements.txt

If you prefer a simpler approach, we can generate a requirements.txt:

```bash
pip install numpy scipy scikit-image scikit-learn rasterio geopandas gdal matplotlib jupyter h5py pywavelets numba pytest black

# Then install the package
pip install -e .
```

## Verifying Installation

### Test imports
```bash
python -c "from padic import preprocessing, pyramid, fractal_density; print('✓ All imports successful')"
```

### Run quick validation
```bash
python tests/run_validation.py
```

### Launch Jupyter notebook
```bash
jupyter notebook notebooks/01_synthetic_terrain_validation.ipynb
```

## System Requirements

### Minimum
- Python 3.8+
- 4 GB RAM
- 2 GB disk space

### Recommended
- Python 3.10+
- 8+ GB RAM
- 10 GB disk space (for Mars DEM files)
- macOS, Linux, or Windows 10+

## Dependency Details

### Core Scientific Stack
- **numpy**: Array operations
- **scipy**: Scientific computing (filtering, interpolation)
- **scikit-image**: Image processing
- **scikit-learn**: Machine learning

### Geospatial
- **gdal**: GeoTIFF I/O and processing
- **rasterio**: Pythonic GIS data access
- **geopandas**: Geospatial data frames

### Visualization & Analysis
- **matplotlib**: 2D plotting
- **jupyter/jupyterlab**: Interactive notebooks
- **plotly**: Interactive visualizations

### Optimization
- **numba**: JIT compilation for performance-critical code
- **h5py**: HDF5 file I/O for large datasets
- **pywavelets**: Wavelet transforms

## Troubleshooting

### Issue: "ImportError: libgfortran.5.dylib"
**On macOS:** This is a known BLAS/LAPACK issue
```bash
# Install dependencies
brew install gcc
conda install nomkl

# Rebuild scipy
conda remove scipy
conda install scipy
```

### Issue: "GDAL not found"
```bash
# Install GDAL
conda install gdal

# Or on macOS via Homebrew
brew install gdal
```

### Issue: "Module not found in development mode"
```bash
# Ensure you're in the project root and run
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### Issue: "Permission denied" when installing
```bash
# Use user installation
pip install --user -e .

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Environment Variables

Set these for optimal performance:

```bash
# Use MKL-free BLAS (avoids licensing issues)
export OPENBLAS_NUM_THREADS=4

# Enable Numba parallel execution
export NUMBA_NUM_THREADS=4

# Set matplotlib backend (for headless systems)
export MPLBACKEND=Agg
```

## Conda Environment Management

### Create from YAML
```bash
conda env create -f environment.yml
```

### Update environment
```bash
conda env update -f environment.yml --prune
```

### List environments
```bash
conda env list
```

### Activate environment
```bash
conda activate padic-fractal-analysis
```

### Remove environment
```bash
conda remove --name padic-fractal-analysis --all
```

### Export current environment
```bash
conda env export > environment.yml
```

## Development Setup

### Install with all development tools
```bash
conda activate padic-fractal-analysis
pip install -e ".[dev]"
```

### Run code quality checks
```bash
# Format code
black src/ tests/ notebooks/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Run tests with coverage
```bash
pytest tests/ --cov=padic --cov-report=html
```

### Build documentation
```bash
cd docs
make html
```

## Quick Verification Checklist

After installation, verify everything works:

- [ ] `python -c "import padic"` - Package imports
- [ ] `python tests/run_validation.py` - Tests run
- [ ] `jupyter notebook` - Jupyter launches
- [ ] Load a DEM - GIS functionality works

## Alternative: Docker Setup (Future)

For reproducible environments across machines:

```bash
# Docker image will be available in future versions
docker pull padic-fractal-analysis:latest
docker run -it -v $(pwd):/workspace padic-fractal-analysis:latest
```

## Getting Help

If you encounter issues:

1. Check this file first
2. Review `CLAUDE.md` for implementation details
3. Check `README.md` for usage examples
4. Review error messages in `tests/` output
5. See `VALIDATION_GUIDE.md` for validation issues

## Next Steps

After successful installation:

1. **Try the synthetic validation** - Run `python tests/run_validation.py`
2. **Explore the notebook** - Open `notebooks/01_synthetic_terrain_validation.ipynb`
3. **Review the code** - Start with `src/padic/preprocessing.py`
4. **Read the docs** - Start with `README.md`

---

**Setup Version**: 1.0
**Last Updated**: 2025-11-22
**Status**: Ready for installation
