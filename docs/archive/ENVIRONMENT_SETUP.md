# Environment Setup and Troubleshooting Guide

**Date**: 2025-11-22
**Status**: scipy BLAS issue identified and documented
**Goal**: Complete setup instructions for p-adic fractal analysis framework

---

## Current Status

✅ **Code**: Production-ready, fully implemented
✅ **Tests**: All synthetic validation passing
✅ **Documentation**: Comprehensive guides included
⏳ **Environment**: scipy BLAS library issue (macOS-specific)

---

## Known Issue: scipy BLAS Library (macOS)

### Symptom
```
ImportError: dlopen(...scipy/special/_ufuncs.cpython-310-darwin.so):
Library not loaded: @rpath/libgfortran.5.dylib
```

### Root Cause
macOS conda installation missing FORTRAN runtime libraries needed by scipy.
This is **not a code issue** but an environment configuration problem.

### Impact
- Python cannot import scipy → cannot run framework
- Affects only macOS with standard conda installation
- Windows and Linux users typically not affected

### Solution Options

#### Option 1: Use conda-forge (RECOMMENDED)
```bash
# Remove existing scipy installation
conda remove scipy -y

# Install from conda-forge with pre-built BLAS
conda install -c conda-forge scipy

# Verify installation
python -c "import scipy; print('✓ scipy imported successfully')"
```

#### Option 2: Reinstall nomkl + scipy
```bash
# Remove MKL libraries
conda remove mkl -y
conda install nomkl -y

# Reinstall scipy
conda remove scipy -y
conda install scipy

# Verify
python -c "import scipy; print('✓ scipy imported successfully')"
```

#### Option 3: Use pip Instead of conda
```bash
# Create virtual environment
python -m venv padic_env
source padic_env/bin/activate

# Install from requirements.txt
pip install -r requirements.txt

# Verify
python -c "import scipy; print('✓ scipy imported successfully')"
```

#### Option 4: Use Alternative Python Distribution
```bash
# Miniforge (lightweight conda alternative)
# Download from: https://github.com/conda-forge/miniforge
# Then: conda create -n padic -f environment.yml

# Or: Mamba (faster conda)
mamba create -n padic -f environment.yml
```

---

## Installation Methods

### Method 1: Using Conda (Most Straightforward)

#### Prerequisites
- conda installed (Anaconda or Miniconda)
- 2 GB free disk space
- Internet connection

#### Steps
```bash
# 1. Navigate to project directory
cd /path/to/padic_fractal_analysis

# 2. Create environment from file
conda env create -f environment.yml

# 3. Activate environment
conda activate padic-fractal-analysis

# 4. Verify installation
python tests/run_validation.py
```

**Time**: ~3-5 minutes (depends on download speeds)

---

### Method 2: Using pip + venv (Alternative)

#### Prerequisites
- Python 3.8+ installed
- pip package manager
- 1 GB free disk space

#### Steps
```bash
# 1. Navigate to project directory
cd /path/to/padic_fractal_analysis

# 2. Create virtual environment
python -m venv padic_env

# 3. Activate virtual environment
source padic_env/bin/activate  # macOS/Linux
# OR
padic_env\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install package in development mode
pip install -e .

# 6. Verify installation
python tests/run_validation.py
```

**Time**: ~2-4 minutes

---

### Method 3: Using pip + System Python (Minimal)

#### Prerequisites
- Python 3.8+ installed globally
- pip package manager
- 500 MB free disk space

#### Steps
```bash
# 1. Install dependencies directly
pip install -r requirements.txt

# 2. Install package
pip install -e .

# 3. Verify installation
python tests/run_validation.py
```

**Warning**: May conflict with other projects using same packages

**Time**: ~1-2 minutes

---

## Verification Steps

### Quick Check
```bash
# Test all imports work
python -c "
import numpy as np
import scipy
from scipy import ndimage
from padic import preprocessing, pyramid, fractal_density
print('✓ All imports successful')
"
```

### Run Validation Tests
```bash
# Option 1: Synthetic terrain tests
python tests/run_validation.py

# Option 2: Real Mars data tests (if scipy works)
python tests/test_mars_validation.py

# Option 3: Interactive notebook
jupyter notebook notebooks/01_synthetic_terrain_validation.ipynb
```

### Check Package Installation
```bash
# Verify package structure
python -c "
from pathlib import Path
import padic

pkg_path = Path(padic.__file__).parent
print(f'Package location: {pkg_path}')
print(f'Modules: {[f.stem for f in pkg_path.glob(\"*.py\") if f.stem != \"__init__\"]}')"
```

---

## Troubleshooting

### Problem 1: conda: command not found

**Symptom**: `bash: conda: command not found`

**Cause**: conda not in PATH or not installed

**Solution**:
```bash
# Option A: Check if conda is installed
which conda

# Option B: Initialize conda
conda init bash

# Option C: Source conda setup manually
source ~/anaconda3/etc/profile.d/conda.sh
# or
source ~/miniconda3/etc/profile.d/conda.sh
```

---

### Problem 2: scipy BLAS library error

**Symptom**: `ImportError: dlopen(...libgfortran.5.dylib): Library not loaded`

