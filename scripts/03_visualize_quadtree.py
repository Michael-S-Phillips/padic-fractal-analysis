#!/usr/bin/env python3
"""
Visualize the p-adic quadtree in Sierpinski-like form.

Uses cached quadtree data to create:
1. Point cloud visualization (hierarchical decomposition)
2. Variance-colored map
3. Progressive level refinement
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import deque

CACHE_DIR = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
QUADTREE_CACHE = CACHE_DIR / 'quadtree.pkl'
DEM_CACHE = CACHE_DIR / 'dem_clean.npy'
OUTPUT_DIR = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
OUTPUT_DIR.mkdir(exist_ok=True)


def load_cached_data():
    """Load quadtree and DEM from cache."""
    if not QUADTREE_CACHE.exists():
        print(f"ERROR: Quadtree not cached. Run: python3 01_build_and_save_quadtree.py")
        return None, None

    print("Loading cached quadtree...")
    with open(QUADTREE_CACHE, 'rb') as f:
        qtree = pickle.load(f)

    print("Loading cached DEM...")
    dem_clean = np.load(DEM_CACHE)

    print(f"✓ Loaded: qtree(depth={qtree.max_depth}), dem{dem_clean.shape}")
    return qtree, dem_clean


def collect_node_points(qtree, level_max=None):
    """
    Collect quadtree node center points.

    Returns dict mapping level -> list of (col, row) tuples (normalized to [0,1])
    """
    if level_max is None:
        level_max = min(qtree.max_depth, 12)

    points_by_level = {}
    queue = deque([qtree.root])

    while queue:
        node = queue.popleft()

        # Collect this node
        if node.level not in points_by_level:
            points_by_level[node.level] = []

        min_row, max_row, min_col, max_col = node.bounds
        center_row = (min_row + max_row) / 2.0
        center_col = (min_col + max_col) / 2.0

        # Normalize to [0, 1]
        norm_row = center_row / qtree.height
        norm_col = center_col / qtree.width

        points_by_level[node.level].append((norm_col, norm_row))

        # Add children if not at max level
        if node.level < level_max and not node.is_leaf():
            queue.extend(node.children)

    return points_by_level


def plot_padic_points(qtree, points_by_level, level_max, ax, color='black', s=3):
    """Plot quadtree points as Sierpinski-like visualization."""

    for level in sorted(points_by_level.keys()):
        if level <= level_max:
            points = np.array(points_by_level[level])

            if len(points) > 0:
                # Size decreases with level
                size = max(0.5, s * (1.0 / (2.0 ** (level / 2))))

                # Alpha increases with level (deeper = more visible)
                alpha = min(1.0, 0.2 + 0.8 * (level / (level_max + 1)))

                print(f"  Level {level:2d}: {len(points):6d} points, size={size:.2f}, alpha={alpha:.2f}")

                ax.scatter(
                    points[:, 0], points[:, 1], s=size, c=color, alpha=alpha, rasterized=True
                )

    ax.set_aspect('equal')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.invert_yaxis()
    ax.set_xlabel('Column (normalized)')
    ax.set_ylabel('Row (normalized)')


def visualize_main(qtree, dem_clean):
    """Create main visualizations."""

    print("\n" + "=" * 80)
    print("CREATING VISUALIZATIONS")
    print("=" * 80)

    # Collect points
    print("\nCollecting node points...")
    points_all = collect_node_points(qtree, level_max=qtree.max_depth)
    print(f"✓ Collected {sum(len(p) for p in points_all.values())} total nodes")

    # =========================================================================
    # Visualization 1: P-Adic Sierpinski Form (Main figure)
    # =========================================================================
    print("\n1. Creating p-adic Sierpinski visualization...")
    fig, (ax_light, ax_dark) = plt.subplots(1, 2, figsize=(16, 7))

    points_light = collect_node_points(qtree, level_max=11)
    plot_padic_points(qtree, points_light, 11, ax_light, color='black', s=3)
    ax_light.set_title(
        'P-Adic Form: CTX Terrain Hierarchy\n(Sierpinski-like decomposition)',
        fontweight='bold',
        fontsize=13,
    )
    ax_light.set_facecolor('lightblue')

    # Dark version
    plot_padic_points(qtree, points_light, 11, ax_dark, color='white', s=3)
    ax_dark.set_title('P-Adic Form (Binary)', fontweight='bold', fontsize=13)
    ax_dark.set_facecolor('black')
    for spine in ax_dark.spines.values():
        spine.set_visible(False)
    ax_dark.set_xticks([])
    ax_dark.set_yticks([])

    plt.tight_layout()
    output_file = OUTPUT_DIR / 'padic_sierpinski.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

    # =========================================================================
    # Visualization 2: Progressive Refinement
    # =========================================================================
    print("\n2. Creating progressive refinement visualization...")
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    for idx, level_max in enumerate([6, 8, 10, 11, 12, 13]):
        ax = axes.flat[idx]
        target_level = min(level_max, qtree.max_depth)

        print(f"   Panel {idx + 1}: Levels 0-{target_level}...")
        points_partial = collect_node_points(qtree, level_max=target_level)
        plot_padic_points(
            qtree, points_partial, target_level, ax, color='black', s=2.5
        )
        ax.set_title(f'Levels 0-{target_level}', fontweight='bold')

    fig.suptitle(
        'P-Adic Quadtree: Progressive Refinement', fontsize=14, fontweight='bold'
    )
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'padic_progressive.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

    # =========================================================================
    # Visualization 3: Multi-panel Comparison
    # =========================================================================
    print("\n3. Creating multi-panel comparison...")
    fig = plt.figure(figsize=(18, 12))

    # Panel 1: P-adic structure (up to level 10)
    print("   Panel 1: P-adic structure...")
    ax1 = plt.subplot(2, 3, 1)
    points_1 = collect_node_points(qtree, level_max=10)
    plot_padic_points(qtree, points_1, 10, ax1, color='black', s=2)
    ax1.set_title('P-Adic Quadtree (Levels 0-10)\n(Sierpinski-like point cloud)', fontweight='bold')

    # Panel 2: Extended p-adic
    print("   Panel 2: Extended p-adic...")
    ax2 = plt.subplot(2, 3, 2)
    points_2 = collect_node_points(qtree, level_max=12)
    plot_padic_points(qtree, points_2, 12, ax2, color='darkblue', s=1.5)
    ax2.set_title('P-Adic Quadtree (Extended)', fontweight='bold')

    # Panel 3: Density map (histogram of points)
    print("   Panel 3: Point density map...")
    ax3 = plt.subplot(2, 3, 3)
    all_points = np.vstack(
        [np.array(points_2[level]) for level in points_2.keys()]
    )
    h, xedges, yedges = np.histogram2d(
        all_points[:, 0], all_points[:, 1], bins=64
    )
    im = ax3.imshow(
        h.T, origin='lower', extent=[0, 1, 0, 1], cmap='hot', aspect='auto'
    )
    ax3.set_xlabel('Column (normalized)')
    ax3.set_ylabel('Row (normalized)')
    ax3.set_title('Point Density Distribution', fontweight='bold')
    plt.colorbar(im, ax=ax3, label='Point count')

    # Panel 4: Original DEM
    print("   Panel 4: Original DEM...")
    ax4 = plt.subplot(2, 3, 4)
    im4 = ax4.imshow(dem_clean, cmap='gray')
    ax4.set_title('Original DEM (CTX)', fontweight='bold')
    plt.colorbar(im4, ax=ax4, label='Elevation (m)')

    # Panel 5: Level 4 statistics
    print("   Panel 5: Level 4 variance...")
    ax5 = plt.subplot(2, 3, 5)
    try:
        mean_grid, var_grid, rough_grid = qtree.extract_statistics_grid(4)
        im5 = ax5.imshow(var_grid, cmap='hot')
        ax5.set_title('Quadtree Level 4: Elevation Variance', fontweight='bold')
        plt.colorbar(im5, ax=ax5, label='Variance')
    except Exception as e:
        ax5.text(0.5, 0.5, f'Error:\n{str(e)[:50]}', ha='center', va='center')
        ax5.set_title('Level 4 Statistics (Error)', fontweight='bold')

    # Panel 6: Roughness
    print("   Panel 6: Level 4 roughness...")
    ax6 = plt.subplot(2, 3, 6)
    try:
        im6 = ax6.imshow(rough_grid, cmap='viridis')
        ax6.set_title('Quadtree Level 4: Roughness', fontweight='bold')
        plt.colorbar(im6, ax=ax6, label='Roughness')
    except Exception as e:
        ax6.text(0.5, 0.5, f'Error:\n{str(e)[:50]}', ha='center', va='center')
        ax6.set_title('Level 4 Roughness (Error)', fontweight='bold')

    plt.tight_layout()
    output_file = OUTPUT_DIR / 'padic_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("✓ VISUALIZATION COMPLETE")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  - padic_sierpinski.png (P-adic Sierpinski-like form)")
    print(f"  - padic_progressive.png (Progressive refinement)")
    print(f"  - padic_comparison.png (6-panel comparison)")
    print(f"\nAll files saved to: {OUTPUT_DIR}")
    print()


if __name__ == '__main__':
    qtree, dem_clean = load_cached_data()

    if qtree is not None and dem_clean is not None:
        visualize_main(qtree, dem_clean)
    else:
        print("ERROR: Could not load data")
