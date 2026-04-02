#!/usr/bin/env python3
"""
Quick test to verify p-adic embedding fix.

Run this before running the full MNIST notebook to check if the embedding
is now properly distributed across [0,1]×[0,1].
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / 'src'))

from padic.padic_embedding import embed_padic_cloud

# Test parameters (same as MNIST notebook)
p = 3
l = 6
total_regions = p ** l  # 729

print("=" * 70)
print("P-ADIC EMBEDDING FIX VERIFICATION")
print("=" * 70)

print(f"\nParameters:")
print(f"  p (prime base): {p}")
print(f"  l (depth): {l}")
print(f"  Total regions: {total_regions}")
print(f"  Expected grid side: sqrt({total_regions}) ≈ {int(np.sqrt(total_regions))}")

# Generate test indices
padic_ints = np.arange(total_regions)

# Test both methods
for method in ['hilbert', 'digits']:
    print(f"\n--- Testing '{method}' method ---")

    points = embed_padic_cloud(padic_ints, p=p, l=l, method=method)

    # Analysis
    print(f"Points shape: {points.shape}")
    print(f"X range: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}]")
    print(f"Y range: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}]")

    # Check distribution
    center_x = (points[:, 0] > 0.25) & (points[:, 0] < 0.75)
    center_y = (points[:, 1] > 0.25) & (points[:, 1] < 0.75)
    center_count = (center_x & center_y).sum()

    print(f"Points in center region [0.25,0.75]×[0.25,0.75]: {center_count} ({100*center_count/len(points):.1f}%)")

    # Visual test
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(points[:, 0], points[:, 1], s=5, alpha=0.6, edgecolors='none')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'P-Adic Embedding (p={p}, l={l})\nMethod: {method.upper()}')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    # Add reference grid
    for i in np.linspace(0, 1, 5):
        ax.axhline(i, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
        ax.axvline(i, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

    plt.tight_layout()
    plt.savefig(f'test_embedding_{method}.png', dpi=100, bbox_inches='tight')
    print(f"✓ Saved visualization to test_embedding_{method}.png")
    plt.close()

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\nExpected results after fix:")
print("  ✓ Points distributed across most of [0,1]×[0,1]")
print("  ✓ X and Y ranges close to [0, 1]")
print("  ✓ No clustering in tiny corner region")
print("  ✓ Clear Sierpinski-like patterns visible")
print("\nIf you see this, the fix worked! Run the MNIST notebook:")
print("  jupyter notebook notebooks/07_mnist_padic_visualization.ipynb")