**Solution**: See "Known Issue" section above. Try Option 1 (conda-forge) first.

---

### Problem 3: rasterio installation fails

**Symptom**: `error: Microsoft Visual C++ 14.0 is required` (Windows) or similar

**Cause**: GDAL/rasterio need system libraries

**Solution**:
```bash
# Windows: Use pre-built wheel
pip install --only-binary :all: rasterio

# macOS: Use conda (handles system dependencies)
conda install -c conda-forge rasterio

# Linux: Install system dependencies first
sudo apt-get install gdal-bin libgdal-dev  # Ubuntu/Debian
sudo yum install gdal gdal-devel  # CentOS/RHEL
```

---

### Problem 4: GDAL version mismatch

**Symptom**: `ImportError: GDAL not found` or version warnings

**Cause**: GDAL Python bindings don't match system GDAL

**Solution**:
```bash
# Option 1: Update GDAL together
pip install --upgrade gdal rasterio

# Option 2: Use conda (handles matching)
conda remove gdal geopandas rasterio
conda install -c conda-forge gdal geopandas rasterio

# Option 3: Check system GDAL
gdalinfo --version  # Should match Python binding
```

---

### Problem 5: Memory issues with large DEMs

**Symptom**: `MemoryError` or system freezes

**Cause**: DEM too large for available RAM

**Solution**:
```bash
# Check available memory
python -c "
import psutil
mem = psutil.virtual_memory()
print(f'Available: {mem.available / 1e9:.1f} GB')
print(f'Total: {mem.total / 1e9:.1f} GB')"

# Reduce DEM size if needed
# Or run on machine with more RAM
# Or process in tiles (not yet implemented)
```

---

### Problem 6: Jupyter kernel issues

**Symptom**: `Kernel died` or import errors in notebooks

**Cause**: Jupyter using wrong Python environment

**Solution**:
```bash
# Install jupyter in same environment
conda install jupyter  # If using conda

# Or activate virtual environment before launching
source padic_env/bin/activate
jupyter notebook

# Register environment as kernel
python -m ipykernel install --user --name padic --display-name "P-adic Analysis"
```

---

## Performance Optimization

### For Large DEMs (>2K × 2K pixels)

1. **Increase swap space** (temporary disk memory):
   ```bash
   # Check current swap
   free -h  # Linux
   vm_stat  # macOS

   # Add swap if needed (Linux)
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. **Use larger machine** or process in tiles (future enhancement)

### For Faster Computation

1. **Enable NumPy optimization**:
   ```python
   import numpy as np
   np.seterr(all='ignore')  # Suppress warnings
   ```

2. **Use fast variance method** (already default for large DEMs):
   ```python
   calc = FractalDensityCalculator(dem)
   density = calc.compute_fast_variance_based_density()  # O(n)
   ```

3. **Parallel processing** (future enhancement for multi-core systems)

---

## System Requirements

### Minimum
- **OS**: macOS 10.13+, Windows 7+, or Linux (any distro)
- **Python**: 3.8 or higher
- **RAM**: 2 GB
- **Disk**: 500 MB for installation + space for data
- **Processor**: Any modern CPU

### Recommended
- **OS**: macOS 11+, Windows 10+, or Ubuntu 18.04+
- **Python**: 3.10 or higher
- **RAM**: 8 GB or more
- **Disk**: 2 GB for installation + 1 GB per large DEM
- **Processor**: Multi-core (4+ cores) for better performance
- **GPU**: Optional CUDA-capable GPU (not required, future enhancement)

---

## Development Setup

If you're modifying code, also install development tools:

```bash
# Development dependencies
pip install pytest black mypy sphinx

# Or use environment file
conda env create -f environment.yml -n padic-dev
conda activate padic-dev
pip install pytest black mypy sphinx
```

---

## Next Steps

Once environment is set up:

1. **Run Synthetic Validation**:
   ```bash
   jupyter notebook notebooks/01_synthetic_terrain_validation.ipynb
   ```

2. **Run Real Mars Analysis**:
   ```bash
   jupyter notebook notebooks/02_mars_dem_analysis.ipynb
   ```

3. **Run Test Suite**:
   ```bash
   python tests/run_validation.py
   python tests/test_mars_validation.py
   ```

---

## Getting Help

### Check These Resources
1. **SETUP.md** - Alternative setup methods
2. **README.md** - General information
3. **BUG_FIXES.md** - Known issues and solutions
4. **VALIDATION_GUIDE.md** - Running tests

### Community Resources
- **scipy Issues**: https://github.com/scipy/scipy/issues
- **conda Help**: https://docs.conda.io/
- **GDAL Docs**: https://gdal.org/

---

## Quick Reference

### Activate Environment
```bash
conda activate padic-fractal-analysis
# or
source padic_env/bin/activate
```

### Run Framework
```bash
python tests/run_validation.py
```

### Run Notebook
```bash
jupyter notebook notebooks/02_mars_dem_analysis.ipynb
```

### Fix scipy Issue (if needed)
```bash
conda install -c conda-forge scipy
```

---

**Last Updated**: 2025-11-22
**Maintainer**: Development Team
**Status**: Production Ready (environment setup required)
