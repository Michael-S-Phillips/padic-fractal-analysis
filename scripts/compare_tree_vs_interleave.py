#!/usr/bin/env python3
"""
Compare: Hierarchical Tree Encoding vs Digit Interleaving

This script generates side-by-side visualizations comparing:
1. Hierarchical tree encoding (NEW - based on paper)
2. Digit interleaving approach (OLD - from MNIST notebook)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent / 'src'))

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom
from padic.padic_embedding import embed_padic_cloud, get_paper_s
from keras.datasets import mnist

print("="*70)
print("COMPARING TREE ENCODING vs DIGIT INTERLEAVING")
print("="*70)

# Load MNIST
(X_train, y_train), (X_test, y_test) = mnist.load_data()
print("\n✓ MNIST loaded")

# Prepare digit
target_size = 27
img_raw = X_train[0]
label = y_train[0]

scale = target_size / img_raw.shape[0]
img_resized = zoom(img_raw.astype(np.float32), scale, order=1)
img_binary = (img_resized > 75).astype(np.float32)

print(f"✓ MNIST digit {label} prepared (27×27)")

# Method 1: Hierarchical Tree Encoding (NEW)
def coords_to_padic_hierarchical(i, j, p=3, l=6):
    """Hierarchical tree structure"""
    i0 = i // 9
    i1 = j // 9
    i2 = (i % 9) // 3
    i3 = (j % 9) // 3
    i4 = i % 3
    i5 = j % 3
    return i0 + i1 * (p ** 1) + i2 * (p ** 2) + i3 * (p ** 3) + i4 * (p ** 4) + i5 * (p ** 5)

# Method 2: Digit Interleaving (OLD)
def coords_to_padic_interleave(i, j, p=3, l=6):
    """Hierarchical interleaving: j[0], i[0], j[1], i[1], j[2], i[2]"""
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
    padic_int = 0
    for k in range(l):
        digit = j_digits[k // 2] if k % 2 == 0 else i_digits[k // 2]
        padic_int += digit * (p ** k)
    return padic_int

# Setup for embedding
p = 3
l = 6
m = 0
s = get_paper_s("sierpinski_triangle", p=p, corrected=True)

# Process both methods
methods = {
    'Hierarchical Tree\n(NEW)': coords_to_padic_hierarchical,
    'Digit Interleaving\n(OLD)': coords_to_padic_interleave,
}

results = {}

for method_name, coords_func in methods.items():
    print(f"\nProcessing: {method_name.replace(chr(10), ' ')}")

    # Create p-adic mapping
    padic_mapping = np.zeros(target_size * target_size, dtype=np.int32)
    pixel_coords_i = np.zeros(target_size * target_size, dtype=np.int32)
    pixel_coords_j = np.zeros(target_size * target_size, dtype=np.int32)

    idx = 0
    for i in range(target_size):
        for j in range(target_size):
            padic_int = coords_func(i, j, p, l)
            padic_mapping[idx] = padic_int
            pixel_coords_i[idx] = i
            pixel_coords_j[idx] = j
            idx += 1

    # Embed in sierpinski space
    padic_points = embed_padic_cloud(padic_mapping, p=p, l=l, s=s, m=m)

    # Extract pixel values
    pixel_vals = np.zeros(target_size * target_size, dtype=np.float32)
    for idx in range(target_size * target_size):
        pixel_vals[idx] = img_binary[pixel_coords_i[idx], pixel_coords_j[idx]]

    results[method_name] = {
        'points': padic_points,
        'values': pixel_vals,
    }

    fg_count = (pixel_vals > 0).sum()
    print(f"  ✓ Foreground points: {fg_count}")
    print(f"  ✓ X range: [{padic_points[:, 0].min():.3f}, {padic_points[:, 0].max():.3f}]")
    print(f"  ✓ Y range: [{padic_points[:, 1].min():.3f}, {padic_points[:, 1].max():.3f}]")

# Visualize comparison
print("\n" + "="*70)
print("Creating Comparison Visualization")
print("="*70)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Row 1: Original image + both methods
ax = axes[0, 0]
ax.imshow(img_binary, cmap='gray', origin='upper')
ax.set_title(f'Original MNIST Digit {label}\n(27×27)', fontsize=12, fontweight='bold')
ax.set_xlabel('Column (j)')
ax.set_ylabel('Row (i)')
ax.grid(True, alpha=0.2)

col = 1
for method_name, result_data in results.items():
    ax = axes[0, col]
    points = result_data['points']
    values = result_data['values']

    ax.set_facecolor('#87CEEB')
    scatter = ax.scatter(points[:, 0], points[:, 1], c=values, cmap='binary',
                        s=30, alpha=0.8, edgecolors='none', vmin=0, vmax=1)
    ax.set_xlim([points[:, 0].min() - 0.15, points[:, 0].max() + 0.15])
    ax.set_ylim([points[:, 1].min() - 0.15, points[:, 1].max() + 0.15])
    ax.set_aspect('equal')
    ax.set_title(f'{method_name}\nAll Points', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.2)

    col += 1

# Row 2: Foreground only comparison
col = 1
for method_name, result_data in results.items():
    ax = axes[1, col]
    points = result_data['points']
    values = result_data['values']

    fg_mask = values > 0
    fg_points = points[fg_mask]

    ax.scatter(fg_points[:, 0], fg_points[:, 1], c='black', s=80, alpha=0.9, edgecolors='none')
    ax.set_xlim([points[:, 0].min() - 0.15, points[:, 0].max() + 0.15])
    ax.set_ylim([points[:, 1].min() - 0.15, points[:, 1].max() + 0.15])
    ax.set_aspect('equal')
    ax.set_title(f'{method_name}\nForeground Only', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.2)

    col += 1

axes[1, 0].axis('off')

plt.suptitle('Comparing P-adic Coordinate Mapping Methods\nHierarchical Tree vs Digit Interleaving',
            fontsize=14, fontweight='bold')
plt.tight_layout()
output_file = Path('compare_tree_vs_interleave.png')
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✓ Comparison visualization saved: {output_file}")
plt.show()

print("\n" + "="*70)
print("COMPARISON ANALYSIS")
print("="*70)
print(f"""
Both methods produce sierpinski-structured embeddings, but with different
white pixel distributions. The key question: which matches Figure 4 from
the paper?

HIERARCHICAL TREE ENCODING (NEW):
- Based on recursive subdivision of image space
- Each level encodes position in 3×3 blocks
- Alternates between horizontal and vertical subdivisions
- More natural representation of spatial hierarchy

DIGIT INTERLEAVING (OLD):
- Based on interleaving base-3 digits of row/column indices
- Digit pattern: j[0], i[0], j[1], i[1], j[2], i[2]
- Was extracted from MNIST notebook
- May not reflect true p-adic structure

NEXT STEP:
Compare the foreground distributions above with Figure 4 from the paper
to determine which approach is correct.
""")
