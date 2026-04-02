"""
P-adic fractal analysis framework for Mars terrain characterization.

This package provides tools for analyzing hierarchical terrain complexity
using p-adic ultrametric spaces, enabling identification of "densely fractal"
Mars terrain suitable for rover exploration targeting.

Core modules:
- preprocessing: DEM data loading, cleaning, and normalization
- pyramid: Gaussian pyramid construction for multi-scale analysis
- quadtree: P-adic quadtree spatial data structure with ultrametric encoding
- ultrametric: Ultrametric distance computation and hierarchical clustering
- wavelet: P-adic wavelet transforms with perfect space-scale localization
- fractal_density: Fractal density metrics combining complexity measures
- per_pixel_complexity: Per-pixel fractal complexity using p-adic methods
- synthetic_terrain: Synthetic fractal terrain generation for validation
- visualization: Visualization and GeoTIFF export utilities
"""

__version__ = "0.1.0"
__author__ = "Research Team"

# Always import padic_embedding (no external dependencies beyond numpy)
from . import padic_embedding

# Lazily import other modules that may have environment dependencies
_optional_modules = [
    "preprocessing",
    "pyramid",
    "quadtree",
    "ultrametric",
    "wavelet",
    "fractal_density",
    "per_pixel_complexity",
    "synthetic_terrain",
    "visualization",
]

__all__ = ["padic_embedding"] + _optional_modules

# Try to import optional modules
for module_name in _optional_modules:
    try:
        exec(f"from . import {module_name}")
    except ImportError as e:
        print(f"Warning: Could not import {module_name}: {e}")
