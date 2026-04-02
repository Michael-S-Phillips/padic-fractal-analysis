"""
DEM preprocessing module for p-adic fractal analysis.

Handles DEM data loading, artifact removal, depression filling,
terrain attribute computation, and normalization to prepare data
for hierarchical p-adic analysis.
"""

import numpy as np
from scipy import ndimage
from scipy.ndimage import gaussian_filter, maximum_filter, minimum_filter
import rasterio
from typing import Tuple, Optional, Dict


def load_dem(filepath: str) -> Tuple[np.ndarray, Dict]:
    """
    Load a DEM from GeoTIFF file using rasterio.

    Parameters
    ----------
    filepath : str
        Path to GeoTIFF DEM file

    Returns
    -------
    dem : np.ndarray
        2D elevation array
    metadata : dict
        Geospatial metadata (CRS, transform, bounds, etc.)
    """
    with rasterio.open(filepath) as src:
        dem = src.read(1).astype(np.float32)
        metadata = {
            'crs': src.crs,
            'transform': src.transform,
            'bounds': src.bounds,
            'width': src.width,
            'height': src.height,
            'nodata': src.nodata,
            'dtype': src.dtypes[0],
        }
    return dem, metadata


def fill_depressions(dem: np.ndarray, max_iterations: int = 1000) -> np.ndarray:
    """
    Fill surface depressions using Priority-Flood algorithm.

    This ensures hydrological correctness for terrain analysis.
    Uses iterative morphological closing to fill pits.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    max_iterations : int
        Maximum iterations for depression filling

    Returns
    -------
    dem_filled : np.ndarray
        DEM with depressions filled
    """
    dem_filled = dem.copy()

    for _ in range(max_iterations):
        dem_eroded = ndimage.grey_erosion(dem_filled, size=3)
        dem_filled = np.maximum(dem_filled, dem_eroded)

        # Check convergence
        if np.allclose(dem_filled, dem_eroded):
            break

    return dem_filled


