#!/usr/bin/env python3
"""
Build and save the p-adic quadtree from DEM.

This script:
1. Loads the DEM
2. Builds the quadtree
3. Saves it to disk for reuse
4. Provides basic statistics
"""

import sys
import pickle
from pathlib import Path

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')

from padic import preprocessing, quadtree

# Paths
DATA_DIR = Path('/Volumes/Fangorn/padic_fractal_analysis/data')
CACHE_DIR = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
CACHE_DIR.mkdir(exist_ok=True)

QUADTREE_CACHE = CACHE_DIR / 'quadtree.pkl'
DEM_CACHE = CACHE_DIR / 'dem_clean.npy'
METADATA_CACHE = CACHE_DIR / 'dem_metadata.txt'


def build_and_cache_quadtree():
    """Build quadtree and save to disk."""

    print("=" * 80)
    print("QUADTREE BUILD AND CACHE")
    print("=" * 80)

    # Load DEM
    print("\n1. Loading DEM...")
    dem_file = list(DATA_DIR.glob('*.tif'))[0]
    print(f"   File: {dem_file.name}")

    dem, metadata = preprocessing.load_dem(str(dem_file))
    dem_clean, _ = preprocessing.preprocess_dem(dem)
    print(f"   Shape: {dem_clean.shape}")
    print(f"   Type: {dem_clean.dtype}")
    print(f"   Range: {dem_clean.min():.2f} to {dem_clean.max():.2f}")
    print(f"   NaN count: {(dem_clean != dem_clean).sum()}")

    # Build quadtree
    print("\n2. Building quadtree...")
    print("   (This may take several minutes...)")
    qtree = quadtree.PadicQuadtree(dem_clean)
    print(f"   ✓ Built successfully")

    # Get statistics
    print("\n3. Quadtree Statistics:")
    print(f"   Max depth: {qtree.max_depth}")
    print(f"   Root bounds: {qtree.root.bounds}")
    print(f"   Root num_pixels: {qtree.root.num_pixels}")
    print(f"   Root elevation_mean: {qtree.root.elevation_mean:.2f}")
    print(f"   Root elevation_variance: {qtree.root.elevation_variance:.6f}")
    print(f"   Root elevation_min: {qtree.root.elevation_min:.2f}")
    print(f"   Root elevation_max: {qtree.root.elevation_max:.2f}")
    print(f"   Root roughness: {qtree.root.roughness:.6f}")

    # Analyze tree structure
    print("\n4. Tree Structure Analysis:")
    level_counts = {}

    def count_nodes(node, counts):
        """Recursively count nodes at each level."""
        if node.level not in counts:
            counts[node.level] = 0
        counts[node.level] += 1
        for child in node.children:
            count_nodes(child, counts)

    count_nodes(qtree.root, level_counts)

    print("   Level  | Count | Avg Variance")
    print("   " + "-" * 40)
    for level in sorted(level_counts.keys()):
        count = level_counts[level]
        # Get sample nodes to compute avg variance
        nodes_at_level = []

        def get_nodes_at_level(node, target_level, result):
            if node.level == target_level:
                result.append(node)
            elif node.level < target_level:
                for child in node.children:
                    get_nodes_at_level(child, target_level, result)

        get_nodes_at_level(qtree.root, level, nodes_at_level)
        if nodes_at_level:
            avg_var = sum(n.elevation_variance for n in nodes_at_level) / len(nodes_at_level)
            print(f"   {level:5d} | {count:5d} | {avg_var:.8f}")

    # Save to disk
    print("\n5. Caching to disk...")

    # Save DEM
    import numpy as np
    np.save(DEM_CACHE, dem_clean)
    print(f"   ✓ DEM saved: {DEM_CACHE}")

    # Save metadata
    with open(METADATA_CACHE, 'w') as f:
        f.write(f"DEM Shape: {dem_clean.shape}\n")
        f.write(f"DEM Type: {dem_clean.dtype}\n")
        f.write(f"DEM Range: {dem_clean.min():.2f} to {dem_clean.max():.2f}\n")
        f.write(f"Quadtree Max Depth: {qtree.max_depth}\n")
        f.write(f"Root Num Pixels: {qtree.root.num_pixels}\n")
    print(f"   ✓ Metadata saved: {METADATA_CACHE}")

    # Save quadtree (pickle)
    print("   Saving quadtree (this may take a moment)...")
    with open(QUADTREE_CACHE, 'wb') as f:
        pickle.dump(qtree, f)

    file_size_mb = QUADTREE_CACHE.stat().st_size / (1024 * 1024)
    print(f"   ✓ Quadtree saved: {QUADTREE_CACHE} ({file_size_mb:.1f} MB)")

    print("\n" + "=" * 80)
    print("✓ QUADTREE BUILD COMPLETE")
    print("=" * 80)
    print(f"\nTo load the quadtree in future scripts:")
    print(f"  import pickle")
    print(f"  with open('{QUADTREE_CACHE}', 'rb') as f:")
    print(f"      qtree = pickle.load(f)")
    print()

    return qtree, dem_clean


if __name__ == '__main__':
    qtree, dem_clean = build_and_cache_quadtree()
