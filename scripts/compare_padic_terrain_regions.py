#!/usr/bin/env python3
"""
Compare P-Adic Embeddings of Different Terrain Regions

This script loads different terrain regions from the CTX DEM and visualizes
their p-adic embeddings side-by-side, revealing how terrain complexity
maps to p-adic hierarchical structure.

Regions selected for varied complexity:
  - Flat region: Low elevation variance
  - Crater region: High-complexity circular feature
  - Ridge region: Linear elevation changes
  - Valley region: Smooth depression
  - Mixed region: Varied terrain with multiple features
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from scipy.ndimage import zoom

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from padic.padic_embedding import embed_padic_cloud, get_default_s, compute_s_0


def load_dem():
    """Load DEM from cache."""
    cache_dir = Path(__file__).parent.parent / 'cache'
    dem_file = cache_dir / 'dem_clean.npy'

    if dem_file.exists():
        dem = np.load(dem_file)
        print(f"✓ Loaded DEM from {dem_file}")
        print(f"  Shape: {dem.shape}")
        return dem
    else:
        print(f"✗ DEM file not found at {dem_file}")
        return None


def extract_region(dem, row_start, col_start, size=81):
    """Extract a terrain region from DEM."""
    row_end = min(row_start + size, dem.shape[0])
    col_end = min(col_start + size, dem.shape[1])

    region = dem[row_start:row_end, col_start:col_end].copy()
    return region


def compute_terrain_complexity(region):
    """Compute terrain complexity metrics."""
    valid_data = region[np.isfinite(region)]

    if len(valid_data) == 0:
        return None

    complexity = {
        'elevation_range': np.nanmax(region) - np.nanmin(region),
        'elevation_std': np.nanstd(region),
        'valid_pixels': np.isfinite(region).sum(),
        'mean_elevation': np.nanmean(region),
    }

    return complexity


def normalize_terrain(region):
    """Normalize terrain elevation to [0, 1]."""
    valid_mask = np.isfinite(region)

    if not valid_mask.any():
        return region, None

    elev_min = np.nanmin(region)
    elev_max = np.nanmax(region)
    elev_range = elev_max - elev_min + 1e-10

    normalized = np.zeros_like(region)
    normalized[valid_mask] = (region[valid_mask] - elev_min) / elev_range
    normalized[~valid_mask] = np.nan

    return normalized, valid_mask


def embed_terrain_region(terrain_norm, p=3, l=6):
    """Embed terrain region using p-adic embedding."""
    size = 3 ** 3  # 27

    # Resize if needed
    if terrain_norm.shape[0] != size or terrain_norm.shape[1] != size:
        scale = size / terrain_norm.shape[0]
        terrain_scaled = zoom(terrain_norm, scale, order=1)
    else:
        terrain_scaled = terrain_norm

    # Create hierarchical mapping
    padic_indices = []
    coords_i = []
    coords_j = []

    def coords_to_padic(i, j, p, l):
        i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
        j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
        padic_int = 0
        for k in range(l):
            digit = j_digits[k // 2] if k % 2 == 0 else i_digits[k // 2]
            padic_int += digit * (p ** k)
        return padic_int

    for i in range(size):
        for j in range(size):
            padic_int = coords_to_padic(i, j, p, l)
            padic_indices.append(padic_int)
            coords_i.append(i)
            coords_j.append(j)

    padic_complete = np.array(padic_indices)
    idx_coords = np.array(coords_i)
    jdx_coords = np.array(coords_j)

    # Look up elevation values
    elevation_values = np.zeros(len(padic_complete), dtype=np.float32)
    for i, (pi, pj) in enumerate(zip(idx_coords, jdx_coords)):
        elevation_values[i] = terrain_scaled[pi, pj]

    valid_mask = np.isfinite(elevation_values)

    # Embed
    padic_points = embed_padic_cloud(padic_complete, p=p, l=l, s=None, m=None)

    return padic_points, elevation_values, valid_mask


def main():
    """Main execution."""

    print("=" * 80)
    print("P-ADIC TERRAIN COMPARISON: MULTIPLE REGIONS")
    print("=" * 80)

    # Load DEM
    dem = load_dem()
    if dem is None:
        print("Cannot proceed without DEM data.")
        return

    # Define terrain regions with varied complexity
    regions = {
        'Flat Area': (100, 100),          # Relatively flat
        'Crater Region': (300, 300),       # Complex circular feature
        'Ridge Feature': (400, 150),       # Linear elevation change
        'Valley Feature': (200, 400),      # Smooth depression
        'Mixed Terrain': (350, 250),       # Varied features
    }

    # P-adic parameters
    p = 3
    l = 6
    s_corrected = get_default_s(p, stability_factor=0.9)
    s_0 = compute_s_0(p)

    print(f"\nP-Adic Parameters:")
    print(f"  Prime base (p): {p}")
    print(f"  Depth (l): {l}")
    print(f"  |s| = {abs(s_corrected):.4f} (constraint: < {s_0:.4f})")
    print(f"  arg(s) = {np.degrees(np.angle(s_corrected)):.0f}°")

    # Extract and analyze regions
    region_data = {}

    print(f"\n" + "=" * 80)
    print("EXTRACTING TERRAIN REGIONS")
    print("=" * 80)

    for name, (row, col) in regions.items():
        print(f"\n{name} (row={row}, col={col}):")

        # Extract
        region = extract_region(dem, row, col, size=81)
        complexity = compute_terrain_complexity(region)

        if complexity:
            print(f"  Elevation range: {complexity['elevation_range']:.1f} m")
            print(f"  Elevation std: {complexity['elevation_std']:.1f} m")
            print(f"  Valid pixels: {complexity['valid_pixels']}")

        # Normalize
        region_norm, valid_mask = normalize_terrain(region)

        # Embed
        padic_points, elevation_values, padic_valid = embed_terrain_region(
            region_norm, p=p, l=l
        )

        region_data[name] = {
            'original': region_norm,
            'padic_points': padic_points,
            'elevation_values': elevation_values,
            'valid_mask': padic_valid,
            'complexity': complexity,
        }

        print(f"  ✓ Embedded {padic_valid.sum()} valid points")

    # Create comparison visualization
    print(f"\n" + "=" * 80)
    print("CREATING COMPARISON VISUALIZATIONS")
    print("=" * 80)

    n_regions = len(regions)
    fig, axes = plt.subplots(n_regions, 2, figsize=(12, 4*n_regions))

    if n_regions == 1:
        axes = [axes]

    for idx, (name, data) in enumerate(region_data.items()):
        # Left: Original terrain
        ax = axes[idx][0]
        im = ax.imshow(data['original'], cmap='viridis', interpolation='nearest')
        ax.set_title(f'{name}\n(Original DEM)', fontsize=11, fontweight='bold')
        ax.axis('off')
        plt.colorbar(im, ax=ax, label='Normalized Elevation')

        # Right: P-adic embedding
        ax = axes[idx][1]
        pts = data['padic_points']
        elev = data['elevation_values']
        valid = data['valid_mask']

        scatter = ax.scatter(
            pts[valid, 0], pts[valid, 1],
            c=elev[valid],
            cmap='viridis',
            s=20,
            alpha=0.85,
            edgecolors='none',
            vmin=0, vmax=1
        )

        ax.set_xlim([pts[:, 0].min() - 0.2, pts[:, 0].max() + 0.2])
        ax.set_ylim([pts[:, 1].min() - 0.2, pts[:, 1].max() + 0.2])
        ax.set_aspect('equal')

        complexity = data['complexity']
        ax.set_title(
            f'{name}\n(P-Adic Embedding)\nRange={complexity["elevation_range"]:.1f}m, '
            f'Std={complexity["elevation_std"]:.1f}m',
            fontsize=11, fontweight='bold'
        )
        ax.set_xlabel('Embedded X')
        ax.set_ylabel('Embedded Y')
        ax.grid(True, alpha=0.2)
        plt.colorbar(scatter, ax=ax, label='Normalized Elevation')

    plt.tight_layout()
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_file = output_dir / 'padic_terrain_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Comparison visualization saved to {output_file}")
    plt.show()

    # Analysis summary
    print(f"\n" + "=" * 80)
    print("REGION ANALYSIS SUMMARY")
    print("=" * 80)

    for name, data in region_data.items():
        complexity = data['complexity']
        valid_count = data['valid_mask'].sum()
        print(f"\n{name}:")
        print(f"  Elevation Range: {complexity['elevation_range']:.1f} m")
        print(f"  Elevation Std: {complexity['elevation_std']:.1f} m")
        print(f"  Valid P-Adic Points: {valid_count} / 729")
        print(f"  Coverage: {100*valid_count/729:.1f}%")

    print(f"\n" + "=" * 80)
    print("✓ P-Adic terrain comparison complete")
    print("=" * 80)


if __name__ == '__main__':
    main()
