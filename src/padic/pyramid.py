"""
Gaussian pyramid construction for multi-scale DEM analysis.

Builds hierarchical multi-resolution representation of elevation data
using iterative Gaussian filtering and downsampling, enabling O(n) total
storage and efficient multi-scale analysis.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, zoom
from typing import List, Tuple, Optional


class GaussianPyramid:
    """
    Hierarchical Gaussian pyramid for multi-scale terrain analysis.

    The pyramid represents elevation data at exponentially coarser scales,
    with each level having 1/4 the pixels of the previous level.
    """

    def __init__(self, dem: np.ndarray, num_levels: Optional[int] = None):
        """
        Initialize Gaussian pyramid from DEM.

        Parameters
        ----------
        dem : np.ndarray
            Base digital elevation model (level 0)
        num_levels : int, optional
            Number of pyramid levels. If None, compute as log2(max(height, width))
        """
        self.levels: List[np.ndarray] = []
        self.num_levels = num_levels or self._compute_num_levels(dem.shape)

        # Ensure num_levels doesn't exceed data size
        self.num_levels = min(
            self.num_levels,
            int(np.log2(max(dem.shape))) + 1
        )

        self._build_pyramid(dem)

    @staticmethod
    def _compute_num_levels(shape: Tuple[int, int]) -> int:
        """Compute optimal number of pyramid levels."""
        max_dim = max(shape)
        return int(np.log2(max_dim)) + 1

    def _build_pyramid(self, dem: np.ndarray) -> None:
        """
        Build the Gaussian pyramid by iterative filtering and downsampling.

        At level k, we apply Gaussian filter with σ = sqrt(2^(2k) - 2^(2(k-1)))
        then subsample by factor of 2.
        """
        current_level = dem.copy().astype(np.float32)
        self.levels.append(current_level)

        for k in range(1, self.num_levels):
            # Compute Gaussian sigma for this level
            sigma = np.sqrt(2**(2*k) - 2**(2*(k-1)))

            # Apply Gaussian filter with separable convolution
            filtered = gaussian_filter(current_level, sigma=sigma / np.sqrt(2))

            # Downsample by factor of 2 using zoom
            downsampled = filtered[::2, ::2].copy()

            self.levels.append(downsampled)
            current_level = downsampled

    def get_level(self, k: int) -> np.ndarray:
        """
        Get the elevation array at pyramid level k.

        Parameters
        ----------
        k : int
            Pyramid level (0 = finest resolution)

        Returns
        -------
        level : np.ndarray
            Elevation array at level k
        """
        if k < 0 or k >= self.num_levels:
            raise IndexError(f"Level {k} out of range [0, {self.num_levels-1}]")
        return self.levels[k]

    def get_shape(self, k: int) -> Tuple[int, int]:
        """Get shape of pyramid level k."""
        return self.levels[k].shape

    def get_resolution(self, k: int, base_resolution: float = 1.0) -> float:
        """
        Get the resolution (cell size) at pyramid level k.

        Parameters
        ----------
        k : int
            Pyramid level
        base_resolution : float
            Cell size at level 0 in meters

        Returns
        -------
        resolution : float
            Cell size at level k in meters
        """
        return base_resolution * (2 ** k)

    def upsample_level(self, k: int, target_level: int = 0) -> np.ndarray:
        """
        Upsample a coarse pyramid level to finer resolution.

        Uses zoom interpolation to expand upward through pyramid.

        Parameters
        ----------
        k : int
            Source pyramid level
        target_level : int
            Target level (usually 0 for base resolution)

        Returns
        -------
        upsampled : np.ndarray
            Upsampled elevation array
        """
        if target_level < k:
            raise ValueError("Target level must be coarser than source")

        current = self.levels[k].copy()

        # Upsample through intermediate levels
        for level in range(k + 1, target_level + 1):
            target_shape = self.levels[level - 1].shape
            current = zoom(current, 2, order=1)  # Linear interpolation
            # Trim to exact target shape
            current = current[:target_shape[0], :target_shape[1]]

        return current

    def compute_differential_pyramid(self) -> List[np.ndarray]:
        """
        Compute differential (Laplacian) pyramid.

        Each level stores the difference between consecutive Gaussian levels.
        This representation is more suitable for p-adic encoding as it captures
        detail coefficients at each scale.

        Returns
        -------
        differential_levels : List[np.ndarray]
            List of differential pyramid levels
        """
        differential = []

        for k in range(self.num_levels - 1):
            current = self.levels[k]
            coarse = self.levels[k + 1]

            # Upsample coarse level to match current resolution
            upsampled_coarse = zoom(coarse, 2, order=1)
            upsampled_coarse = upsampled_coarse[:current.shape[0], :current.shape[1]]

            # Compute difference
            detail = current - upsampled_coarse
            differential.append(detail)

        # Last level has no coarser level
        differential.append(self.levels[-1])

        return differential

    def compute_local_statistics(self, k: int, window_size: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute local mean and variance at pyramid level k.

        Parameters
        ----------
        k : int
            Pyramid level
        window_size : int
            Window size for local statistics

        Returns
        -------
        local_mean : np.ndarray
            Local mean elevation
        local_variance : np.ndarray
            Local variance of elevation
        """
        level = self.levels[k]
        pad = window_size // 2

        local_mean = np.zeros_like(level)
        local_variance = np.zeros_like(level)

        for i in range(pad, level.shape[0] - pad):
            for j in range(pad, level.shape[1] - pad):
                window = level[i-pad:i+pad+1, j-pad:j+pad+1]
                local_mean[i, j] = np.mean(window)
                local_variance[i, j] = np.var(window)

        return local_mean, local_variance

    def compute_variance_profile(self, i: int, j: int, window_size: int = 5) -> np.ndarray:
        """
        Compute variance profile across scales at location (i, j).

        This is used for computing hierarchical variance-based fractal density.

        Parameters
        ----------
        i, j : int
            Pixel coordinates at base resolution
        window_size : int
            Local neighborhood window size

        Returns
        -------
        variance_profile : np.ndarray
            Variance at each pyramid level
        """
        variance_profile = np.zeros(self.num_levels)

        for k in range(self.num_levels):
            # Map base coordinates to level k
            i_k = i // (2 ** k)
            j_k = j // (2 ** k)

            level = self.levels[k]
            pad = window_size // 2

            # Clamp coordinates to valid range
            i_k = np.clip(i_k, pad, level.shape[0] - pad - 1)
            j_k = np.clip(j_k, pad, level.shape[1] - pad - 1)

            window = level[i_k-pad:i_k+pad+1, j_k-pad:j_k+pad+1]
            variance_profile[k] = np.var(window)

        return variance_profile

    def compute_fractal_slope(self, variance_profile: np.ndarray) -> Tuple[float, float]:
        """
        Compute fractal dimension from variance profile using power-law scaling.

        For fractal terrain: variance ~ scale^beta
        Fractal dimension D = 3 - beta/2

        Parameters
        ----------
        variance_profile : np.ndarray
            Variance at each scale

        Returns
        -------
        slope : float
            Slope of log-log variance vs scale curve
        fractal_dimension : float
            Estimated fractal dimension
        """
        # Remove zero variances to avoid log(0)
        valid_indices = np.where(variance_profile > 1e-10)[0]

        if len(valid_indices) < 2:
            return 0.0, 2.0

        scales = valid_indices.astype(float)
        variances = variance_profile[valid_indices]

        # Log-log regression
        log_scales = np.log(scales + 1)  # +1 to avoid log(0) at level 0
        log_variances = np.log(variances)

        # Fit line: log_var = slope * log_scale + intercept
        coeffs = np.polyfit(log_scales, log_variances, 1)
        slope = coeffs[0]

        # Fractal dimension estimate
        fractal_dimension = 3 - slope / 2

        return float(slope), float(fractal_dimension)

    def save_pyramid(self, filepath: str) -> None:
        """
        Save pyramid levels to HDF5 file for efficient I/O.

        Parameters
        ----------
        filepath : str
            Output HDF5 file path
        """
        import h5py

        with h5py.File(filepath, 'w') as f:
            f.attrs['num_levels'] = self.num_levels
            for k, level in enumerate(self.levels):
                f.create_dataset(f'level_{k}', data=level, compression='gzip')

    @classmethod
    def load_pyramid(cls, filepath: str) -> 'GaussianPyramid':
        """
        Load pyramid from HDF5 file.

        Parameters
        ----------
        filepath : str
            Input HDF5 file path

        Returns
        -------
        pyramid : GaussianPyramid
            Loaded Gaussian pyramid object
        """
        import h5py

        with h5py.File(filepath, 'r') as f:
            num_levels = f.attrs['num_levels']
            levels = [np.array(f[f'level_{k}']) for k in range(num_levels)]

        pyramid = cls.__new__(cls)
        pyramid.levels = levels
        pyramid.num_levels = num_levels

        return pyramid

    def __repr__(self) -> str:
        """String representation of pyramid."""
        level_0_shape = self.levels[0].shape
        level_n_shape = self.levels[-1].shape
        return (f"GaussianPyramid(levels={self.num_levels}, "
                f"base_shape={level_0_shape}, "
                f"coarsest_shape={level_n_shape})")


def build_gaussian_pyramid(dem: np.ndarray, num_levels: Optional[int] = None) -> GaussianPyramid:
    """
    Convenience function to build a Gaussian pyramid from a DEM.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    num_levels : int, optional
        Number of pyramid levels

    Returns
    -------
    pyramid : GaussianPyramid
        Built Gaussian pyramid
    """
    return GaussianPyramid(dem, num_levels)
