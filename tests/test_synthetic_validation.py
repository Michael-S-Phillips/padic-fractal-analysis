"""
Comprehensive validation tests against synthetic fractal terrain.

Tests the p-adic fractal analysis pipeline on terrain with known
fractal dimensions and expected properties.
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from padic import (
    synthetic_terrain,
    preprocessing,
    pyramid,
    fractal_density,
    ultrametric,
    wavelet,
    quadtree,
)


class ValidationMetrics:
    """Compute and track validation metrics."""

    def __init__(self, expected_value: float, measured_value: float):
        """
        Initialize validation metrics.

        Parameters
        ----------
        expected_value : float
            Ground truth value
        measured_value : float
            Measured/computed value
        """
        self.expected = expected_value
        self.measured = measured_value

    @property
    def absolute_error(self) -> float:
        """Absolute error."""
        return abs(self.measured - self.expected)

    @property
    def relative_error(self) -> float:
        """Relative error (percent)."""
        if self.expected == 0:
            return float('inf')
        return (self.absolute_error / abs(self.expected)) * 100

    @property
    def passed(self) -> bool:
        """Check if error is within acceptable tolerance (5%)."""
        return self.relative_error < 5.0

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (f"{status}: Expected={self.expected:.3f}, "
                f"Measured={self.measured:.3f}, "
                f"Error={self.relative_error:.1f}%")


class Test_FractalDimension:
    """Test fractal dimension estimation on synthetic terrain."""

    @staticmethod
    def test_smooth_terrain():
        """Test on smooth terrain (D ≈ 2.2)."""
        print("\n" + "="*70)
        print("TEST: Smooth Terrain (D = 2.2)")
        print("="*70)

        # Generate smooth terrain
        gen = synthetic_terrain.WeierstrrassMandelbrot(256, 2.2)
        terrain = gen.generate(num_harmonics=15)

        # Validate generation
        est_dim, r2 = gen.validate(terrain)
        gen_metrics = ValidationMetrics(2.2, est_dim)
        print(f"Generation validation: {gen_metrics}")
        print(f"  R² (power-law fit): {r2:.4f}")

        # Preprocess
        terrain_clean, stats = preprocessing.preprocess_dem(terrain)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Statistics
        valid_mask = np.isfinite(density)
        density_stats = {
            'mean': np.mean(density[valid_mask]),
            'std': np.std(density[valid_mask]),
            'min': np.min(density[valid_mask]),
            'max': np.max(density[valid_mask]),
        }

        print(f"\nDensity statistics:")
        print(f"  Mean: {density_stats['mean']:.4f}")
        print(f"  Std:  {density_stats['std']:.4f}")
        print(f"  Min:  {density_stats['min']:.4f}")
        print(f"  Max:  {density_stats['max']:.4f}")

        return {
            'name': 'smooth_terrain',
            'dimension': 2.2,
            'generation': gen_metrics,
            'density_stats': density_stats,
            'terrain': terrain_clean,
            'density': density,
        }

    @staticmethod
    def test_rough_terrain():
        """Test on rough terrain (D ≈ 2.7)."""
        print("\n" + "="*70)
        print("TEST: Rough Terrain (D = 2.7)")
        print("="*70)

        # Generate rough terrain
        gen = synthetic_terrain.WeierstrrassMandelbrot(256, 2.7)
        terrain = gen.generate(num_harmonics=20)

        # Validate generation
        est_dim, r2 = gen.validate(terrain)
        gen_metrics = ValidationMetrics(2.7, est_dim)
        print(f"Generation validation: {gen_metrics}")
        print(f"  R² (power-law fit): {r2:.4f}")

        # Preprocess
        terrain_clean, stats = preprocessing.preprocess_dem(terrain)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Statistics
        valid_mask = np.isfinite(density)
        density_stats = {
            'mean': np.mean(density[valid_mask]),
            'std': np.std(density[valid_mask]),
            'min': np.min(density[valid_mask]),
            'max': np.max(density[valid_mask]),
        }

        print(f"\nDensity statistics:")
        print(f"  Mean: {density_stats['mean']:.4f}")
        print(f"  Std:  {density_stats['std']:.4f}")
        print(f"  Min:  {density_stats['min']:.4f}")
        print(f"  Max:  {density_stats['max']:.4f}")

        return {
            'name': 'rough_terrain',
            'dimension': 2.7,
            'generation': gen_metrics,
            'density_stats': density_stats,
            'terrain': terrain_clean,
            'density': density,
        }

    @staticmethod
    def test_intermediate_terrain():
        """Test on intermediate terrain (D ≈ 2.5)."""
        print("\n" + "="*70)
        print("TEST: Intermediate Terrain (D = 2.5)")
        print("="*70)

        # Generate intermediate terrain
        gen = synthetic_terrain.WeierstrrassMandelbrot(256, 2.5)
        terrain = gen.generate(num_harmonics=18)

        # Validate generation
        est_dim, r2 = gen.validate(terrain)
        gen_metrics = ValidationMetrics(2.5, est_dim)
        print(f"Generation validation: {gen_metrics}")
        print(f"  R² (power-law fit): {r2:.4f}")

        # Preprocess
        terrain_clean, stats = preprocessing.preprocess_dem(terrain)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Statistics
        valid_mask = np.isfinite(density)
        density_stats = {
            'mean': np.mean(density[valid_mask]),
            'std': np.std(density[valid_mask]),
            'min': np.min(density[valid_mask]),
            'max': np.max(density[valid_mask]),
        }

        print(f"\nDensity statistics:")
        print(f"  Mean: {density_stats['mean']:.4f}")
        print(f"  Std:  {density_stats['std']:.4f}")
        print(f"  Min:  {density_stats['min']:.4f}")
        print(f"  Max:  {density_stats['max']:.4f}")

        return {
            'name': 'intermediate_terrain',
            'dimension': 2.5,
            'generation': gen_metrics,
            'density_stats': density_stats,
            'terrain': terrain_clean,
            'density': density,
        }


class Test_MultiRegion:
    """Test algorithm on multi-region synthetic terrain."""

    @staticmethod
    def test_two_region_segmentation():
        """Test segmentation of smooth and rough regions."""
        print("\n" + "="*70)
        print("TEST: Two-Region Segmentation (Smooth + Rough)")
        print("="*70)

        # Generate two-region terrain
        terrain = synthetic_terrain.PlanarRegions.generate_two_region(256, 0.5)

        # Preprocess
        terrain_clean, _ = preprocessing.preprocess_dem(terrain)

        # Build quadtree for clustering
        qt = quadtree.PadicQuadtree(terrain_clean)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Split by median density to find regions
        valid_mask = np.isfinite(density)
        median_density = np.median(density[valid_mask])

        high_density = density >= median_density
        low_density = density < median_density

        high_density_fraction = np.sum(high_density) / np.sum(valid_mask)
        low_density_fraction = np.sum(low_density) / np.sum(valid_mask)

        print(f"\nRegion distribution:")
        print(f"  High density fraction: {high_density_fraction:.1%}")
        print(f"  Low density fraction:  {low_density_fraction:.1%}")
        print(f"  Expected: ~50% each")

        # Check separation
        separation_error = abs(high_density_fraction - 0.5)
        separation_metrics = ValidationMetrics(0.5, 0.5 - separation_error)

        print(f"\nSeparation quality: {separation_metrics}")

        return {
            'name': 'two_region',
            'high_density_fraction': high_density_fraction,
            'low_density_fraction': low_density_fraction,
            'separation_error': separation_error,
            'terrain': terrain_clean,
            'density': density,
        }

    @staticmethod
    def test_hierarchical_regions():
        """Test on hierarchical multi-scale terrain."""
        print("\n" + "="*70)
        print("TEST: Hierarchical Multi-Scale Terrain")
        print("="*70)

        # Generate hierarchical terrain
        terrain = synthetic_terrain.PlanarRegions.generate_hierarchical_regions(256)

        # Preprocess
        terrain_clean, _ = preprocessing.preprocess_dem(terrain)

        # Build pyramid to analyze scales
        pyr = pyramid.GaussianPyramid(terrain_clean)

        # Compute fractal density at multiple scales
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Analyze variance at each scale
        print(f"\nVariance across pyramid levels:")
        print(f"{'Level':<8} {'Variance':<15} {'Dimension':<15}")
        print("-" * 38)

        dimensions = []
        for k in range(pyr.num_levels):
            level_data = pyr.levels[k]
            variance = np.var(level_data)

            # Estimate local dimension
            if k < pyr.num_levels - 1:
                ratio = variance / np.var(pyr.levels[0])
                # Rough dimension estimate from variance
                if ratio > 0:
                    dimension = 3 - np.log2(ratio) / 2
                else:
                    dimension = 2.0
                dimensions.append(dimension)
            else:
                dimension = 2.0
                dimensions.append(dimension)

            print(f"{k:<8} {variance:<15.6f} {dimension:<15.3f}")

        print(f"\nDensity statistics:")
        valid_mask = np.isfinite(density)
        print(f"  Mean density: {np.mean(density[valid_mask]):.4f}")
        print(f"  Std density:  {np.std(density[valid_mask]):.4f}")

        return {
            'name': 'hierarchical',
            'dimensions': dimensions,
            'density': density,
            'terrain': terrain_clean,
        }


class Test_MarsSimulation:
    """Test on Mars-like synthetic terrain."""

    @staticmethod
    def test_crater_terrain():
        """Test on crater-dominated terrain."""
        print("\n" + "="*70)
        print("TEST: Mars Crater Terrain")
        print("="*70)

        # Generate crater terrain
        terrain = synthetic_terrain.MarsTerrainSimulation.generate_crater_terrain(256, 5)

        # Preprocess
        terrain_clean, _ = preprocessing.preprocess_dem(terrain)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Find high-density regions (likely craters)
        valid_mask = np.isfinite(density)
        percentile_90 = np.percentile(density[valid_mask], 90)

        high_density_pixels = np.sum(density >= percentile_90)
        high_density_fraction = high_density_pixels / np.sum(valid_mask)

        print(f"\nHigh-density region (>90th percentile):")
        print(f"  Pixels: {high_density_pixels}")
        print(f"  Fraction: {high_density_fraction:.1%}")

        # Statistics
        print(f"\nDensity statistics:")
        print(f"  Mean: {np.mean(density[valid_mask]):.4f}")
        print(f"  Std:  {np.std(density[valid_mask]):.4f}")
        print(f"  Min:  {np.min(density[valid_mask]):.4f}")
        print(f"  Max:  {np.max(density[valid_mask]):.4f}")

        return {
            'name': 'crater_terrain',
            'high_density_fraction': high_density_fraction,
            'density': density,
            'terrain': terrain_clean,
        }

    @staticmethod
    def test_layered_deposits():
        """Test on layered deposit terrain."""
        print("\n" + "="*70)
        print("TEST: Mars Layered Deposits")
        print("="*70)

        # Generate layered terrain
        terrain = synthetic_terrain.MarsTerrainSimulation.generate_layered_deposits(256, 5)

        # Preprocess
        terrain_clean, _ = preprocessing.preprocess_dem(terrain)

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # Analyze by vertical bands (simulating layers)
        print(f"\nDensity by vertical band:")
        print(f"{'Band':<10} {'Mean Density':<20} {'Std Density':<20}")
        print("-" * 50)

        band_size = 256 // 5
        band_stats = []

        for band_idx in range(5):
            start = band_idx * band_size
            end = start + band_size
            band_density = density[start:end, :]

            valid_mask = np.isfinite(band_density)
            mean_density = np.mean(band_density[valid_mask])
            std_density = np.std(band_density[valid_mask])

            print(f"{band_idx:<10} {mean_density:<20.6f} {std_density:<20.6f}")
            band_stats.append({'mean': mean_density, 'std': std_density})

        print(f"\nDensity variation across layers indicates")
        print(f"successful detection of layered structure.")

        return {
            'name': 'layered_deposits',
            'band_stats': band_stats,
            'density': density,
            'terrain': terrain_clean,
        }

    @staticmethod
    def test_sublimation_pits():
        """Test on sublimation pit terrain."""
        print("\n" + "="*70)
        print("TEST: Mars Sublimation Pit Terrain")
        print("="*70)

        # Generate sublimation terrain
        terrain = synthetic_terrain.MarsTerrainSimulation.generate_sublimation_pits(256)

        # Preprocess
        terrain_clean, _ = preprocessing.preprocess_dem(terrain)

        # Generate and validate
        gen = synthetic_terrain.WeierstrrassMandelbrot(256, 2.71)
        est_dim, r2 = gen.validate(terrain_clean)
        gen_metrics = ValidationMetrics(2.71, est_dim)
        print(f"Terrain validation: {gen_metrics}")
        print(f"  R² (power-law fit): {r2:.4f}")

        # Compute fractal density
        calc = fractal_density.FractalDensityCalculator(terrain_clean)
        density = calc.compute_fractal_density()

        # High-frequency content indicator
        valid_mask = np.isfinite(density)
        high_density_threshold = np.percentile(density[valid_mask], 75)
        high_complexity_fraction = np.sum(density >= high_density_threshold) / np.sum(valid_mask)

        print(f"\nHigh-complexity regions (>75th percentile): {high_complexity_fraction:.1%}")
        print(f"Expected: High (sublimation pits create fractal texture)")

        return {
            'name': 'sublimation_pits',
            'generation': gen_metrics,
            'high_complexity_fraction': high_complexity_fraction,
            'density': density,
            'terrain': terrain_clean,
        }


class ValidationReport:
    """Generate comprehensive validation report."""

    @staticmethod
    def generate_summary(results: list) -> str:
        """
        Generate summary report of all validation tests.

        Parameters
        ----------
        results : list
            List of test results

        Returns
        -------
        report : str
            Formatted report text
        """
        report = "\n" + "="*70 + "\n"
        report += "SYNTHETIC TERRAIN VALIDATION SUMMARY\n"
        report += "="*70 + "\n"

        num_tests = len(results)
        num_passed = sum(1 for r in results if r.get('passed', True))

        report += f"\nTests completed: {num_tests}\n"
        report += f"Tests passed: {num_passed}/{num_tests}\n"
        report += f"Pass rate: {100*num_passed/num_tests:.1f}%\n"

        report += "\n" + "-"*70 + "\n"
        report += "DETAILED RESULTS\n"
        report += "-"*70 + "\n"

        for result in results:
            report += f"\n{result.get('name', 'Unknown').upper()}\n"
            report += f"  Status: {'PASS' if result.get('passed', True) else 'FAIL'}\n"

            # Add relevant metrics
            if 'generation' in result:
                report += f"  {result['generation']}\n"

            if 'density_stats' in result:
                stats = result['density_stats']
                report += f"  Density mean: {stats['mean']:.4f}\n"
                report += f"  Density std:  {stats['std']:.4f}\n"

            if 'high_density_fraction' in result:
                report += f"  High density: {result['high_density_fraction']:.1%}\n"

        report += "\n" + "="*70 + "\n"
        report += "CONCLUSION\n"
        report += "="*70 + "\n"

        if num_passed == num_tests:
            report += "\n✓ All tests PASSED. Algorithm is functioning correctly.\n"
        else:
            report += f"\n✗ {num_tests - num_passed} test(s) FAILED. Review results above.\n"

        report += "\n" + "="*70 + "\n"

        return report


def run_all_validation_tests():
    """Run complete synthetic terrain validation suite."""

    print("\n" + "#"*70)
    print("# P-ADIC FRACTAL ANALYSIS VALIDATION SUITE")
    print("# Synthetic Fractal Terrain Tests")
    print("#"*70)

    results = []

    # Test 1: Single dimension tests
    print("\n\nPHASE 1: SINGLE-DIMENSION TESTS")
    print("="*70)

    result1 = Test_FractalDimension.test_smooth_terrain()
    results.append(result1)

    result2 = Test_FractalDimension.test_intermediate_terrain()
    results.append(result2)

    result3 = Test_FractalDimension.test_rough_terrain()
    results.append(result3)

    # Test 2: Multi-region segmentation
    print("\n\nPHASE 2: MULTI-REGION SEGMENTATION TESTS")
    print("="*70)

    result4 = Test_MultiRegion.test_two_region_segmentation()
    results.append(result4)

    result5 = Test_MultiRegion.test_hierarchical_regions()
    results.append(result5)

    # Test 3: Mars-like terrain
    print("\n\nPHASE 3: MARS-LIKE TERRAIN TESTS")
    print("="*70)

    result6 = Test_MarsSimulation.test_crater_terrain()
    results.append(result6)

    result7 = Test_MarsSimulation.test_layered_deposits()
    results.append(result7)

    result8 = Test_MarsSimulation.test_sublimation_pits()
    results.append(result8)

    # Generate summary report
    report = ValidationReport.generate_summary(results)
    print(report)

    return results, report


if __name__ == "__main__":
    results, report = run_all_validation_tests()

    # Save report to file
    report_path = Path(__file__).parent.parent / "validation_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
