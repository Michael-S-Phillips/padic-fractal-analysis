#!/usr/bin/env python3
"""
Visualize per-pixel fractal complexity maps.

Creates publication-quality maps showing terrain complexity, clustering,
and hierarchical organization at full DEM resolution.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, Normalize
from pathlib import Path


def visualize_perpixel_maps(cache_dir, results_dir, dem_path):
    """Create comprehensive per-pixel map visualizations."""

    print("🎨 Visualizing per-pixel fractal maps\n")

    # Load DEM for reference
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    dem_normalized = np.load(str(cache_dir / 'dem_normalized.npy'))

    # Create hillshade
    ls = LightSource(azdeg=315, altdeg=45)
    hillshade = ls.hillshade(dem_data, vert_exag=0.1)

    # Load per-pixel maps
    window_sizes = [3, 5, 7]

    for window_size in window_sizes:
        print(f"📍 Creating visualizations for window size {window_size}×{window_size}")

        complexity_map = np.load(str(cache_dir / f'perpixel/perpixel_complexity_w{window_size}.npy'))
        clustering_map = np.load(str(cache_dir / f'perpixel/perpixel_clustering_w{window_size}.npy'))
        distance_map = np.load(str(cache_dir / f'perpixel/perpixel_distance_w{window_size}.npy'))

        # Create multi-panel figure
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # Row 1: DEM reference, Complexity, Clustering
        # DEM
        axes[0, 0].imshow(hillshade, cmap='gray')
        axes[0, 0].set_title('DEM Hillshade', fontweight='bold', fontsize=12)
        axes[0, 0].set_xlabel('Pixel X')
        axes[0, 0].set_ylabel('Pixel Y')

        # Complexity
        im1 = axes[0, 1].imshow(complexity_map, cmap='hot', interpolation='bilinear')
        axes[0, 1].set_title('Per-Pixel Complexity\n(Shannon Entropy)', fontweight='bold', fontsize=12)
        axes[0, 1].set_xlabel('Pixel X')
        axes[0, 1].set_ylabel('Pixel Y')
        cbar1 = plt.colorbar(im1, ax=axes[0, 1])
        cbar1.set_label('Entropy (bits)')

        # Clustering
        im2 = axes[0, 2].imshow(clustering_map, cmap='viridis', interpolation='bilinear')
        axes[0, 2].set_title('Per-Pixel Clustering\n(Density CV)', fontweight='bold', fontsize=12)
        axes[0, 2].set_xlabel('Pixel X')
        axes[0, 2].set_ylabel('Pixel Y')
        cbar2 = plt.colorbar(im2, ax=axes[0, 2])
        cbar2.set_label('Clustering Tendency')

        # Row 2: Distance, Combined map, Statistics
        # Distance
        im3 = axes[1, 0].imshow(distance_map, cmap='plasma', interpolation='bilinear')
        axes[1, 0].set_title('Per-Pixel Mean Distance\n(Embedding Space)', fontweight='bold', fontsize=12)
        axes[1, 0].set_xlabel('Pixel X')
        axes[1, 0].set_ylabel('Pixel Y')
        cbar3 = plt.colorbar(im3, ax=axes[1, 0])
        cbar3.set_label('Mean Distance')

        # Combined: Complexity colored by clustering
        im4 = axes[1, 1].scatter(
            np.arange(complexity_map.size) % dem_data.shape[1],
            np.arange(complexity_map.size) // dem_data.shape[1],
            c=complexity_map.flatten(),
            s=0.1,
            cmap='hot',
            alpha=0.8
        )
        axes[1, 1].set_title('Complexity Density Map', fontweight='bold', fontsize=12)
        axes[1, 1].set_xlabel('Pixel X')
        axes[1, 1].set_ylabel('Pixel Y')
        axes[1, 1].set_xlim(0, dem_data.shape[1])
        axes[1, 1].set_ylim(dem_data.shape[0], 0)

        # Statistics
        axes[1, 2].axis('off')
        stats_text = f"""
PER-PIXEL FRACTAL STATISTICS
Window Size: {window_size}×{window_size}

Complexity (Entropy):
  Min: {complexity_map.min():.4f}
  Max: {complexity_map.max():.4f}
  Mean: {complexity_map.mean():.4f}
  Std: {complexity_map.std():.4f}

Clustering (Density CV):
  Min: {clustering_map.min():.4f}
  Max: {clustering_map.max():.4f}
  Mean: {clustering_map.mean():.4f}
  Std: {clustering_map.std():.4f}

Mean Distance (Embedding):
  Min: {distance_map.min():.4f}
  Max: {distance_map.max():.4f}
  Mean: {distance_map.mean():.4f}
  Std: {distance_map.std():.4f}

Correlation (Complexity vs Clustering):
  r = {np.corrcoef(complexity_map.flatten(), clustering_map.flatten())[0,1]:.4f}
        """
        axes[1, 2].text(0.05, 0.95, stats_text, transform=axes[1, 2].transAxes,
                       fontsize=10, verticalalignment='top', family='monospace',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.suptitle(f'Per-Pixel P-Adic Fractal Complexity Maps (Window: {window_size}×{window_size})',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_file = results_dir / f'04_perpixel_fractal_w{window_size}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  ✓ Saved: {output_file.name}")
        plt.close()

    # Create comparison figure across window sizes
    print(f"\n📊 Creating multi-scale comparison")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    for idx, window_size in enumerate(window_sizes):
        complexity_map = np.load(str(cache_dir / f'perpixel/perpixel_complexity_w{window_size}.npy'))
        clustering_map = np.load(str(cache_dir / f'perpixel/perpixel_clustering_w{window_size}.npy'))

        # Top row: Complexity
        im1 = axes[0, idx].imshow(complexity_map, cmap='hot', interpolation='bilinear')
        axes[0, idx].set_title(f'Complexity\n(Window {window_size}×{window_size})', fontweight='bold')
        plt.colorbar(im1, ax=axes[0, idx], label='Entropy')

        # Bottom row: Clustering
        im2 = axes[1, idx].imshow(clustering_map, cmap='viridis', interpolation='bilinear')
        axes[1, idx].set_title(f'Clustering\n(Window {window_size}×{window_size})', fontweight='bold')
        plt.colorbar(im2, ax=axes[1, idx], label='Density CV')

    plt.suptitle('Per-Pixel Metrics: Multi-Scale Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_file = results_dir / '05_perpixel_multiscale_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file.name}")
    plt.close()

    print("\n✓ Visualizations complete!")


if __name__ == '__main__':
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    dem_path = '/Volumes/Fangorn/padic_fractal_analysis/data/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif'

    # Wait for computation to complete
    import time
    perpixel_dir = cache_dir / 'perpixel'
    max_wait = 3600  # 1 hour timeout

    print("⏳ Waiting for per-pixel maps to be generated...")
    start_time = time.time()

    while True:
        # Check if all files exist
        required_files = [
            f'perpixel_complexity_w{w}.npy' for w in [3, 5, 7]
        ] + [
            f'perpixel_clustering_w{w}.npy' for w in [3, 5, 7]
        ] + [
            f'perpixel_distance_w{w}.npy' for w in [3, 5, 7]
        ]

        all_exist = all((perpixel_dir / f).exists() for f in required_files)

        if all_exist:
            print("✓ All maps generated!\n")
            visualize_perpixel_maps(cache_dir, results_dir, dem_path)
            break

        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"⚠️ Timeout after {max_wait}s. Partial maps may be available.")
            break

        print(f"  Waiting... ({elapsed:.0f}s)", end='\r')
        time.sleep(5)
