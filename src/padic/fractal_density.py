"""
Fractal density calculation for hierarchical terrain complexity.

Computes local fractal density metrics that combine geometric complexity,
multi-scale persistence, and information content to identify "densely fractal"
terrain regions warranting rover exploration.
"""

import numpy as np
from typing import Tuple, Optional
from scipy.ndimage import gaussian_filter
from .pyramid import GaussianPyramid
from .quadtree import PadicQuadtree
from .wavelet import PadicWaveletTransform, WaveletModulusMaxima


class FractalDensityCalculator:
    """
    Compute fractal density metrics for terrain complexity characterization.

    Fractal density combines:
    1. Local fractal dimension (geometric complexity)
    2. Multi-scale persistence (consistency across scales)
    3. Information content (unpredictability in patterns)
    """

    def __init__(self, dem: np.ndarray, base_resolution: float = 1.0):
        """
        Initialize fractal density calculator.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        base_resolution : float
            Cell size at finest level in meters
        """
        self.dem = dem
        self.base_resolution = base_resolution
        self.pyramid = GaussianPyramid(dem)
        self.quadtree = PadicQuadtree(dem, base_resolution)

    def compute_local_fractal_dimension(self, i: int, j: int,
                                       window_size: int = 5) -> float:
        """
        Compute local fractal dimension using variance profile method.

        For fractal terrain: variance ~ scale^beta
        Fractal dimension D = 3 - beta/2

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local analysis

        Returns
        -------
        D_local : float
            Local fractal dimension (typically 2.0-3.0)
        """
        # Get variance profile across scales
        variance_profile = self.pyramid.compute_variance_profile(i, j, window_size)

        # Fit to power law in log-log space
        slope, D_local = self.pyramid.compute_fractal_slope(variance_profile)

        return D_local

    def compute_persistence(self, i: int, j: int, window_size: int = 5,
                           min_r2: float = 0.95) -> float:
        """
        Compute multi-scale persistence measure.

        Counts how many scales exhibit consistent fractal scaling.
        High persistence indicates robust multi-scale structure.

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local analysis
        min_r2 : float
            Minimum R² threshold for fractal scaling

        Returns
        -------
        persistence : float
            Fraction of scales showing consistent fractal scaling (0-1)
        """
        variance_profile = self.pyramid.compute_variance_profile(i, j, window_size)

        # Remove zero variances
        valid_indices = np.where(variance_profile > 1e-10)[0]

        if len(valid_indices) < 2:
            return 0.0

        scales = np.array(valid_indices, dtype=float)
        variances = variance_profile[valid_indices]

        # Compute R² for log-log fit
        log_scales = np.log(scales + 1)
        log_variances = np.log(variances)

        # Linear regression
        coeffs = np.polyfit(log_scales, log_variances, 1)
        slope = coeffs[0]

        # Predict and compute R²
        y_pred = coeffs[0] * log_scales + coeffs[1]
        ss_res = np.sum((log_variances - y_pred) ** 2)
        ss_tot = np.sum((log_variances - np.mean(log_variances)) ** 2)

        if ss_tot == 0:
            return 0.0

        r_squared = 1 - (ss_res / ss_tot)

        # Persistence: fraction of scales consistent with power law
        num_consistent = np.sum(r_squared >= min_r2 - 0.2)  # Allow some variation
        persistence = num_consistent / len(valid_indices)

        return float(persistence)

    def compute_information_content(self, i: int, j: int,
                                   window_size: int = 5) -> float:
        """
        Compute information content (entropy) of local elevation patterns.

        Quantifies unpredictability in terrain structure.

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local analysis

        Returns
        -------
        information : float
            Normalized information content (0-1)
        """
        pad = window_size // 2
        i_clamped = np.clip(i, pad, self.dem.shape[0] - pad - 1)
        j_clamped = np.clip(j, pad, self.dem.shape[1] - pad - 1)

        window = self.dem[i_clamped-pad:i_clamped+pad+1, j_clamped-pad:j_clamped+pad+1]

        # Compute gradient directions in window
        gy, gx = np.gradient(window)
        gradient_mag = np.sqrt(gx**2 + gy**2)

        # Discretize directions into 8 bins
        gradient_dirs = np.arctan2(gy, gx)
        bins = np.linspace(-np.pi, np.pi, 9)
        dir_indices = np.digitize(gradient_dirs, bins)

        # Compute Shannon entropy of direction distribution
        unique, counts = np.unique(dir_indices, return_counts=True)
        probabilities = counts / np.sum(counts)

        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * np.log2(p)

        # Maximum entropy is log2(8) for 8 directions
        max_entropy = np.log2(8)
        information = entropy / max_entropy if max_entropy > 0 else 0.0

        return float(np.clip(information, 0.0, 1.0))

    def compute_variance_persistence_ratio(self, i: int, j: int,
                                          window_size: int = 5) -> float:
        """
        Compute variance persistence ratio across scales.

        Measures total hierarchical elevation variability normalized by
        finest-scale roughness.

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local analysis

        Returns
        -------
        ratio : float
            Variance persistence ratio (0-1 after normalization)
        """
        variance_profile = self.pyramid.compute_variance_profile(i, j, window_size)

        # Sum variance across all scales
        total_variance = np.sum(variance_profile)

        # Normalize by finest-scale variance and number of levels
        finest_variance = variance_profile[0]
        num_levels = len(variance_profile)

        if finest_variance < 1e-10:
            return 0.0

        ratio = total_variance / (finest_variance * num_levels)

        return float(np.clip(ratio, 0.0, 1.0))

    def compute_characteristic_scales(self, i: int, j: int,
                                     window_size: int = 5) -> int:
        """
        Count characteristic scales where new terrain structure emerges.

        Identifies local maxima in variance derivative across scales.

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local analysis

        Returns
        -------
        num_scales : int
            Number of characteristic scales
        """
        variance_profile = self.pyramid.compute_variance_profile(i, j, window_size)

        if len(variance_profile) < 3:
            return 0

        # Compute scale derivative
        derivatives = np.diff(variance_profile)

        # Find local maxima in derivative
        num_maxima = 0
        for k in range(1, len(derivatives) - 1):
            if derivatives[k] > derivatives[k-1] and derivatives[k] > derivatives[k+1]:
                num_maxima += 1

        return num_maxima

    def compute_fractal_density(self, window_size: int = 5,
                               d_weight: float = 1.0,
                               p_weight: float = 1.0,
                               i_weight: float = 1.0) -> np.ndarray:
        """
        Compute complete fractal density map.

        Combines local fractal dimension, multi-scale persistence,
        and information content into unified density metric.

        ρ_fractal = D_local * P(x,y) * I(x,y) / max_value

        Parameters
        ----------
        window_size : int
            Window size for local analysis
        d_weight : float
            Weight for dimension term
        p_weight : float
            Weight for persistence term
        i_weight : float
            Weight for information content

        Returns
        -------
        density : np.ndarray
            Fractal density at each pixel
        """
        height, width = self.dem.shape
        density = np.zeros_like(self.dem)

        # Sample every N pixels for efficiency
        step = max(1, height // 50)

        for i in range(0, height, step):
            for j in range(0, width, step):
                if np.isfinite(self.dem[i, j]):
                    # Compute components
                    d_local = self.compute_local_fractal_dimension(i, j, window_size)
                    persistence = self.compute_persistence(i, j, window_size)
                    information = self.compute_information_content(i, j, window_size)

                    # Normalize dimension to 0-1 range (typical 2.0-3.0)
                    d_normalized = (d_local - 2.0) / 1.0

                    # Combine with weights
                    combined = (
                        d_weight * d_normalized +
                        p_weight * persistence +
                        i_weight * information
                    )

                    density[i, j] = combined

        # Interpolate to full resolution
        from scipy.interpolate import griddata

        valid_mask = density != 0
        if np.any(valid_mask):
            coords = np.where(valid_mask)
            values = density[valid_mask]

            i_grid, j_grid = np.mgrid[0:height, 0:width]
            density_interp = griddata(
                (coords[0], coords[1]), values,
                (i_grid, j_grid),
                method='linear'
            )

            density = np.nan_to_num(density_interp, nan=0.0)

        # Normalize to 0-1 range
        max_density = np.max(density)
        if max_density > 0:
            density = density / max_density

        return density

    def compute_fast_variance_based_density(self) -> np.ndarray:
        """
        Compute fractal density using fast variance-based method.

        Computes hierarchical variance profile and integrates across scales
        for efficient O(n) algorithm.

        Returns
        -------
        density : np.ndarray
            Fractal density at base resolution
        """
        height, width = self.dem.shape
        density = np.zeros((height, width), dtype=np.float32)

        # For each location, compute variance persistence
        for k in range(self.pyramid.num_levels):
            level_data = self.pyramid.levels[k]

            # Upsample back to base resolution
            scale_factor = 2 ** k
            if k > 0:
                upsampled = np.repeat(np.repeat(level_data, scale_factor, axis=0),
                                    scale_factor, axis=1)
                # Trim to exact size
                upsampled = upsampled[:height, :width]
            else:
                upsampled = level_data

            # Add contribution to density
            # Normalize by variance at this level to prevent scale-dependent bias
            # Higher variance at coarser scales indicates multi-scale structure
            level_variance = np.var(level_data) if np.var(level_data) > 1e-8 else 1.0

            # Accumulate normalized contributions
            normalized = np.abs(upsampled) / (level_variance + 1e-8)
            density += normalized

        # Normalize to [0, 1] range
        max_density = np.max(density)
        if max_density > 1e-8:
            density = density / max_density

        # Ensure output is in valid range
        density = np.clip(density, 0.0, 1.0)

        return density


class MultiScaleAnalysis:
    """
    Multi-scale analysis combining multiple fractal density measures.
    """

    def __init__(self, dem: np.ndarray, base_resolution: float = 1.0):
        """
        Initialize multi-scale analysis.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        base_resolution : float
            Cell size in meters
        """
        self.dem = dem
        self.calculator = FractalDensityCalculator(dem, base_resolution)

    def compute_combined_density(self) -> np.ndarray:
        """
        Compute density using multiple methods and average results.

        Returns
        -------
        combined : np.ndarray
            Combined fractal density estimate
        """
        # Weighted averaging of methods
        density1 = self.calculator.compute_fractal_density()
        density2 = self.calculator.compute_fast_variance_based_density()

        combined = (density1 + density2) / 2.0

        return combined

    def extract_peaks(self, density: np.ndarray,
                     percentile: float = 90.0) -> np.ndarray:
        """
        Extract high fractal density regions.

        Parameters
        ----------
        density : np.ndarray
            Fractal density map
        percentile : float
            Percentile threshold for high-density regions

        Returns
        -------
        peaks : np.ndarray
            Boolean mask of high-density regions
        """
        threshold = np.percentile(density, percentile)
        peaks = density >= threshold

        return peaks