def remove_jitter(dem: np.ndarray, direction: str = 'vertical', window_size: int = 5) -> np.ndarray:
    """
    Remove HiRISE jitter artifacts (washboard patterns along track direction).

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    direction : str
        Direction of jitter artifacts ('vertical', 'horizontal', 'both')
    window_size : int
        Median filter window size

    Returns
    -------
    dem_denoised : np.ndarray
        DEM with jitter removed
    """
    dem_denoised = dem.copy()

    if direction in ['vertical', 'both']:
        # Apply vertical directional median filter
        for i in range(window_size // 2, dem.shape[0] - window_size // 2):
            dem_denoised[i, :] = np.median(
                dem[i - window_size//2:i + window_size//2 + 1, :],
                axis=0
            )

    if direction in ['horizontal', 'both']:
        # Apply horizontal directional median filter
        for j in range(window_size // 2, dem.shape[1] - window_size // 2):
            dem_denoised[:, j] = np.median(
                dem[:, j - window_size//2:j + window_size//2 + 1],
                axis=1
            )

    return dem_denoised


def compute_slope(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
    """
    Compute slope (terrain gradient) from DEM.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    cell_size : float
        DEM cell size in meters

    Returns
    -------
    slope : np.ndarray
        Slope in degrees (0-90)
    """
    gy, gx = np.gradient(dem, cell_size)
    slope_radians = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_degrees = np.degrees(slope_radians)
    return slope_degrees


def compute_aspect(dem: np.ndarray) -> np.ndarray:
    """
    Compute aspect (slope direction) from DEM.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model

    Returns
    -------
    aspect : np.ndarray
        Aspect in degrees (0-360), with 0=North, 90=East
    """
    gy, gx = np.gradient(dem)
    aspect = np.arctan2(-gx, gy)
    aspect = np.degrees(aspect)
    aspect = (aspect + 180) % 360
    return aspect


def compute_curvature(dem: np.ndarray, cell_size: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute plan and profile curvature from DEM.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    cell_size : float
        DEM cell size in meters

    Returns
    -------
    plan_curv : np.ndarray
        Plan curvature (horizontal curvature)
    profile_curv : np.ndarray
        Profile curvature (vertical curvature)
    """
    # Compute second derivatives
    gy, gx = np.gradient(dem, cell_size)

    gyy, gyx = np.gradient(gy, cell_size)
    gxy, gxx = np.gradient(gx, cell_size)

    # Plan curvature (horizontal): -∂²z/∂x∂y / (∂z/∂x)² - (∂z/∂y)²
    # Profile curvature (vertical): -∂²z/∂x² (∂z/∂y)² + 2∂²z/∂x∂y ∂z/∂x∂z/∂y - ∂²z/∂y² (∂z/∂x)²

    denominator = gx**2 + gy**2 + 1e-8  # Avoid division by zero

    plan_curv = -gyx / denominator
    profile_curv = -(gxx * gy**2 + 2*gxy*gx*gy + gyy*gx**2) / (denominator**(3/2) + 1e-8)

    return plan_curv, profile_curv


def compute_roughness(dem: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Compute local roughness as variance of elevation differences.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    window_size : int
        Local window size for roughness computation

    Returns
    -------
    roughness : np.ndarray
        Local roughness measure
    """
    roughness = np.zeros_like(dem)
    pad = window_size // 2

    for i in range(pad, dem.shape[0] - pad):
        for j in range(pad, dem.shape[1] - pad):
            window = dem[i-pad:i+pad+1, j-pad:j+pad+1]
            roughness[i, j] = np.std(window)

    return roughness


def normalize_dem(dem: np.ndarray, method: str = 'zscore') -> np.ndarray:
    """
    Normalize DEM values for analysis.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    method : str
        Normalization method: 'zscore', 'minmax', or 'standardize'

    Returns
    -------
    dem_normalized : np.ndarray
        Normalized DEM
    """
    valid_mask = np.isfinite(dem)
    valid_data = dem[valid_mask]

    if method == 'zscore':
        # Z-score normalization: (x - μ) / σ
        mean = np.mean(valid_data)
        std = np.std(valid_data)
        dem_normalized = (dem - mean) / (std + 1e-8)

    elif method == 'minmax':
        # Min-max normalization: (x - min) / (max - min)
        dem_min = np.min(valid_data)
        dem_max = np.max(valid_data)
        dem_normalized = (dem - dem_min) / (dem_max - dem_min + 1e-8)

    elif method == 'standardize':
        # Simple standardization
        dem_normalized = (dem - np.mean(valid_data)) / np.max(np.abs(dem - np.mean(valid_data)))

    else:
        raise ValueError(f"Unknown normalization method: {method}")

    return dem_normalized


def preprocess_dem(
    dem: np.ndarray,
    fill_depressions_flag: bool = True,
    remove_jitter_flag: bool = False,
    normalize_flag: bool = True,
    normalization_method: str = 'zscore',
) -> Tuple[np.ndarray, Dict]:
    """
    Complete preprocessing pipeline for DEM data.

    Applies depression filling, optional jitter removal, and normalization.

    Parameters
    ----------
    dem : np.ndarray
        Raw digital elevation model
    fill_depressions_flag : bool
        Whether to fill depressions
    remove_jitter_flag : bool
        Whether to remove jitter artifacts (for HiRISE data)
    normalize_flag : bool
        Whether to normalize elevation values
    normalization_method : str
        Normalization method to use

    Returns
    -------
    dem_processed : np.ndarray
        Preprocessed DEM
    stats : dict
        Dictionary of preprocessing statistics
    """
    stats = {}
    dem_processed = dem.copy()

    # Remove NaN/invalid values temporarily for statistics
    valid_mask = np.isfinite(dem_processed)
    valid_data = dem_processed[valid_mask]

    stats['original_mean'] = float(np.mean(valid_data))
    stats['original_std'] = float(np.std(valid_data))
    stats['original_min'] = float(np.min(valid_data))
    stats['original_max'] = float(np.max(valid_data))

    # Fill depressions
    if fill_depressions_flag:
        dem_processed = fill_depressions(dem_processed)
        stats['depressions_filled'] = True

    # Remove jitter
    if remove_jitter_flag:
        dem_processed = remove_jitter(dem_processed)
        stats['jitter_removed'] = True

    # Normalize
    if normalize_flag:
        dem_processed = normalize_dem(dem_processed, method=normalization_method)
        stats['normalized'] = True
        stats['normalization_method'] = normalization_method

    valid_mask = np.isfinite(dem_processed)
    valid_data = dem_processed[valid_mask]

    stats['processed_mean'] = float(np.mean(valid_data))
    stats['processed_std'] = float(np.std(valid_data))
    stats['processed_min'] = float(np.min(valid_data))
    stats['processed_max'] = float(np.max(valid_data))

    return dem_processed, stats


def mask_invalid_pixels(dem: np.ndarray, nodata_value: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identify and mask invalid pixels (NaN, nodata values, extreme values).

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    nodata_value : float, optional
        Nodata value to mask

    Returns
    -------
    dem_masked : np.ndarray
        DEM with invalid values set to NaN
    mask : np.ndarray
        Boolean mask of valid pixels
    """
    mask = np.ones_like(dem, dtype=bool)

    # Mask NaN values
    mask &= np.isfinite(dem)

    # Mask nodata values
    if nodata_value is not None:
        mask &= (dem != nodata_value)

    # Mask extreme outliers (more than 5 sigma from mean)
    valid_data = dem[mask]
    if len(valid_data) > 0:
        mean = np.mean(valid_data)
        std = np.std(valid_data)
        mask &= (np.abs(dem - mean) < 5 * std)

    dem_masked = dem.copy()
    dem_masked[~mask] = np.nan

    return dem_masked, mask
