#!/usr/bin/env python3
"""
Full-resolution p-adic embedding visualization.

Creates a 2-panel figure showing:
- Left: DEM at native resolution colored by elevation
- Right: P-adic embeddings of all pixels, colored by elevation
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def create_full_resolution_visualization():
    """Create full-resolution DEM + p-adic embedding visualization."""

    # Load DEM
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    print(f"DEM shape: {dem_data.shape}")
    print(f"Elevation range: {dem_data.min():.2f} to {dem_data.max():.2f} m")

    h, w = dem_data.shape

    # Create elevation colormap normalization
    norm = Normalize(vmin=dem_data.min(), vmax=dem_data.max())
    cmap = plt.get_cmap('terrain')

    # Flatten DEM for embedding
    dem_flat = dem_data.flatten()

    # Normalize elevation to [0, 1] for p-adic encoding
    dem_normalized = (dem_flat - dem_flat.min()) / (dem_flat.max() - dem_flat.min())

    # Convert to p-adic integers
    p, l = 3, 6
    padic_ints = np.round(dem_normalized * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)

    print(f"\nEmbedding {len(padic_ints):,} pixels into p-adic space...")
    print(f"P-adic parameters: p={p}, l={l}")

    # Get embeddings
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)

    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Embedding range: real [{embeddings[:, 0].min():.4f}, {embeddings[:, 0].max():.4f}], "
          f"imag [{embeddings[:, 1].min():.4f}, {embeddings[:, 1].max():.4f}]")

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    # Left panel: DEM with elevation colormap
    im_left = axes[0].imshow(dem_data, cmap='terrain', norm=norm, aspect='auto')
    axes[0].set_title('CTX DEM (Native Resolution)', fontweight='bold', fontsize=14)
    axes[0].set_xlabel('Pixel X')
    axes[0].set_ylabel('Pixel Y')
    cbar_left = plt.colorbar(im_left, ax=axes[0], label='Elevation (m)')

    # Right panel: P-adic embeddings colored by elevation
    # Get colors from elevation values
    colors = cmap(norm(dem_flat))

    scatter = axes[1].scatter(
        embeddings[:, 0],
        embeddings[:, 1],
        c=dem_flat,
        cmap='terrain',
        norm=norm,
        s=3,  # Larger points for better visibility
        alpha=0.8,
        edgecolors='none'
    )
    axes[1].set_title('P-Adic Embeddings (All Pixels)', fontweight='bold', fontsize=14)
    axes[1].set_xlabel('Real Part')
    axes[1].set_ylabel('Imaginary Part')
    axes[1].grid(True, alpha=0.3)
    cbar_right = plt.colorbar(scatter, ax=axes[1], label='Elevation (m)')

    plt.suptitle(f'Full-Resolution DEM & P-Adic Embedding (p={p}, l={l}, s={s:.4f})',
                fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Save
    output_file = results_dir / '06_full_resolution_padic_embedding.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()

    # Also create a zoomed version of the embedding space to see structure better
    fig, ax = plt.subplots(figsize=(14, 12))

    scatter = ax.scatter(
        embeddings[:, 0],
        embeddings[:, 1],
        c=dem_flat,
        cmap='terrain',
        norm=norm,
        s=5,  # Larger for better visibility
        alpha=0.6,
        edgecolors='none'
    )
    ax.set_title('P-Adic Embedding Detail (All Pixels)', fontweight='bold', fontsize=14)
    ax.set_xlabel('Real Part', fontsize=12)
    ax.set_ylabel('Imaginary Part', fontsize=12)
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax, label='Elevation (m)')

    plt.tight_layout()
    output_file = results_dir / '06_full_resolution_padic_detail.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    print(f"\n✓ Visualizations complete!")

if __name__ == '__main__':
    create_full_resolution_visualization()
