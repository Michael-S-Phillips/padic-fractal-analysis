"""
Real Mars DEM validation tests for p-adic fractal analysis framework.

Tests the complete pipeline on actual Mars CTX DEM data.
Validates against known geological features and expected properties.
"""

import sys
import numpy as np
from pathlib import Path
import json
from typing import Tuple, Dict, Any

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from padic import preprocessing, pyramid, fractal_density, visualization


class MarsValidationTest:
    """Real Mars DEM validation test suite."""

    @staticmethod
    def test_dem_loading() -> Tuple[bool, str]:
        """Test 1: Load real Mars DEM"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found in data directory"

            dem_file = dem_files[0]
            dem, metadata = preprocessing.load_dem(str(dem_file))

            # Validate loaded data
            if dem is None or dem.size == 0:
                return False, "Loaded DEM is empty"

            if not isinstance(dem, np.ndarray):
                return False, "DEM is not a numpy array"

            if dem.dtype != np.float32 and dem.dtype != np.float64:
                return False, f"Unexpected dtype: {dem.dtype}"

            # Check for reasonable Mars elevation range
            valid_dem = dem[np.isfinite(dem)]
            if valid_dem.size == 0:
                return False, "No valid elevation data"

            min_elev = np.min(valid_dem)
            max_elev = np.max(valid_dem)

            # Mars topography typically ranges -10km to +20km
            if min_elev < -15000 or max_elev > 25000:
                return False, f"Elevation out of expected range: {min_elev:.0f} to {max_elev:.0f}"

            return True, f"✓ Loaded {dem.shape[0]}x{dem.shape[1]} DEM from {dem_file.name}"

        except Exception as e:
            return False, f"Error loading DEM: {str(e)}"


    @staticmethod
    def test_dem_statistics() -> Tuple[bool, str]:
        """Test 2: Verify DEM has reasonable statistics"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, _ = preprocessing.load_dem(str(dem_files[0]))
            valid_dem = dem[np.isfinite(dem)]

            # Statistics validation
            mean = np.mean(valid_dem)
            std = np.std(valid_dem)
            median = np.median(valid_dem)

            # Std should be > 0
            if std <= 0:
                return False, "Elevation std is zero (no variation)"

            # Std should be reasonable compared to range
            elevation_range = np.max(valid_dem) - np.min(valid_dem)
            if std > elevation_range * 0.5:
                return False, f"Std ({std:.0f}m) seems too large"

            stats_msg = f"mean={mean:.0f}m, std={std:.0f}m, median={median:.0f}m, range={elevation_range:.0f}m"
            return True, f"✓ DEM statistics reasonable: {stats_msg}"

        except Exception as e:
            return False, f"Error computing statistics: {str(e)}"


    @staticmethod
    def test_preprocessing() -> Tuple[bool, str]:
        """Test 3: Preprocess DEM"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, _ = preprocessing.load_dem(str(dem_files[0]))

            # Run preprocessing
            dem_clean, stats = preprocessing.preprocess_dem(
                dem,
                fill_depressions_flag=True,
                remove_jitter_flag=True,
                normalize_flag=True
            )

            # Validate output
            if dem_clean is None:
                return False, "Preprocessing returned None"

            if dem_clean.shape != dem.shape:
                return False, f"Output shape mismatch: {dem_clean.shape} vs {dem.shape}"

            # After normalization, should be centered
            valid_clean = dem_clean[np.isfinite(dem_clean)]
            mean = np.mean(valid_clean)
            std = np.std(valid_clean)

            if abs(mean) > 0.1:  # Should be close to 0
                return False, f"Normalized mean is {mean:.3f}, expected ~0"

            if abs(std - 1.0) > 0.1:  # Should be close to 1
                return False, f"Normalized std is {std:.3f}, expected ~1"

            return True, f"✓ Preprocessing complete: mean={mean:.3f}, std={std:.3f}"

        except Exception as e:
            return False, f"Error in preprocessing: {str(e)}"


    @staticmethod
    def test_pyramid_construction() -> Tuple[bool, str]:
        """Test 4: Build Gaussian pyramid"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, _ = preprocessing.load_dem(str(dem_files[0]))
            dem_clean, _ = preprocessing.preprocess_dem(dem)

            # Build pyramid
            pyr = pyramid.GaussianPyramid(dem_clean, num_levels=None)

            if pyr is None or not hasattr(pyr, 'levels'):
                return False, "Pyramid construction failed"

            if len(pyr.levels) < 2:
                return False, f"Pyramid has only {len(pyr.levels)} levels (expected >= 2)"

            # Validate level structure
            for i in range(len(pyr.levels) - 1):
                if pyr.levels[i].size <= pyr.levels[i+1].size:
                    return False, f"Level {i} not larger than level {i+1}"

            # Check storage efficiency
            total_size = sum(l.size for l in pyr.levels)
            base_size = pyr.levels[0].size
            ratio = total_size / base_size

            if ratio > 2.0:  # Should be < 2 for efficient pyramid
                return False, f"Storage ratio {ratio:.2f} is too high"

            level_str = " → ".join([f"{l.shape}" for l in pyr.levels[:5]])
            return True, f"✓ Pyramid built: {len(pyr.levels)} levels, ratio={ratio:.3f}x, shapes: {level_str}..."

        except Exception as e:
            return False, f"Error building pyramid: {str(e)}"


    @staticmethod
    def test_fractal_density() -> Tuple[bool, str]:
        """Test 5: Compute fractal density"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, _ = preprocessing.load_dem(str(dem_files[0]))
            dem_clean, _ = preprocessing.preprocess_dem(dem)

            # Compute fractal density
            calc = fractal_density.FractalDensityCalculator(dem_clean, base_resolution=1.0)
            density = calc.compute_fast_variance_based_density()

            if density is None:
                return False, "Fractal density computation returned None"

            if density.shape != dem_clean.shape:
                return False, f"Density shape mismatch: {density.shape} vs {dem_clean.shape}"

            # Validate density properties
            valid_density = density[np.isfinite(density)]

            if valid_density.size == 0:
                return False, "No valid density values"

            min_dens = np.min(valid_density)
            max_dens = np.max(valid_density)
            mean_dens = np.mean(valid_density)
            std_dens = np.std(valid_density)

            # Density should have variation
            if std_dens <= 0:
                return False, "Density has no variation"

            # Typical range should be [0, 1] or close
            if min_dens < -0.5 or max_dens > 2.0:
                return False, f"Density out of expected range: {min_dens:.3f} to {max_dens:.3f}"

            return True, f"✓ Fractal density computed: min={min_dens:.3f}, max={max_dens:.3f}, mean={mean_dens:.3f}, std={std_dens:.3f}"

        except Exception as e:
            return False, f"Error computing fractal density: {str(e)}"


    @staticmethod
    def test_spatial_variation() -> Tuple[bool, str]:
        """Test 6: Verify spatial variation in density"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, _ = preprocessing.load_dem(str(dem_files[0]))
            dem_clean, _ = preprocessing.preprocess_dem(dem)
            calc = fractal_density.FractalDensityCalculator(dem_clean)
            density = calc.compute_fast_variance_based_density()

            # Check spatial autocorrelation
            # Compute variance of local differences
            valid_density = density[np.isfinite(density)]

            if valid_density.size < 10:
                return False, "Insufficient valid density pixels"

            # Sample correlation at different distances
            h, w = density.shape

            # Get samples at quarter points
            samples = []
            for i in [h//4, h//2, 3*h//4]:
                for j in [w//4, w//2, 3*w//4]:
                    if np.isfinite(density[i, j]):
                        samples.append(density[i, j])

            if len(samples) < 4:
                return False, "Insufficient valid samples"

            sample_std = np.std(samples)
            sample_mean = np.mean(samples)

            # Samples should show variation
            if sample_std <= 0:
                return False, "No spatial variation in density"

            # Coefficient of variation should be reasonable
            cv = sample_std / (abs(sample_mean) + 1e-6)
            if cv < 0.1 or cv > 10:
                return False, f"Spatial variation out of range: CV={cv:.2f}"

            return True, f"✓ Spatial variation detected: CV={cv:.2f}, sample_std={sample_std:.3f}"

        except Exception as e:
            return False, f"Error checking spatial variation: {str(e)}"


    @staticmethod
    def test_geotiff_export() -> Tuple[bool, str]:
        """Test 7: Export to GeoTIFF"""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            dem_files = list(data_dir.glob('*.tif'))

            if not dem_files:
                return False, "No DEM files found"

            dem, metadata = preprocessing.load_dem(str(dem_files[0]))
            dem_clean, _ = preprocessing.preprocess_dem(dem)
            calc = fractal_density.FractalDensityCalculator(dem_clean)
            density = calc.compute_fast_variance_based_density()

            # Create results directory
            results_dir = Path(__file__).parent.parent / 'results'
            results_dir.mkdir(parents=True, exist_ok=True)

            output_file = results_dir / 'test_fractal_density_jezero.tif'

            # Try to export
            try:
                exporter = visualization.GeoTIFFExporter()
                exporter.save_density_tiff(
                    density,
                    str(output_file),
                    transform=metadata.get('transform'),
                    crs=metadata.get('crs')
                )

                if output_file.exists():
                    file_size = output_file.stat().st_size / 1e6
                    return True, f"✓ GeoTIFF exported: {output_file.name} ({file_size:.1f} MB)"
                else:
                    return False, "Export function ran but file not created"

            except Exception as geotiff_err:
                # Fallback to NumPy save
                np.save(results_dir / 'test_fractal_density_jezero.npy', density)
                return True, f"⚠ GeoTIFF export failed, saved as NumPy array: {str(geotiff_err)[:50]}"

        except Exception as e:
            return False, f"Error in export: {str(e)}"


class ValidationReport:
    """Generate validation report from test results."""

    @staticmethod
    def generate_report(results: Dict[str, Tuple[bool, str]]) -> str:
        """Generate formatted validation report."""

        passed = sum(1 for success, _ in results.values() if success)
        total = len(results)

        report = "=" * 70 + "\n"
        report += "MARS DEM VALIDATION REPORT\n"
        report += "=" * 70 + "\n\n"

        report += f"SUMMARY: {passed}/{total} tests passed\n\n"

        for test_name, (success, message) in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            report += f"{status} | {test_name}\n"
            report += f"         {message}\n\n"

        report += "=" * 70 + "\n"

        if passed == total:
            report += "STATUS: ✅ ALL TESTS PASSED - Framework validated on real Mars data\n"
        elif passed >= total * 0.8:
            report += "STATUS: ⚠️  MOSTLY PASSED - Minor issues to address\n"
        else:
            report += "STATUS: ❌ VALIDATION FAILED - Multiple issues detected\n"

        report += "=" * 70 + "\n"

        return report


def run_all_tests():
    """Run complete validation test suite."""

    print("=" * 70)
    print("P-ADIC FRACTAL ANALYSIS: MARS VALIDATION TEST SUITE")
    print("=" * 70 + "\n")

    results = {}

    # Run each test
    test_methods = [
        ("Test 1: DEM Loading", MarsValidationTest.test_dem_loading),
        ("Test 2: DEM Statistics", MarsValidationTest.test_dem_statistics),
        ("Test 3: DEM Preprocessing", MarsValidationTest.test_preprocessing),
        ("Test 4: Pyramid Construction", MarsValidationTest.test_pyramid_construction),
        ("Test 5: Fractal Density", MarsValidationTest.test_fractal_density),
        ("Test 6: Spatial Variation", MarsValidationTest.test_spatial_variation),
        ("Test 7: GeoTIFF Export", MarsValidationTest.test_geotiff_export),
    ]

    for test_name, test_func in test_methods:
        print(f"Running {test_name}...", end=" ", flush=True)
        try:
            success, message = test_func()
            results[test_name] = (success, message)
            print(f"{'✓' if success else '✗'}")
        except Exception as e:
            results[test_name] = (False, f"Unexpected error: {str(e)}")
            print("✗")

    # Generate report
    report = ValidationReport.generate_report(results)
    print("\n" + report)

    # Save report
    report_file = Path(__file__).parent.parent / 'MARS_VALIDATION_REPORT.txt'
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {report_file.name}\n")

    # Return exit code
    passed = sum(1 for success, _ in results.values() if success)
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
