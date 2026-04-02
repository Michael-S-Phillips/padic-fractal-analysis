"""
P-adic wavelet transform and analysis.

Implements fast hierarchical wavelet decomposition exploiting tree structure
of p-adic spaces for O(n log n) transforms with perfect space-scale localization.
"""

import numpy as np
from scipy.ndimage import zoom
from typing import List, Tuple, Optional
from .pyramid import GaussianPyramid


class PadicWaveletTransform:
    """
    Fast p-adic wavelet transform using hierarchical pyramid decomposition.

    For p=2, this produces Haar-like wavelets on dyadic grids with O(n log n)
    complexity via tree-based algorithms.
    """

    def __init__(self, pyramid: GaussianPyramid):
        """
        Initialize wavelet transform from Gaussian pyramid.

        Parameters
        ----------
        pyramid : GaussianPyramid
            Hierarchical Gaussian pyramid representation
        """
        self.pyramid = pyramid
        self.num_levels = pyramid.num_levels
        self.approximation_coeffs: List[np.ndarray] = []
        self.detail_coeffs: List[np.ndarray] = []

    def forward_transform(self) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Perform forward wavelet decomposition.

        Computes approximation and detail coefficients at each level.

        Returns
        -------
        approximation_coeffs : List[np.ndarray]
            Approximation (low-pass) coefficients
        detail_coeffs : List[np.ndarray]
            Detail (high-pass) coefficients
        """
        self.approximation_coeffs = []
        self.detail_coeffs = []

        # Finest level approximation is the base pyramid level
        current_approx = self.pyramid.levels[0].copy()
        self.approximation_coeffs.append(current_approx)

        # Decompose through pyramid levels
        for k in range(1, self.num_levels):
            coarse = self.pyramid.levels[k]

            # Upsample coarse to match current resolution
            upsampled_coarse = zoom(coarse, 2, order=1)
            upsampled_coarse = upsampled_coarse[:current_approx.shape[0], :current_approx.shape[1]]

            # Detail coefficients are the difference
            detail = current_approx - upsampled_coarse
            self.detail_coeffs.append(detail)

            # Next approximation is the coarse level
            current_approx = coarse

            self.approximation_coeffs.append(current_approx)

        return self.approximation_coeffs, self.detail_coeffs

    def inverse_transform(self) -> np.ndarray:
        """
        Perform inverse wavelet reconstruction.

        Reconstructs original signal from approximation and detail coefficients.

        Returns
        -------
        reconstructed : np.ndarray
            Reconstructed elevation data at base resolution
        """
        if not self.detail_coeffs or not self.approximation_coeffs:
            raise ValueError("Must run forward_transform first")

        # Start from coarsest level
        current = self.approximation_coeffs[-1].copy()

        # Reconstruct upward through levels
        for k in range(self.num_levels - 2, 0, -1):
            # Upsample current approximation
            upsampled = zoom(current, 2, order=1)
            target_shape = self.approximation_coeffs[k].shape
            upsampled = upsampled[:target_shape[0], :target_shape[1]]

            # Add detail coefficients
            current = upsampled + self.detail_coeffs[k - 1]

        return current

    def get_wavelet_coefficients(self) -> np.ndarray:
        """
        Get all wavelet coefficients as a matrix.

        Rows are scales, columns are spatial positions (flattened).

        Returns
        -------
        coefficients : np.ndarray
            All wavelet coefficients
        """
        if not self.detail_coeffs:
            self.forward_transform()

        # Flatten detail coefficients at each level
        all_coeffs = []

        for detail in self.detail_coeffs:
            all_coeffs.append(detail.flatten())

        # Pad to equal length
        max_len = max(len(c) for c in all_coeffs)
        padded_coeffs = []

        for coeffs in all_coeffs:
            padded = np.zeros(max_len)
            padded[:len(coeffs)] = coeffs
            padded_coeffs.append(padded)

        return np.array(padded_coeffs)

    def compute_energy(self) -> np.ndarray:
        """
        Compute energy spectrum across scales.

        Energy at scale k is the sum of squared wavelet coefficients.

        Returns
        -------
        energy : np.ndarray
            Energy at each scale
        """
        if not self.detail_coeffs:
            self.forward_transform()

        energy = np.zeros(len(self.detail_coeffs))

        for k, detail in enumerate(self.detail_coeffs):
            energy[k] = np.sum(detail ** 2) / detail.size

        return energy

    def compute_entropy(self) -> float:
        """
        Compute total entropy of wavelet decomposition.

        Measures how concentrated the energy is across scales.

        Returns
        -------
        entropy : float
            Shannon entropy of wavelet coefficients
        """
        if not self.detail_coeffs:
            self.forward_transform()

        # Compute energy at each scale
        energy = self.compute_energy()

        # Normalize to get probability distribution
        total_energy = np.sum(energy)
        if total_energy == 0:
            return 0.0

        probabilities = energy / total_energy

        # Compute Shannon entropy: H = -sum(p * log(p))
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * np.log2(p)

        return float(entropy)


class WaveletModulusMaxima:
    """
    Wavelet Transform Modulus Maxima (WTMM) method for multifractal analysis.

    Identifies local maxima of wavelet coefficients and tracks them across scales
    to estimate local Hölder exponents and singularity spectrum.
    """

    def __init__(self, wavelet_transform: PadicWaveletTransform):
        """
        Initialize WTMM analysis.

        Parameters
        ----------
        wavelet_transform : PadicWaveletTransform
            Computed wavelet transform
        """
        self.wavelet_transform = wavelet_transform
        self.detail_coeffs = wavelet_transform.detail_coeffs
        self.maxima_lines: List[List[Tuple[int, int, float]]] = []

    def detect_modulus_maxima(self) -> List[np.ndarray]:
        """
        Detect local maxima of wavelet coefficient moduli.

        At each scale, identifies locations where |W(x,γ)| is local maximum
        in the direction of steepest gradient.

        Returns
        -------
        maxima_masks : List[np.ndarray]
            Boolean masks of maxima at each scale
        """
        maxima_masks = []

        for detail in self.detail_coeffs:
            # Compute absolute values
            abs_detail = np.abs(detail)

            # Find local maxima using morphological operations
            from scipy.ndimage import maximum_filter

            local_max = maximum_filter(abs_detail, size=3) == abs_detail
            maxima_masks.append(local_max)

        return maxima_masks

    def compute_holder_exponent(self, i: int, j: int, window_size: int = 5) -> float:
        """
        Estimate Hölder exponent at location (i, j).

        Hölder exponent α characterizes local regularity via |W(γ,x)| ~ 2^(αγ).

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        window_size : int
            Window size for local estimation

        Returns
        -------
        alpha : float
            Hölder exponent (0 = smooth, <1 = non-differentiable)
        """
        coeffs_at_location = []
        scales = []

        for k, detail in enumerate(self.detail_coeffs):
            # Map base coordinates to this scale
            scale_factor = 2 ** k
            i_k = i // scale_factor
            j_k = j // scale_factor

            # Clamp to valid range
            i_k = np.clip(i_k, 0, detail.shape[0] - 1)
            j_k = np.clip(j_k, 0, detail.shape[1] - 1)

            # Get modulus
            modulus = np.abs(detail[i_k, j_k])
            if modulus > 0:
                coeffs_at_location.append(np.log2(modulus))
                scales.append(k)

        if len(coeffs_at_location) < 2:
            return 0.0  # Default for insufficient data

        # Fit line in log-log space
        scales = np.array(scales, dtype=float)
        coeffs = np.array(coeffs_at_location)

        # Linear fit: log|W| = α*scale + const
        coeffs_fit = np.polyfit(scales, coeffs, 1)
        alpha = coeffs_fit[0]

        return float(alpha)

    def compute_singularity_spectrum(self, num_bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate local singularity spectrum D(α).

        Returns probability distribution of Hölder exponents across image.

        Parameters
        ----------
        num_bins : int
            Number of bins for histogram

        Returns
        -------
        alpha_values : np.ndarray
            Hölder exponent values
        spectrum : np.ndarray
            Probability density D(α)
        """
        # Sample Hölder exponents at random locations
        num_samples = min(100, self.detail_coeffs[0].size // 100)

        alphas = []
        indices = np.random.choice(self.detail_coeffs[0].size, num_samples, replace=False)

        for idx in indices:
            i = idx // self.detail_coeffs[0].shape[1]
            j = idx % self.detail_coeffs[0].shape[1]
            alpha = self.compute_holder_exponent(i, j)
            alphas.append(alpha)

        alphas = np.array(alphas)

        # Compute histogram
        spectrum, alpha_values = np.histogram(alphas, bins=num_bins)
        spectrum = spectrum / np.sum(spectrum)  # Normalize

        # Return bin centers
        alpha_centers = (alpha_values[:-1] + alpha_values[1:]) / 2

        return alpha_centers, spectrum

    def compute_local_fractal_dimension(self, i: int, j: int) -> float:
        """
        Compute local fractal dimension using Hölder exponent.

        D_local ~ 3 - α where α is the Hölder exponent.

        Parameters
        ----------
        i, j : int
            Pixel coordinates

        Returns
        -------
        D_local : float
            Local fractal dimension (2-3 typical for terrain)
        """
        alpha = self.compute_holder_exponent(i, j)
        D_local = 3 - alpha

        # Clamp to reasonable range
        D_local = np.clip(D_local, 2.0, 3.0)

        return float(D_local)


class MultifractalAnalysis:
    """
    Complete multifractal analysis pipeline using wavelet transforms.
    """

    def __init__(self, dem: np.ndarray, num_pyramid_levels: Optional[int] = None):
        """
        Initialize multifractal analysis.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        num_pyramid_levels : int, optional
            Number of Gaussian pyramid levels
        """
        self.dem = dem
        self.pyramid = GaussianPyramid(dem, num_pyramid_levels)
        self.wavelet_transform = PadicWaveletTransform(self.pyramid)
        self.wtmm = WaveletModulusMaxima(self.wavelet_transform)

    def compute_fractal_map(self) -> np.ndarray:
        """
        Compute local fractal dimension at each pixel.

        Returns
        -------
        fractal_map : np.ndarray
            Local fractal dimension at each location
        """
        self.wavelet_transform.forward_transform()

        fractal_map = np.zeros_like(self.dem)

        # Sample every N pixels for efficiency
        step = max(1, self.dem.shape[0] // 100)

        for i in range(0, self.dem.shape[0], step):
            for j in range(0, self.dem.shape[1], step):
                if np.isfinite(self.dem[i, j]):
                    D = self.wtmm.compute_local_fractal_dimension(i, j)
                    fractal_map[i, j] = D

        # Interpolate to full resolution
        from scipy.interpolate import griddata

        valid_mask = fractal_map != 0
        if np.any(valid_mask):
            coords = np.where(valid_mask)
            values = fractal_map[valid_mask]

            # Create grid for interpolation
            i_grid, j_grid = np.mgrid[0:self.dem.shape[0], 0:self.dem.shape[1]]
            fractal_map_interp = griddata(
                (coords[0], coords[1]), values,
                (i_grid, j_grid),
                method='linear'
            )

            # Fill any remaining NaN with nearest neighbor
            mask = np.isnan(fractal_map_interp)
            fractal_map_interp[mask] = griddata(
                (coords[0], coords[1]), values,
                (i_grid[mask], j_grid[mask]),
                method='nearest'
            )

            fractal_map = fractal_map_interp

        return fractal_map

    def compute_energy_spectrum(self) -> np.ndarray:
        """
        Compute energy spectrum across scales.

        Returns
        -------
        spectrum : np.ndarray
            Energy at each wavelet scale
        """
        self.wavelet_transform.forward_transform()
        return self.wavelet_transform.compute_energy()
