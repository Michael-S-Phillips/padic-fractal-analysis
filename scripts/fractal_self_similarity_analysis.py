#!/usr/bin/env python3
"""
Fractal self-similarity analysis of terrain elevation distributions.

Tests whether elevation distributions in individual Sierpinski regions
match the overall distribution, indicating fractal properties.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import entropy, ks_2samp, entropy as scipy_entropy
from pathlib import Path
import sys
import json

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def compute_elevation_distribution_metrics(elevations):
    """Compute statistical metrics for elevation distribution."""
    return {
        'mean': float(np.mean(elevations)),
        'std': float(np.std(elevations)),
        'min': float(np.min(elevations)),
        'max': float(np.max(elevations)),
        'median': float(np.median(elevations)),
        'entropy': float(scipy_entropy(np.histogram(elevations, bins=50)[0] + 1e-10))
    }

def analyze_self_similarity():
    """Analyze fractal self-similarity of terrain."""

    # Load DEM
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    dem_flat = dem_data.flatten()

    print("=" * 70)
    print("FRACTAL SELF-SIMILARITY ANALYSIS")
    print("=" * 70)
    print(f"\nAnalyzing {len(dem_flat):,} terrain pixels...")

    # Normalize elevation to [0, 1] for p-adic encoding
    dem_normalized = (dem_flat - dem_flat.min()) / (dem_flat.max() - dem_flat.min())

    # Get overall baseline distribution
    baseline_metrics = compute_elevation_distribution_metrics(dem_flat)
    print(f"\nBaseline (Full DEM):")
    print(f"  Mean elevation: {baseline_metrics['mean']:.2f} m")
    print(f"  Std deviation: {baseline_metrics['std']:.2f} m")
    print(f"  Range: {baseline_metrics['min']:.2f} to {baseline_metrics['max']:.2f} m")
    print(f"  Entropy: {baseline_metrics['entropy']:.4f}")

    # Compute embeddings at different levels
    levels_to_analyze = [4, 5, 6]
    all_results = {}

    for level in levels_to_analyze:
        print(f"\n{'=' * 70}")
        print(f"LEVEL {level} (3^{level} = {3**level} regions)")
        print(f"{'=' * 70}")

        # Convert to p-adic integers
        p = 3
        padic_ints = np.round(dem_normalized * (p**level - 1)).astype(int)
        padic_ints = np.clip(padic_ints, 0, p**level - 1)

        # Get embeddings
        s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
        embeddings = embed_padic_cloud(padic_ints, p=p, l=level, s=s, m=0)

        # Analyze each region
        num_regions = 3**level
        region_metrics = {}
        distribution_distances = []

        print(f"\nAnalyzing {num_regions} regions...")

        for region_id in range(num_regions):
            mask = padic_ints == region_id
            if mask.sum() == 0:
                continue

            region_elevations = dem_flat[mask]
            metrics = compute_elevation_distribution_metrics(region_elevations)
            region_metrics[region_id] = {
                'count': int(mask.sum()),
                'metrics': metrics
            }

            # Compare to baseline using KS test
            ks_stat, p_value = ks_2samp(region_elevations, dem_flat)
            distribution_distances.append(ks_stat)

        # Statistics across all regions
        num_nonempty = len(region_metrics)
        pixel_counts = [m['count'] for m in region_metrics.values()]
        entropies = [m['metrics']['entropy'] for m in region_metrics.values()]
        means = [m['metrics']['mean'] for m in region_metrics.values()]
        stds = [m['metrics']['std'] for m in region_metrics.values()]

        print(f"\nRegion Population Statistics:")
        print(f"  Non-empty regions: {num_nonempty} / {num_regions}")
        print(f"  Pixels per region: mean={np.mean(pixel_counts):.0f}, std={np.std(pixel_counts):.0f}")
        print(f"  Min: {np.min(pixel_counts)}, Max: {np.max(pixel_counts)}")

        print(f"\nDistribution Comparison (vs Baseline):")
        print(f"  Mean KS distance: {np.mean(distribution_distances):.4f}")
        print(f"  Std KS distance: {np.std(distribution_distances):.4f}")
        print(f"  (KS distance near 0 = distributions very similar)")

        print(f"\nElevation Statistics Across Regions:")
        print(f"  Mean of means: {np.mean(means):.2f} m (baseline: {baseline_metrics['mean']:.2f})")
        print(f"  Mean of stds: {np.mean(stds):.2f} m (baseline: {baseline_metrics['std']:.2f})")
        print(f"  Entropy: mean={np.mean(entropies):.4f}, std={np.std(entropies):.4f}")
        print(f"           (baseline: {baseline_metrics['entropy']:.4f})")

        # Estimate fractal dimension via scaling
        avg_region_size = np.mean(pixel_counts)
        scaling_factor = len(dem_flat) / avg_region_size
        print(f"\nFractal Dimension Estimate (from level {level}):")
        print(f"  Region scaling: {scaling_factor:.2f}x")
        print(f"  Expected for 2D fractal: ~{3**(level-1)}x = {3**(level-1)}")

        all_results[level] = {
            'level': level,
            'num_regions': num_regions,
            'num_nonempty': num_nonempty,
            'avg_pixels_per_region': float(np.mean(pixel_counts)),
            'mean_ks_distance': float(np.mean(distribution_distances)),
            'std_ks_distance': float(np.std(distribution_distances)),
            'mean_entropy': float(np.mean(entropies)),
            'std_entropy': float(np.std(entropies))
        }

    # Cross-level comparison
    print(f"\n{'=' * 70}")
    print("CROSS-LEVEL FRACTAL ANALYSIS")
    print(f"{'=' * 70}")

    ks_distances = [all_results[l]['mean_ks_distance'] for l in levels_to_analyze]
    entropies_by_level = [all_results[l]['mean_entropy'] for l in levels_to_analyze]

    print(f"\nKS Distance Scaling:")
    for i, level in enumerate(levels_to_analyze):
        print(f"  Level {level}: {ks_distances[i]:.4f}")

    print(f"\nEntropy Scaling:")
    for i, level in enumerate(levels_to_analyze):
        print(f"  Level {level}: {entropies_by_level[i]:.4f}")

    # Interpretation
    print(f"\n{'=' * 70}")
    print("INTERPRETATION")
    print(f"{'=' * 70}")

    if np.mean(ks_distances) < 0.1:
        print("\n✓ STRONG evidence of self-similarity!")
        print("  Sierpinski regions have similar elevation distributions")
        print("  Terrain exhibits fractal properties")
    elif np.mean(ks_distances) < 0.2:
        print("\n◐ MODERATE evidence of self-similarity")
        print("  Some scale-dependent structure detected")
    else:
        print("\n✗ WEAK evidence of self-similarity")
        print("  Distributions vary significantly across scales")

    # Save results
    results_file = cache_dir / 'fractal_self_similarity_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'baseline': baseline_metrics,
            'by_level': all_results
        }, f, indent=2)
    print(f"\n✓ Results saved to {results_file.name}")

    # Create visualizations
    create_comparison_plots(dem_flat, baseline_metrics, all_results, results_dir)

def create_comparison_plots(dem_flat, baseline_metrics, all_results, results_dir):
    """Create visualization comparing distributions across levels."""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: KS Distance by level
    levels = [all_results[l]['level'] for l in sorted(all_results.keys())]
    ks_distances = [all_results[l]['mean_ks_distance'] for l in levels]
    ks_stds = [all_results[l]['std_ks_distance'] for l in levels]

    axes[0, 0].errorbar(levels, ks_distances, yerr=ks_stds, marker='o', linewidth=2, markersize=10, capsize=5)
    axes[0, 0].axhline(y=0.05, color='g', linestyle='--', label='Strong similarity (KS < 0.05)')
    axes[0, 0].axhline(y=0.1, color='orange', linestyle='--', label='Moderate similarity (KS < 0.1)')
    axes[0, 0].set_xlabel('Sierpinski Level', fontsize=12)
    axes[0, 0].set_ylabel('Mean KS Distance', fontsize=12)
    axes[0, 0].set_title('Distribution Similarity Across Levels\n(Lower = More Self-Similar)', fontweight='bold', fontsize=13)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: Entropy by level
    entropies = [all_results[l]['mean_entropy'] for l in levels]
    entropy_stds = [all_results[l]['std_entropy'] for l in levels]

    axes[0, 1].errorbar(levels, entropies, yerr=entropy_stds, marker='s', linewidth=2, markersize=10, capsize=5, color='purple')
    axes[0, 1].axhline(y=baseline_metrics['entropy'], color='r', linestyle='--', label=f"Baseline entropy ({baseline_metrics['entropy']:.4f})")
    axes[0, 1].set_xlabel('Sierpinski Level', fontsize=12)
    axes[0, 1].set_ylabel('Mean Entropy', fontsize=12)
    axes[0, 1].set_title('Distribution Entropy Across Levels\n(Constant = Self-Similar)', fontweight='bold', fontsize=13)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Plot 3: Histogram comparison
    axes[1, 0].hist(dem_flat, bins=100, alpha=0.7, label='Full DEM', density=True, color='black', linewidth=2)
    axes[1, 0].set_xlabel('Elevation (m)', fontsize=12)
    axes[1, 0].set_ylabel('Probability Density', fontsize=12)
    axes[1, 0].set_title('Baseline Elevation Distribution\n(All pixels)', fontweight='bold', fontsize=13)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Plot 4: Summary statistics
    axes[1, 1].axis('off')
    summary_text = f"""
FRACTAL SELF-SIMILARITY SUMMARY

Baseline Statistics:
  Mean: {baseline_metrics['mean']:.2f} m
  Std Dev: {baseline_metrics['std']:.2f} m
  Entropy: {baseline_metrics['entropy']:.4f}
  Range: {baseline_metrics['min']:.2f} - {baseline_metrics['max']:.2f} m

Cross-Scale Analysis:
  Levels analyzed: {min(levels)} to {max(levels)}
  Mean KS distance: {np.mean([all_results[l]['mean_ks_distance'] for l in levels]):.4f}

Interpretation:
  • KS distance measures distribution divergence
  • Lower values = stronger self-similarity
  • Constant entropy = scale independence

Fractal Hypothesis:
  If KS distance ≈ constant across levels → Fractal properties present
  If entropy ≈ constant across levels → Scale-independent structure
"""
    axes[1, 1].text(0.05, 0.95, summary_text, transform=axes[1, 1].transAxes,
                   fontsize=11, verticalalignment='top', family='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.suptitle('Fractal Self-Similarity Analysis: Terrain Elevation Distributions',
                fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = results_dir / '09_fractal_self_similarity_analysis.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    analyze_self_similarity()
