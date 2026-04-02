#!/usr/bin/env python3
"""
Full-resolution p-adic embedding with density visualization to reveal Sierpinski structure.

Creates visualizations that show the hierarchical structure through:
1. Heatmap of point density in embedding space
2. Hexbin plot showing clustered regions
3. Log-density to reveal sparse structure
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LogNorm
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def create_density_visualizations():
    """Create density-based p-adic embedding visualizations."""

    # Load DEM
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape
    dem_flat = dem_data.flatten()

    # Normalize elevation to [0, 1] for p-adic encoding
    dem_normalized = (dem_flat - dem_flat.min()) / (dem_flat.max() - dem_flat.min())

    # Convert to p-adic integers
    p, l = 3, 6
    padic_ints = np.round(dem_normalized * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)

    print(f"Creating density visualizations for {len(padic_ints):,} pixels...")

    # Get embeddings
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)

    norm = Normalize(vmin=dem_flat.min(), vmax=dem_flat.max())
    cmap = plt.get_cmap('terrain')

    # Figure 1: Density heatmap
    print("Creating density heatmap...")
    fig, ax = plt.subplots(figsize=(14, 12))

    h_2d, xedges, yedges = np.histogram2d(
        embeddings[:, 0],
        embeddings[:, 1],
        bins=256
    )

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    im = ax.imshow(h_2d.T, extent=extent, origin='lower', cmap='hot', aspect='auto')
    ax.set_xlabel('Real Part', fontsize=12)
    ax.set_ylabel('Imaginary Part', fontsize=12)
    ax.set_title('P-Adic Embedding Density (Sierpinski Structure Revealed)', fontweight='bold', fontsize=14)
    cbar = plt.colorbar(im, ax=ax, label='Point Count')

    plt.tight_layout()
    output_file = results_dir / '07_padic_density_heatmap.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Figure 2: Log-density to reveal sparse structure
    print("Creating log-density plot...")
    fig, ax = plt.subplots(figsize=(14, 12))

    h_2d_log = np.log1p(h_2d)
    im = ax.imshow(h_2d_log.T, extent=extent, origin='lower', cmap='viridis', aspect='auto')
    ax.set_xlabel('Real Part', fontsize=12)
    ax.set_ylabel('Imaginary Part', fontsize=12)
    ax.set_title('P-Adic Embedding Log-Density (Hierarchical Organization)', fontweight='bold', fontsize=14)
    cbar = plt.colorbar(im, ax=ax, label='Log(Point Count + 1)')

    plt.tight_layout()
    output_file = results_dir / '07_padic_logdensity.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Figure 3: Hexbin plot showing clustering
    print("Creating hexbin plot...")
    fig, ax = plt.subplots(figsize=(14, 12))

    hb = ax.hexbin(
        embeddings[:, 0],
        embeddings[:, 1],
        gridsize=80,
        cmap='YlOrRd',
        mincnt=1,
        edgecolors='none'
    )
    ax.set_xlabel('Real Part', fontsize=12)
    ax.set_ylabel('Imaginary Part', fontsize=12)
    ax.set_title('P-Adic Embedding Hexbin (Sierpinski Fractal Clustering)', fontweight='bold', fontsize=14)
    cbar = plt.colorbar(hb, ax=ax, label='Points per Hexagon')

    plt.tight_layout()
    output_file = results_dir / '07_padic_hexbin.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Figure 4: Multi-view comparison
    print("Creating multi-view figure...")
    fig, axes = plt.subplots(2, 2, figsize=(18, 16))

    # DEM
    dem_norm = Normalize(vmin=dem_data.min(), vmax=dem_data.max())
    im0 = axes[0, 0].imshow(dem_data, cmap='terrain', norm=dem_norm, aspect='auto')
    axes[0, 0].set_title('CTX DEM', fontweight='bold', fontsize=13)
    plt.colorbar(im0, ax=axes[0, 0], label='Elevation (m)')

    # Density
    im1 = axes[0, 1].imshow(h_2d.T, extent=extent, origin='lower', cmap='hot', aspect='auto')
    axes[0, 1].set_title('P-Adic Density (Hot)', fontweight='bold', fontsize=13)
    axes[0, 1].set_xlabel('Real')
    axes[0, 1].set_ylabel('Imag')
    plt.colorbar(im1, ax=axes[0, 1], label='Count')

    # Log-density
    h_2d_log = np.log1p(h_2d)
    im2 = axes[1, 0].imshow(h_2d_log.T, extent=extent, origin='lower', cmap='viridis', aspect='auto')
    axes[1, 0].set_title('P-Adic Log-Density (Viridis)', fontweight='bold', fontsize=13)
    axes[1, 0].set_xlabel('Real')
    axes[1, 0].set_ylabel('Imag')
    plt.colorbar(im2, ax=axes[1, 0], label='Log(Count+1)')

    # Ultra-transparent scatter to show structure
    axes[1, 1].scatter(
        embeddings[:, 0],
        embeddings[:, 1],
        c=dem_flat,
        cmap='terrain',
        norm=dem_norm,
        s=0.1,
        alpha=0.05,
        edgecolors='none'
    )
    axes[1, 1].set_title('P-Adic Points (Ultra-Transparent)', fontweight='bold', fontsize=13)
    axes[1, 1].set_xlabel('Real')
    axes[1, 1].set_ylabel('Imag')
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle(f'Full-Resolution P-Adic Analysis (p={p}, l={l}, {len(padic_ints):,} pixels)',
                fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = results_dir / '07_padic_multiview.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    print(f"\n✓ All density visualizations complete!")
    print(f"\nKey insight: The Sierpinski carpet structure is revealed through point density clustering.")
    print(f"High-density regions (red in heatmap) show the hierarchical organization of terrain elevations.")

if __name__ == '__main__':
    create_density_visualizations()
