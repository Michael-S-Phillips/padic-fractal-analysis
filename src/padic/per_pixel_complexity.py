"""
Per-pixel fractal complexity measures using p-adic mathematics.

Implements four distinct methods for computing local fractal complexity
at each pixel using p-adic concepts, hierarchical wavelets, and ultrametric distances.

Methods:
1. P-Adic Local Roughness: Variance in p-adic balls (2^k scaling)
2. P-Adic Hierarchical Variance: Entropy of variance distribution across scales
3. Wavelet Spectral Entropy: Energy spectrum of wavelet coefficients
4. Ultrametric Fractal Dimension: Dimension from quadtree ultrametric structure
"""

import numpy as np
from typing import Tuple, Optional
from scipy.ndimage import zoom
import warnings


class PerPixelComplexity:
    """
    Compute four per-pixel fractal complexity measures using p-adic mathematics.
    """

    def __init__(self, dem: np.ndarray, pyramid=None, quadtree=None):
        """
        Initialize per-pixel complexity calculator.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        pyramid : GaussianPyramid, optional
            Gaussian pyramid for wavelet analysis
        quadtree : PadicQuadtree, optional
            P-adic quadtree for ultrametric analysis
        """
        self.dem = dem
        self.pyramid = pyramid
        self.quadtree = quadtree
        self.height, self.width = dem.shape

    def padic_local_roughness(self, max_radius: int = 4) -> np.ndarray:
        """
        Compute p-adic local roughness at each pixel.

        Measures elevation variability in p-adic balls of radius 2^k
        around each pixel, weighted inversely by radius.

        Mathematical basis:
        For pixel (i,j) at each scale k:
            radius_k = 2^k
            var_k = variance in (2*radius_k × 2*radius_k) window
            weight_k = 1 / 2^k

        roughness = Σ(var_k * weight_k) / Σ(weight_k)

        Parameters
        ----------
        max_radius : int
            Maximum exponent for p-adic radius (max radius = 2^max_radius)

        Returns
        -------
        roughness_map : np.ndarray
            Per-pixel roughness values in [0, 1]
        """
        roughness_map = np.zeros_like(self.dem, dtype=np.float32)

        # Precompute normalized weights for efficiency
        weights = np.array([1.0 / (2.0 ** k) for k in range(max_radius)])
        weight_sum = np.sum(weights)

        for i in range(self.height):
            for j in range(self.width):
                weighted_var = 0.0

                for k in range(max_radius):
                    radius = 2 ** k

                    # Extract p-adic ball around pixel
                    i_min = max(0, i - radius)
                    i_max = min(self.height, i + radius + 1)
                    j_min = max(0, j - radius)
                    j_max = min(self.width, j + radius + 1)

                    window = self.dem[i_min:i_max, j_min:j_max]

                    # Compute variance in this p-adic ball
                    if window.size > 0:
                        var_k = np.var(window)
                        weighted_var += var_k * weights[k]

                # Normalize by weight sum
                roughness = weighted_var / weight_sum
                roughness_map[i, j] = np.clip(roughness, 0.0, 1.0)

        return roughness_map

    def padic_variance_hierarchy(self, max_level: int = 5) -> np.ndarray:
        """
        Compute p-adic hierarchical variance entropy at each pixel.

        Measures how elevation variance distributes across p-adic scales,
        using Shannon entropy of the variance distribution.

        Mathematical basis:
        For pixel (i,j) at each level k:
            radius_k = 2^k
            var_k = variance in (2^k+1 × 2^k+1) window
            ratio_k = var_k / Σ(var_k)

        entropy = -Σ(ratio_k * log(ratio_k))
        normalized = entropy / log(max_level)

        Parameters
        ----------
        max_level : int
            Maximum pyramid level to analyze

        Returns
        -------
        entropy_map : np.ndarray
            Per-pixel entropy values in [0, 1]
        """
        entropy_map = np.zeros_like(self.dem, dtype=np.float32)

        for i in range(self.height):
            for j in range(self.width):
                variances = []

                for level in range(max_level):
                    radius = 2 ** level

                    # Extract p-adic ball
                    i_min = max(0, i - radius)
                    i_max = min(self.height, i + radius + 1)
                    j_min = max(0, j - radius)
                    j_max = min(self.width, j + radius + 1)

                    window = self.dem[i_min:i_max, j_min:j_max]

                    if window.size > 0:
                        var_level = np.var(window)
                        variances.append(var_level)
                    else:
                        variances.append(0.0)

                # Normalize variances to probabilities
                total_var = np.sum(variances)
                if total_var > 1e-10:
                    probs = np.array(variances) / total_var
                else:
                    probs = np.ones(len(variances)) / len(variances)

                # Compute Shannon entropy
                entropy = 0.0
                for p in probs:
                    if p > 1e-10:
                        entropy -= p * np.log(p)

                # Normalize by maximum entropy
                max_entropy = np.log(max_level)
                if max_entropy > 0:
                    normalized_entropy = entropy / max_entropy
                else:
                    normalized_entropy = 0.0

                entropy_map[i, j] = np.clip(normalized_entropy, 0.0, 1.0)

        return entropy_map

    def wavelet_spectral_entropy(self) -> np.ndarray:
        """
        Compute wavelet spectral entropy at each pixel.

        Uses wavelet coefficients from Gaussian pyramid to compute
        energy spectrum and its Shannon entropy.

        Mathematical basis:
        For pixel (i,j) at each wavelet level k:
            coeff = detail coefficient at (i,j), level k
            energy_k = |coeff|^2
            prob_k = energy_k / Σ(energy_k)

        entropy = -Σ(prob_k * log(prob_k))
        normalized = entropy / log(num_levels)

        Returns
        -------
        entropy_map : np.ndarray
            Per-pixel spectral entropy in [0, 1]
        """
        if self.pyramid is None:
            raise ValueError("GaussianPyramid required for spectral entropy")

        # Compute wavelet detail coefficients if not already done
        if not hasattr(self.pyramid, 'detail_coeffs') or self.pyramid.detail_coeffs is None:
            from .wavelet import PadicWaveletTransform
            wavelet = PadicWaveletTransform(self.pyramid)
            approx, detail = wavelet.forward_transform()
            detail_coeffs = detail
        else:
            detail_coeffs = self.pyramid.detail_coeffs

        num_levels = len(detail_coeffs)
        entropy_map = np.zeros_like(self.dem, dtype=np.float32)

        for i in range(self.height):
            for j in range(self.width):
                energies = []

                for level in range(num_levels):
                    coeff_map = detail_coeffs[level]

                    # Handle dimension mismatch by downsampling
                    if coeff_map.shape[0] <= i or coeff_map.shape[1] <= j:
                        # Downsample coeff_map to match DEM resolution
                        scale_i = self.height / coeff_map.shape[0]
                        scale_j = self.width / coeff_map.shape[1]
                        i_down = int(i / scale_i)
                        j_down = int(j / scale_j)

                        i_down = np.clip(i_down, 0, coeff_map.shape[0] - 1)
                        j_down = np.clip(j_down, 0, coeff_map.shape[1] - 1)

                        coeff = coeff_map[i_down, j_down]
                    else:
                        coeff = coeff_map[i, j]

                    energy = coeff ** 2
                    energies.append(energy)

                # Normalize energies to probabilities
                total_energy = np.sum(energies)
                if total_energy > 1e-10:
                    probs = np.array(energies) / total_energy
                else:
                    probs = np.ones(len(energies)) / len(energies)

                # Compute Shannon entropy
                entropy = 0.0
                for p in probs:
                    if p > 1e-10:
                        entropy -= p * np.log(p)

                # Normalize by maximum entropy
                max_entropy = np.log(num_levels) if num_levels > 1 else 1.0
                if max_entropy > 0:
                    normalized_entropy = entropy / max_entropy
                else:
                    normalized_entropy = 0.0

                entropy_map[i, j] = np.clip(normalized_entropy, 0.0, 1.0)

        return entropy_map

    def ultrametric_fractal_dimension(self, samples: Optional[int] = None) -> np.ndarray:
        """
        Compute ultrametric fractal dimension from quadtree structure.

        Uses p-adic ultrametric distances and terrain roughness properties
        to estimate local fractal dimension based on hierarchical structure.

        Mathematical basis:
        For each scale k (block size 2^k):
            variance_k = variance in 2^k-sized block containing (i,j)
            distance_k = 2^(-k) (ultrametric distance scale)

        Fit log(variance) vs log(distance):
        Higher fractal dimension → variance grows faster with scale
        Lower fractal dimension → variance grows slower

        Parameters
        ----------
        samples : int, optional
            If provided, compute only for this many random pixels for speed

        Returns
        -------
        dimension_map : np.ndarray
            Per-pixel fractal dimension estimates in [2.0, 3.0] range
        """
        if self.quadtree is None:
            raise ValueError("PadicQuadtree required for ultrametric dimension")

        dimension_map = np.full_like(self.dem, dtype=np.float32, fill_value=2.5)

        if samples is None:
            sample_indices = [(i, j) for i in range(self.height) for j in range(self.width)]
        else:
            num_pixels = self.height * self.width
            sample_count = min(samples, num_pixels)
            indices = np.random.choice(num_pixels, sample_count, replace=False)
            sample_indices = [(idx // self.width, idx % self.width) for idx in indices]

        for i, j in sample_indices:
            # For each pixel, analyze variance at different scales using quadtree
            variances = []

            try:
                # Use quadtree to get variance at each level
                # quadtree stores pre-computed variances at each node
                for level in range(min(self.quadtree.max_depth + 1, 12)):  # Cap at 12 levels for stability
                    try:
                        # Get node at this level containing (i,j)
                        node = self.quadtree.find_node_at(i, j, target_level=level)

                        # Use the elevation variance stored in the node
                        # This is the variance within the spatial region of the node
                        var = node.elevation_variance
                        variances.append(max(var, 1e-10))  # Ensure positive for log
                    except:
                        # If level not reached, break
                        break

                # Fit log-log line: log(variance) vs log(distance)
                if len(variances) > 2:
                    # Remove zero/negative variances
                    valid_indices = [idx for idx, v in enumerate(variances) if v > 1e-10]

                    if len(valid_indices) > 2:
                        valid_vars = np.array([variances[idx] for idx in valid_indices])
                        valid_levels = np.array(valid_indices)

                        # Ultrametric distances: d = 2^(-level)
                        distances = 2.0 ** (-valid_levels)

                        log_vars = np.log(np.maximum(valid_vars, 1e-10))
                        log_distances = np.log(distances)

                        # Linear regression: log(variance) = slope * log(distance) + intercept
                        # For Brownian motion: slope ≈ 1.0 (dimension 2.0)
                        # For rougher fractals: slope > 1.0 (dimension > 2.0)
                        coeffs = np.polyfit(log_distances, log_vars, 1)
                        slope = coeffs[0]

                        # Map slope to dimension: dimension = 2.0 + slope/2
                        # slope=0 → dim=2.0, slope=1 → dim=2.5, slope=2 → dim=3.0
                        dimension = 2.0 + np.clip(slope / 2.0, 0.0, 1.0)
                    else:
                        dimension = 2.5
                else:
                    dimension = 2.5

                dimension_map[i, j] = dimension

            except Exception as e:
                # Use default if error
                dimension_map[i, j] = 2.5

        # If sampling, interpolate to full grid
        if samples is not None and samples < (self.height * self.width):
            from scipy.interpolate import griddata

            x = [idx[0] for idx in sample_indices]
            y = [idx[1] for idx in sample_indices]
            values = [dimension_map[i, j] for i, j in sample_indices]

            xi = np.arange(self.height)
            yi = np.arange(self.width)
            xi_grid, yi_grid = np.meshgrid(xi, yi)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dimension_map = griddata((x, y), values,
                                        (xi_grid, yi_grid),
                                        method='linear', fill_value=2.5).T

        return dimension_map

    def compute_all_methods(self, max_radius: int = 4, max_level: int = 5) -> dict:
        """
        Compute all four complexity methods.

        Parameters
        ----------
        max_radius : int
            Maximum radius for p-adic local roughness
        max_level : int
            Maximum level for hierarchical variance

        Returns
        -------
        results : dict
            Dictionary with keys:
            - 'padic_roughness': Local roughness map
            - 'padic_variance_hierarchy': Variance hierarchy entropy map
            - 'wavelet_spectral_entropy': Spectral entropy map
            - 'ultrametric_dimension': Fractal dimension map
        """
        results = {}

        print("Computing p-adic local roughness...")
        results['padic_roughness'] = self.padic_local_roughness(max_radius)

        print("Computing p-adic variance hierarchy...")
        results['padic_variance_hierarchy'] = self.padic_variance_hierarchy(max_level)

        if self.pyramid is not None:
            print("Computing wavelet spectral entropy...")
            results['wavelet_spectral_entropy'] = self.wavelet_spectral_entropy()
        else:
            print("Warning: Pyramid not provided, skipping wavelet spectral entropy")
            results['wavelet_spectral_entropy'] = None

        if self.quadtree is not None:
            print("Computing ultrametric fractal dimension...")
            results['ultrametric_dimension'] = self.ultrametric_fractal_dimension()
        else:
            print("Warning: Quadtree not provided, skipping ultrametric dimension")
            results['ultrametric_dimension'] = None

        return results

    def extract_sample_values(self, sample_coords: list) -> dict:
        """
        Extract complexity values at specific sample locations.

        Parameters
        ----------
        sample_coords : list
            List of (i, j) pixel coordinates

        Returns
        -------
        samples : dict
            Dictionary with complexity values at each sample location
        """
        results = self.compute_all_methods()

        samples = {
            'padic_roughness': [],
            'padic_variance_hierarchy': [],
            'wavelet_spectral_entropy': [],
            'ultrametric_dimension': []
        }

        for i, j in sample_coords:
            if 0 <= i < self.height and 0 <= j < self.width:
                samples['padic_roughness'].append(results['padic_roughness'][i, j])
                samples['padic_variance_hierarchy'].append(results['padic_variance_hierarchy'][i, j])

                if results['wavelet_spectral_entropy'] is not None:
                    samples['wavelet_spectral_entropy'].append(
                        results['wavelet_spectral_entropy'][i, j]
                    )

                if results['ultrametric_dimension'] is not None:
                    samples['ultrametric_dimension'].append(
                        results['ultrametric_dimension'][i, j]
                    )

        return samples
