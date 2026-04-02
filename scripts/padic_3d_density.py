#!/usr/bin/env python3
"""
3D visualization of p-adic embedding density.

Shows the distribution of terrain elevations across the Sierpinski structure
with height representing how many pixels stack at each location.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def create_3d_density_visualization():
    """Create 3D density plot of p-adic embeddings."""

    # Load DEM
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    dem_flat = dem_data.flatten()

    print(f"Creating 3D density visualization...")
    print(f"Processing {len(dem_flat):,} pixels...")

    # Normalize elevation to [0, 1] for p-adic encoding
    dem_normalized = (dem_flat - dem_flat.min()) / (dem_flat.max() - dem_flat.min())

    # Convert to p-adic integers
    p, l = 3, 6
    padic_ints = np.round(dem_normalized * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)

    # Get embeddings
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)

    print(f"Embeddings computed. Creating density histogram...")

    # Create 2D histogram
    bins = 150  # Resolution of the 3D surface
    h_2d, xedges, yedges = np.histogram2d(
        embeddings[:, 0],
        embeddings[:, 1],
        bins=bins
    )

    # Create mesh grid
    X, Y = np.meshgrid(
        (xedges[:-1] + xedges[1:]) / 2,
        (yedges[:-1] + yedges[1:]) / 2,
        indexing='ij'
    )
    Z = h_2d.T

    # Get elevation colormap
    norm = Normalize(vmin=dem_flat.min(), vmax=dem_flat.max())
    cmap = plt.get_cmap('terrain')

    # Compute average elevation at each bin for coloring
    elevation_by_bin = np.zeros_like(Z, dtype=float)
    for i in range(len(xedges)-1):
        for j in range(len(yedges)-1):
            mask = (embeddings[:, 0] >= xedges[i]) & (embeddings[:, 0] < xedges[i+1]) & \
                   (embeddings[:, 1] >= yedges[j]) & (embeddings[:, 1] < yedges[j+1])
            if mask.sum() > 0:
                elevation_by_bin[j, i] = dem_flat[mask].mean()
            else:
                elevation_by_bin[j, i] = np.nan

    # Figure 1: 3D surface with elevation coloring
    print("Creating 3D surface plot...")
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    # Create surface
    colors_array = cmap(norm(elevation_by_bin))
    surf = ax.plot_surface(X, Y, Z, facecolors=colors_array, shade=False, rstride=1, cstride=1)

    ax.set_xlabel('Real Part', fontsize=12, labelpad=10)
    ax.set_ylabel('Imaginary Part', fontsize=12, labelpad=10)
    ax.set_zlabel('Point Count', fontsize=12, labelpad=10)
    ax.set_title('3D P-Adic Embedding Density (Sierpinski Structure)\nHeight = Number of Pixels, Color = Average Elevation',
                fontweight='bold', fontsize=14, pad=20)

    # Add colorbar manually
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.1, shrink=0.8, label='Elevation (m)')

    # Adjust viewing angle
    ax.view_init(elev=25, azim=45)

    plt.tight_layout()
    output_file = results_dir / '08_padic_3d_density_surface.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Figure 2: Alternative angle
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    colors_array = cmap(norm(elevation_by_bin))
    surf = ax.plot_surface(X, Y, Z, facecolors=colors_array, shade=False, rstride=1, cstride=1)

    ax.set_xlabel('Real Part', fontsize=12, labelpad=10)
    ax.set_ylabel('Imaginary Part', fontsize=12, labelpad=10)
    ax.set_zlabel('Point Count', fontsize=12, labelpad=10)
    ax.set_title('3D P-Adic Embedding Density (Sierpinski Structure)\nHeight = Number of Pixels, Color = Average Elevation',
                fontweight='bold', fontsize=14, pad=20)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.1, shrink=0.8, label='Elevation (m)')

    # Different viewing angle
    ax.view_init(elev=15, azim=120)

    plt.tight_layout()
    output_file = results_dir / '08_padic_3d_density_surface_alt.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Figure 3: Top-down view (like a heatmap but with contours)
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    colors_array = cmap(norm(elevation_by_bin))
    surf = ax.plot_surface(X, Y, Z, facecolors=colors_array, shade=False, rstride=1, cstride=1)

    ax.set_xlabel('Real Part', fontsize=12, labelpad=10)
    ax.set_ylabel('Imaginary Part', fontsize=12, labelpad=10)
    ax.set_zlabel('Point Count', fontsize=12, labelpad=10)
    ax.set_title('3D P-Adic Embedding Density (Sierpinski Structure)\nHeight = Number of Pixels, Color = Average Elevation',
                fontweight='bold', fontsize=14, pad=20)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.1, shrink=0.8, label='Elevation (m)')

    # Top-down view
    ax.view_init(elev=90, azim=0)

    plt.tight_layout()
    output_file = results_dir / '08_padic_3d_density_topdown.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    # Print statistics
    print(f"\n3D Density Statistics:")
    print(f"  Max points in any bin: {Z.max():.0f}")
    print(f"  Mean points per bin: {Z.mean():.1f}")
    print(f"  Non-empty bins: {(Z > 0).sum()} / {Z.size}")
    print(f"  Elevation range: {dem_flat.min():.1f} to {dem_flat.max():.1f} m")

    print(f"\n✓ All 3D visualizations complete!")

if __name__ == '__main__':
    create_3d_density_visualization()
