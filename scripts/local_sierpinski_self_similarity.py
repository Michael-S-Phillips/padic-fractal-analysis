#!/usr/bin/env python3
"""
Local Sierpinski Self-Similarity Analysis

For each pixel, compute a 27x27 window Sierpinski distribution and
compare it to the global Sierpinski distribution. Pixels with high
similarity exhibit fractal properties ("most fractal" regions).
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import wasserstein_distance
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def compute_sierpinski_distribution(elevations, p=3, l=6, bins=729):
    """
    Compute the distribution of elevations in p-adic Sierpinski space.

    Returns a histogram showing how elevations cluster across the
    Sierpinski structure (one bin per possible p-adic region).
    """
    if len(elevations) == 0:
        return np.zeros(bins)

    # Normalize to [0, 1]
    e_min, e_max = elevations.min(), elevations.max()
    if e_max == e_min:
        e_norm = np.zeros_like(elevations)
    else:
        e_norm = (elevations - e_min) / (e_max - e_min)

    # Convert to p-adic integers
    padic_ints = np.round(e_norm * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)

    # Create histogram
    hist, _ = np.histogram(padic_ints, bins=np.arange(bins + 1))
    return hist.astype(float)

def analyze_local_fractality():
    """Analyze local fractal properties using sliding 27x27 windows."""

    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape

    print("=" * 70)
    print("LOCAL SIERPINSKI SELF-SIMILARITY ANALYSIS")
    print("=" * 70)
    print(f"\nDEM shape: {dem_data.shape}")
    print(f"Window size: 27×27")
    print(f"Total pixels to analyze: {h * w:,}")

    # Compute global Sierpinski distribution (baseline for comparison)
    print(f"\nComputing global Sierpinski distribution...")
    global_dist = compute_sierpinski_distribution(dem_data.flatten(), p=3, l=6)
    global_dist_norm = global_dist / global_dist.sum()  # Normalize

    print(f"  Global distribution computed")
    print(f"  Non-zero bins: {(global_dist > 0).sum()} / 729")

    # Create output map
    similarity_map = np.zeros((h, w), dtype=np.float32)
    window_size = 27
    half_window = window_size // 2

    print(f"\nProcessing {h:,} rows × {w:,} cols = {h*w:,} pixels...")

    # Process each pixel
    for y in range(h):
        if y % 100 == 0:
            print(f"  Row {y}/{h}...")

        for x in range(w):
            # Extract 27×27 window centered at (x, y)
            y1 = max(0, y - half_window)
            y2 = min(h, y + half_window + 1)
            x1 = max(0, x - half_window)
            x2 = min(w, x + half_window + 1)

            window = dem_data[y1:y2, x1:x2].flatten()

            if len(window) < 9:  # Too close to edge
                similarity_map[y, x] = 0
                continue

            # Compute local Sierpinski distribution
            local_dist = compute_sierpinski_distribution(window, p=3, l=6)
            local_dist_norm = local_dist / (local_dist.sum() + 1e-10)

            # Compare to global using Wasserstein distance
            # (lower distance = more similar = more fractal)
            w_dist = wasserstein_distance(
                np.arange(729),
                np.arange(729),
                global_dist_norm,
                local_dist_norm
            )

            # Normalize distance to 0-1 range
            # Use 1/(1+distance) which is more stable than exponential
            similarity = 1.0 / (1.0 + w_dist)
            similarity_map[y, x] = similarity

    print(f"\n✓ Local fractality analysis complete!")

    # Statistics
    valid_pixels = similarity_map > 0
    print(f"\nSimilarity Map Statistics:")
    print(f"  Min: {similarity_map[valid_pixels].min():.4f}")
    print(f"  Max: {similarity_map[valid_pixels].max():.4f}")
    print(f"  Mean: {similarity_map[valid_pixels].mean():.4f}")
    print(f"  Std: {similarity_map[valid_pixels].std():.4f}")
    print(f"  Median: {np.median(similarity_map[valid_pixels]):.4f}")

    # Save raw data
    np.save(str(cache_dir / 'local_sierpinski_similarity.npy'), similarity_map)
    print(f"\n✓ Saved: local_sierpinski_similarity.npy")

    # Create visualization
    create_visualization(similarity_map, dem_data, results_dir)

def create_visualization(similarity_map, dem_data, results_dir):
    """Create visualization of local fractality."""

    print("\nCreating visualizations...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Plot 1: Similarity map
    im1 = axes[0, 0].imshow(similarity_map, cmap='hot', aspect='auto')
    axes[0, 0].set_title('Local Sierpinski Self-Similarity\n(Bright = Most Fractal)',
                         fontweight='bold', fontsize=13)
    axes[0, 0].set_xlabel('Pixel X')
    axes[0, 0].set_ylabel('Pixel Y')
    cbar1 = plt.colorbar(im1, ax=axes[0, 0])
    cbar1.set_label('Similarity Score (0-1)')

    # Plot 2: DEM for reference
    im2 = axes[0, 1].imshow(dem_data, cmap='terrain', aspect='auto')
    axes[0, 1].set_title('DEM (Reference)', fontweight='bold', fontsize=13)
    axes[0, 1].set_xlabel('Pixel X')
    axes[0, 1].set_ylabel('Pixel Y')
    cbar2 = plt.colorbar(im2, ax=axes[0, 1])
    cbar2.set_label('Elevation (m)')

    # Plot 3: Overlay - high fractality regions
    high_fractality = similarity_map > np.percentile(similarity_map[similarity_map > 0], 90)
    overlay = np.zeros((*dem_data.shape, 3), dtype=float)
    overlay[:, :, 0] = dem_data / dem_data.max()  # Red channel = elevation
    overlay[high_fractality, 1] = 1  # Green highlights fractal regions

    axes[1, 0].imshow(overlay, aspect='auto')
    axes[1, 0].set_title('High Fractality Regions (Top 10%)\nGreen overlay on elevation',
                         fontweight='bold', fontsize=13)
    axes[1, 0].set_xlabel('Pixel X')
    axes[1, 0].set_ylabel('Pixel Y')

    # Plot 4: Histogram and statistics
    valid_sim = similarity_map[similarity_map > 0]
    axes[1, 1].hist(valid_sim, bins=100, color='darkblue', alpha=0.7, edgecolor='black')
    axes[1, 1].axvline(valid_sim.mean(), color='red', linestyle='--', linewidth=2,
                       label=f"Mean: {valid_sim.mean():.4f}")
    axes[1, 1].axvline(np.percentile(valid_sim, 90), color='green', linestyle='--',
                       linewidth=2, label=f"90th %ile: {np.percentile(valid_sim, 90):.4f}")
    axes[1, 1].set_xlabel('Similarity Score', fontsize=12)
    axes[1, 1].set_ylabel('Pixel Count', fontsize=12)
    axes[1, 1].set_title('Distribution of Local Fractality Scores', fontweight='bold', fontsize=13)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle('Local Sierpinski Self-Similarity: Per-Pixel Fractality Analysis\n(27×27 Window Comparison)',
                fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = results_dir / '10_local_sierpinski_self_similarity.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    analyze_local_fractality()
