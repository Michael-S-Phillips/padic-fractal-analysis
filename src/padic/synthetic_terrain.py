"""
Synthetic fractal terrain generation for algorithm validation and testing.

Generates Weierstrass-Mandelbrot and other synthetic fractal surfaces with
known fractal dimensions for validating algorithm accuracy.
"""

import numpy as np
from typing import Tuple, Optional


class WeierstrrassMandelbrot:
    """
    Generate Weierstrass-Mandelbrot fractal surfaces.

    Creates 2D terrain with specified fractal dimension via superposition
    of sinusoidal components with exponentially decreasing amplitudes.
    """

    def __init__(self, size: int = 256, fractal_dimension: float = 2.5):
        """
        Initialize Weierstrass-Mandelbrot generator.

        Parameters
        ----------
        size : int
            Size of output grid (size x size)
        fractal_dimension : float
            Target fractal dimension (2.0-3.0)
        """
        self.size = size
        self.fractal_dimension = fractal_dimension

        # Validate fractal dimension
        if not 2.0 <= fractal_dimension <= 3.0:
            raise ValueError("Fractal dimension must be between 2.0 and 3.0")

        # Compute scaling exponent
        # D = 3 - beta/2, so beta = 2*(3-D)
        self.beta = 2 * (3 - fractal_dimension)

    def generate(self, num_harmonics: int = 20, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate Weierstrass-Mandelbrot surface.

        Parameters
        ----------
        num_harmonics : int
            Number of frequency components to use
        seed : int, optional
            Random seed for reproducibility

        Returns
        -------
        surface : np.ndarray
            Generated fractal terrain (size x size)
        """
        if seed is not None:
            np.random.seed(seed)

        x = np.linspace(0, 2*np.pi, self.size)
        y = np.linspace(0, 2*np.pi, self.size)
        X, Y = np.meshgrid(x, y)

        surface = np.zeros((self.size, self.size))

        # Superpose sinusoidal components
        for n in range(1, num_harmonics + 1):
            # Amplitude decreases with exponent beta
            amplitude = n ** (-self.beta / 2)

            # Random phase for each harmonic
            phase_x = np.random.uniform(0, 2*np.pi)
            phase_y = np.random.uniform(0, 2*np.pi)

            # Random direction
            freq_mag = 2 ** n
            freq_x = freq_mag * np.cos(phase_x)
            freq_y = freq_mag * np.sin(phase_y)

            # Add component
            surface += amplitude * np.sin(freq_x * X + freq_y * Y)

        # Normalize
        surface = (surface - np.mean(surface)) / np.std(surface)

        return surface

    def validate(self, surface: np.ndarray, num_scales: int = 10) -> Tuple[float, float]:
        """
        Validate that generated surface has correct fractal dimension.

        Estimates fractal dimension from variance scaling.

        Parameters
        ----------
        surface : np.ndarray
            Generated fractal surface
        num_scales : int
            Number of scales to test

        Returns
        -------
        estimated_dimension : float
            Estimated fractal dimension
        r_squared : float
            R² value for power-law fit
        """
        variances = []
        scales = []

        # Compute variance at different scales
        for scale in range(1, num_scales + 1):
            block_size = 2 ** scale

            if block_size >= min(surface.shape):
                break

            # Compute variance by downsampling
            downsampled = surface[::block_size, ::block_size]
            variances.append(np.var(downsampled))
            scales.append(scale)

        if len(scales) < 2:
            return 0.0, 0.0

        # Log-log regression
        log_scales = np.array(scales, dtype=float)
        log_variances = np.log(np.array(variances))

        coeffs = np.polyfit(log_scales, log_variances, 1)
        slope = coeffs[0]

        # Estimate dimension: D = 3 - beta/2, where variance ~ 2^(beta*scale)
        estimated_dimension = 3 - slope / 2

        # Compute R²
        y_pred = coeffs[0] * log_scales + coeffs[1]
        ss_res = np.sum((log_variances - y_pred) ** 2)
        ss_tot = np.sum((log_variances - np.mean(log_variances)) ** 2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return float(estimated_dimension), float(r_squared)


class PlanarRegions:
    """
    Generate synthetic terrain with distinct planar regions at different scales.
    """

    @staticmethod
    def generate_two_region(size: int = 256, smooth_fraction: float = 0.5) -> np.ndarray:
        """
        Generate terrain with smooth and rough regions.

        Parameters
        ----------
        size : int
            Size of output grid
        smooth_fraction : float
            Fraction of grid that is smooth (0.5 = half smooth, half rough)

        Returns
        -------
        surface : np.ndarray
            Synthetic terrain with two regions
        """
        surface = np.zeros((size, size))

        # Smooth region (lower fractal dimension)
        split = int(size * smooth_fraction)
        surface[:split, :] = np.random.normal(0, 0.1, (split, size))

        # Rough region (higher fractal dimension)
        # Generate rough region with same full size, then extract
        generator = WeierstrrassMandelbrot(size, 2.7)
        rough_full = generator.generate()
        surface[split:, :] = rough_full[split:, :]

        return surface

    @staticmethod
    def generate_hierarchical_regions(size: int = 256) -> np.ndarray:
        """
        Generate terrain with nested regions of varying complexity.

        Creates a multi-scale structure with smooth background and rough
        clusters at different scales.

        Parameters
        ----------
        size : int
            Size of output grid

        Returns
        -------
        surface : np.ndarray
            Hierarchical synthetic terrain
        """
        surface = np.zeros((size, size))

        # Base smooth terrain
        base = np.random.normal(0, 0.05, (size, size))

        # Add rough clusters at multiple scales
        for scale_factor in [64, 32, 16, 8]:
            num_clusters = (size // scale_factor) ** 2
            generator = WeierstrrassMandelbrot(scale_factor, 2.6)
            cluster = generator.generate(num_harmonics=10)

            # Place clusters at grid locations
            for i in range(0, size - scale_factor + 1, scale_factor):
                for j in range(0, size - scale_factor + 1, scale_factor):
                    surface[i:i+scale_factor, j:j+scale_factor] += cluster * 0.5

        return surface + base


class MarsTerrainSimulation:
    """
    Generate synthetic Mars-like terrain based on known characteristics.
    """

    @staticmethod
    def generate_crater_terrain(size: int = 512, impact_sites: int = 5) -> np.ndarray:
        """
        Generate terrain with impact craters.

        Parameters
        ----------
        size : int
            Size of output grid
        impact_sites : int
            Number of impact craters to add

        Returns
        -------
        surface : np.ndarray
            Crater-dominated synthetic terrain
        """
        # Base fractal terrain
        generator = WeierstrrassMandelbrot(size, 2.4)
        surface = generator.generate()

        # Add impact craters
        y, x = np.ogrid[:size, :size]

        for _ in range(impact_sites):
            # Random crater location and size
            cx = np.random.randint(0, size)
            cy = np.random.randint(0, size)
            radius = np.random.randint(10, 50)
            depth = np.random.uniform(0.5, 2.0)

            # Create crater depression
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            crater = -depth * np.exp(-dist**2 / (2 * radius**2))
            surface += crater

        return surface

    @staticmethod
    def generate_layered_deposits(size: int = 512, num_layers: int = 5) -> np.ndarray:
        """
        Generate terrain with exposed layered deposits.

        Simulates sedimentary sequences with distinct layers.

        Parameters
        ----------
        size : int
            Size of output grid
        num_layers : int
            Number of distinct layers

        Returns
        -------
        surface : np.ndarray
            Layered deposit terrain
        """
        surface = np.zeros((size, size))

        layer_height = size // num_layers

        for layer_idx in range(num_layers):
            start = layer_idx * layer_height
            end = start + layer_height

            # Each layer has different fractal properties
            fractal_dim = 2.3 + (layer_idx / num_layers) * 0.3

            # Generate full-size fractal, then extract layer-height strip
            generator = WeierstrrassMandelbrot(size, fractal_dim)
            layer_full = generator.generate()

            # Extract the appropriate layer section
            surface[start:end, :] = layer_full[start:end, :]

        return surface

    @staticmethod
    def generate_sublimation_pits(size: int = 512) -> np.ndarray:
        """
        Generate terrain with CO₂ sublimation pit patterns.

        Simulates high-frequency roughness from polar region processes.

        Parameters
        ----------
        size : int
            Size of output grid

        Returns
        -------
        surface : np.ndarray
            Sublimation-dominated terrain
        """
        # High-frequency fractal noise (dimension near 2.7)
        generator = WeierstrrassMandelbrot(size, 2.71)
        surface = generator.generate(num_harmonics=25)

        # Add characteristic length scales (5m and 30m pits)
        y, x = np.ogrid[:size, :size]

        # Simulate pit patterns at characteristic scales
        num_pits_coarse = 50
        num_pits_fine = 300

        # Coarse pits (~30m scale equivalent)
        for _ in range(num_pits_coarse):
            cx = np.random.randint(0, size)
            cy = np.random.randint(0, size)
            radius = np.random.randint(10, 20)

            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            pit = -0.3 * np.exp(-dist**2 / (2 * radius**2))
            surface += pit

        # Fine pits (~5m scale equivalent)
        for _ in range(num_pits_fine):
            cx = np.random.randint(0, size)
            cy = np.random.randint(0, size)
            radius = np.random.randint(2, 5)

            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            pit = -0.1 * np.exp(-dist**2 / (2 * radius**2))
            surface += pit

        return surface


class TestSuite:
    """
    Complete test suite for algorithm validation.
    """

    @staticmethod
    def create_test_cases() -> dict:
        """
        Create standard test cases for algorithm validation.

        Returns
        -------
        test_cases : dict
            Dictionary of named test cases with known properties
        """
        test_cases = {}

        # Test case 1: Pure smooth terrain
        test_cases['smooth'] = {
            'surface': WeierstrrassMandelbrot(256, 2.2).generate(),
            'expected_dimension': 2.2,
            'description': 'Smooth terrain (low complexity)'
        }

        # Test case 2: Pure rough terrain
        test_cases['rough'] = {
            'surface': WeierstrrassMandelbrot(256, 2.7).generate(),
            'expected_dimension': 2.7,
            'description': 'Rough terrain (high complexity)'
        }

        # Test case 3: Two regions
        test_cases['two_region'] = {
            'surface': PlanarRegions.generate_two_region(256, 0.5),
            'expected_regions': 2,
            'description': 'Smooth and rough regions'
        }

        # Test case 4: Hierarchical
        test_cases['hierarchical'] = {
            'surface': PlanarRegions.generate_hierarchical_regions(256),
            'expected_dimensions': [2.2, 2.5, 2.7],
            'description': 'Multi-scale hierarchical terrain'
        }

        # Test case 5: Craters
        test_cases['craters'] = {
            'surface': MarsTerrainSimulation.generate_crater_terrain(256, 5),
            'expected_feature': 'impact_craters',
            'description': 'Impact crater-dominated terrain'
        }

        # Test case 6: Layers
        test_cases['layers'] = {
            'surface': MarsTerrainSimulation.generate_layered_deposits(256, 5),
            'expected_feature': 'layered_deposits',
            'description': 'Stratified layered deposits'
        }

        # Test case 7: Sublimation pits
        test_cases['sublimation'] = {
            'surface': MarsTerrainSimulation.generate_sublimation_pits(256),
            'expected_dimension': 2.71,
            'description': 'CO₂ sublimation pit terrain'
        }

        return test_cases

    @staticmethod
    def generate_validation_report(test_cases: dict, algorithm_results: dict) -> str:
        """
        Generate validation report comparing expected vs. measured results.

        Parameters
        ----------
        test_cases : dict
            Known test cases with expected properties
        algorithm_results : dict
            Algorithm results on test cases

        Returns
        -------
        report : str
            Validation report text
        """
        report = "="*60 + "\n"
        report += "ALGORITHM VALIDATION REPORT\n"
        report += "="*60 + "\n\n"

        for test_name, test_data in test_cases.items():
            report += f"Test: {test_name}\n"
            report += f"Description: {test_data['description']}\n"

            if test_name in algorithm_results:
                result = algorithm_results[test_name]
                report += f"Expected: {test_data.get('expected_dimension', 'N/A')}\n"
                report += f"Measured: {result.get('measured_dimension', 'N/A')}\n"
                report += f"Error: {result.get('error', 'N/A')}\n"
            else:
                report += "Results: NOT RUN\n"

            report += "-"*60 + "\n"

        return report
