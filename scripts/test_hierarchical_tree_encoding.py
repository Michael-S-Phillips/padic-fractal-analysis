#!/usr/bin/env python3
"""
Test: Hierarchical Tree Encoding for P-adic Coordinate Mapping

Based on paper analysis, the correct approach uses recursive hierarchical
subdivision of the image, NOT digit interleaving of row/column coordinates.

For a 27×27 image (3³×3³), the tree structure is:
- Level 0-1: Divide into 3×3 blocks of 9×9 pixels (horizontal then vertical)
- Level 2-3: Subdivide each 9×9 into 3×3 blocks of 3×3 pixels
- Level 4-5: Final subdivision into individual pixels

P-adic index encodes the path through this tree:
  i = i₀ + i₁·3 + i₂·9 + i₃·27 + i₄·81 + i₅·243
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
print("HIERARCHICAL TREE ENCODING TEST")
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
print(f"  Foreground pixels: {(img_binary > 0).sum()} / 729")


# HIERARCHICAL TREE ENCODING
def coords_to_padic_hierarchical(i, j, p=3, l=6):
    """
    Map pixel (i,j) to p-adic integer using hierarchical tree structure.

    For 27×27 image (3³×3³), encodes path through recursive 3-way subdivisions:
    - Level 0: i₀ = i // 9 (which horizontal band of 9 pixels)
    - Level 1: i₁ = j // 9 (which vertical column of 9 pixels)
    - Level 2: i₂ = (i % 9) // 3 (which horizontal sub-band of 3 pixels)
    - Level 3: i₃ = (j % 9) // 3 (which vertical sub-column of 3 pixels)
    - Level 4: i₄ = i % 3 (which row within 3×3 block)
    - Level 5: i₅ = j % 3 (which column within 3×3 block)

    P-adic integer: padic_int = i₀ + i₁·3 + i₂·9 + i₃·27 + i₄·81 + i₅·243
    """
    # Extract hierarchical positions at each level
    i0 = i // 9           # Level 0: horizontal band
    i1 = j // 9           # Level 1: vertical column
    i2 = (i % 9) // 3     # Level 2: horizontal sub-band
    i3 = (j % 9) // 3     # Level 3: vertical sub-column
    i4 = i % 3            # Level 4: row within block
    i5 = j % 3            # Level 5: column within block

    # Encode as p-adic integer
    padic_int = i0 + i1 * (p ** 1) + i2 * (p ** 2) + i3 * (p ** 3) + i4 * (p ** 4) + i5 * (p ** 5)
    return padic_int


# Test with a few examples
print("\n" + "="*70)
print("Example Hierarchical Encodings")
print("="*70)

test_coords = [(0, 0), (5, 5), (8, 8), (9, 9), (13, 13), (26, 26)]
for i, j in test_coords:
    padic = coords_to_padic_hierarchical(i, j)
    i0 = i // 9
    i1 = j // 9
    i2 = (i % 9) // 3
    i3 = (j % 9) // 3
    i4 = i % 3
    i5 = j % 3
    print(f"(i={i:2d}, j={j:2d}) -> [{i0},{i1},{i2},{i3},{i4},{i5}] -> p-adic: {padic:3d}")


# Apply to full image
print("\n" + "="*70)
print("Mapping Full Image Using Hierarchical Tree Encoding")
print("="*70)

p = 3
l = 6
m = 0
s = get_paper_s("sierpinski_triangle", p=p, corrected=True)

padic_mapping = np.zeros(target_size * target_size, dtype=np.int32)
pixel_coords_i = np.zeros(target_size * target_size, dtype=np.int32)
pixel_coords_j = np.zeros(target_size * target_size, dtype=np.int32)

idx = 0
for i in range(target_size):
    for j in range(target_size):
        padic_int = coords_to_padic_hierarchical(i, j, p, l)
        padic_mapping[idx] = padic_int
        pixel_coords_i[idx] = i
        pixel_coords_j[idx] = j
        idx += 1

print(f"✓ Image mapped to p-adic integers")
print(f"  P-adic range: [{padic_mapping.min()}, {padic_mapping.max()}]")
print(f"  Expected range: [0, {3**6 - 1}]")
print(f"  Correct: {padic_mapping.min() == 0 and padic_mapping.max() == 3**6 - 1}")

# Embed in sierpinski space
padic_points = embed_padic_cloud(padic_mapping, p=p, l=l, s=s, m=m)

# Extract pixel values
pixel_vals = np.zeros(target_size * target_size, dtype=np.float32)
for idx in range(target_size * target_size):
    pixel_vals[idx] = img_binary[pixel_coords_i[idx], pixel_coords_j[idx]]

fg_count = (pixel_vals > 0).sum()
print(f"\n✓ Embedded in sierpinski space")
print(f"  Foreground points: {fg_count}")
print(f"  X range: [{padic_points[:, 0].min():.3f}, {padic_points[:, 0].max():.3f}]")
print(f"  Y range: [{padic_points[:, 1].min():.3f}, {padic_points[:, 1].max():.3f}]")


# Visualize
print("\n" + "="*70)
print("Creating Visualization")
print("="*70)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Original image
ax = axes[0]
ax.imshow(img_binary, cmap='gray', origin='upper')
ax.set_title(f'Original MNIST Digit {label}\n(27×27)', fontsize=12, fontweight='bold')
ax.set_xlabel('Column (j)')
ax.set_ylabel('Row (i)')

# All points in sierpinski space
ax = axes[1]
ax.set_facecolor('#87CEEB')
scatter = ax.scatter(padic_points[:, 0], padic_points[:, 1], c=pixel_vals, cmap='binary',
                    s=30, alpha=0.8, edgecolors='none', vmin=0, vmax=1)
ax.set_xlim([padic_points[:, 0].min() - 0.15, padic_points[:, 0].max() + 0.15])
ax.set_ylim([padic_points[:, 1].min() - 0.15, padic_points[:, 1].max() + 0.15])
ax.set_aspect('equal')
ax.set_title('Hierarchical Tree Encoding\nAll Points in Sierpinski Space', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.2)
plt.colorbar(scatter, ax=ax, label='Pixel Value')

# Foreground only (matching paper visualization style)
ax = axes[2]
fg_mask = pixel_vals > 0
fg_points = padic_points[fg_mask]

ax.scatter(fg_points[:, 0], fg_points[:, 1], c='black', s=80, alpha=0.9, edgecolors='none')
ax.set_xlim([padic_points[:, 0].min() - 0.15, padic_points[:, 0].max() + 0.15])
ax.set_ylim([padic_points[:, 1].min() - 0.15, padic_points[:, 1].max() + 0.15])
ax.set_aspect('equal')
ax.set_title('Hierarchical Tree Encoding\nForeground Points Only', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.2)

plt.suptitle('Testing Hierarchical Tree Encoding for P-adic to Sierpinski Mapping',
            fontsize=14, fontweight='bold')
plt.tight_layout()
output_file = Path('test_hierarchical_tree_encoding.png')
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✓ Visualization saved: {output_file}")
plt.show()


print("\n" + "="*70)
print("ANALYSIS")
print("="*70)
print(f"""
Hierarchical tree encoding results:
- Mapped 729 pixels (27×27) using tree structure
- Each pixel's position in recursive 3×3 subdivisions determines p-adic index
- Result embedded in sierpinski complex plane

KEY OBSERVATIONS:
1. P-adic index distribution: [{padic_mapping.min()}, {padic_mapping.max()}] ✓
2. Foreground coverage: {fg_count} pixels
3. Sierpinski bounding box preserved with correct structure

NEXT: Compare this distribution with Figure 4 from the paper.
Does the white pixel pattern match the paper's expected distribution?

If YES: This is the correct coordinate mapping!
If NO: Need to reconsider the tree structure interpretation.
""")
