#!/usr/bin/env python3
"""
Debug: Which coordinate mapping method is correct?
Compares 4 different approaches to map pixel coords (i,j) to p-adic integers.
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
print("COORDINATE MAPPING DEBUG")
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
img_norm = img_resized / 255.0
img_binary = (img_norm > 0.5).astype(np.float32)

print(f"✓ MNIST digit {label} prepared (27×27)")
print(f"  Foreground pixels: {(img_binary > 0).sum()} / 729")

# Define mapping methods
def coords_to_padic_CURRENT(i, j, p=3, l=6):
    """CURRENT: j[0], i[0], j[1], i[1], j[2], i[2]"""
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
    padic_int = 0
    for k in range(l):
        digit = j_digits[k // 2] if k % 2 == 0 else i_digits[k // 2]
        padic_int += digit * (p ** k)
    return padic_int


def coords_to_padic_ALT1(i, j, p=3, l=6):
    """ALT1: i[0], j[0], i[1], j[1], i[2], j[2]"""
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
    padic_int = 0
    for k in range(l):
        digit = i_digits[k // 2] if k % 2 == 0 else j_digits[k // 2]
        padic_int += digit * (p ** k)
    return padic_int


def coords_to_padic_ALT2(i, j, p=3, l=6):
    """ALT2: i then j concatenation"""
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
    padic_int = 0
    for k in range(3):
        padic_int += i_digits[k] * (p ** k)
    for k in range(3):
        padic_int += j_digits[k] * (p ** (k + 3))
    return padic_int


def coords_to_padic_ALT3(i, j, p=3, l=6):
    """ALT3: j then i concatenation"""
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]
    padic_int = 0
    for k in range(3):
        padic_int += j_digits[k] * (p ** k)
    for k in range(3):
        padic_int += i_digits[k] * (p ** (k + 3))
    return padic_int


# Test each method
p = 3
l = 6
m = 0
s = get_paper_s("sierpinski_triangle", p=p, corrected=True)

methods = [
    ("CURRENT (j,i interleave)", coords_to_padic_CURRENT),
    ("ALT1 (i,j interleave)", coords_to_padic_ALT1),
    ("ALT2 (i+j concat)", coords_to_padic_ALT2),
    ("ALT3 (j+i concat)", coords_to_padic_ALT3),
]

results = {}

print(f"\n{'='*70}")
print("Processing each mapping method...")
print(f"{'='*70}")

for method_name, coords_func in methods:
    print(f"\n{method_name}")

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
        'mapping': padic_mapping
    }

    fg_count = (pixel_vals > 0).sum()
    print(f"  ✓ Foreground points: {fg_count}")
    print(f"  ✓ X range: [{padic_points[:, 0].min():.3f}, {padic_points[:, 0].max():.3f}]")
    print(f"  ✓ Y range: [{padic_points[:, 1].min():.3f}, {padic_points[:, 1].max():.3f}]")

print(f"\n✓ All methods processed")

# Create visualization
fig, axes = plt.subplots(2, 5, figsize=(25, 10))

# Row 1: Original + 3 methods
ax = axes[0, 0]
ax.imshow(img_binary, cmap='gray', origin='upper')
ax.set_title('Original Image', fontsize=11, fontweight='bold')
ax.axis('off')

for col, (method_name, _) in enumerate(methods):
    ax = axes[0, col + 1]
    points = results[method_name]['points']
    values = results[method_name]['values']

    ax.set_facecolor('#87CEEB')
    scatter = ax.scatter(points[:, 0], points[:, 1], c=values, cmap='binary',
                        s=30, alpha=0.8, edgecolors='none', vmin=0, vmax=1)
    ax.set_xlim([points[:, 0].min() - 0.15, points[:, 0].max() + 0.15])
    ax.set_ylim([points[:, 1].min() - 0.15, points[:, 1].max() + 0.15])
    ax.set_aspect('equal')
    ax.set_title(method_name, fontsize=10, fontweight='bold')
    ax.grid(True, alpha=0.2)

# Row 2: Foreground only
for col, (method_name, _) in enumerate(methods):
    ax = axes[1, col + 1]
    points = results[method_name]['points']
    values = results[method_name]['values']

    fg_mask = values > 0
    fg_points = points[fg_mask]

    ax.scatter(fg_points[:, 0], fg_points[:, 1], c='black', s=50, alpha=0.8)
    ax.set_xlim([points[:, 0].min() - 0.15, points[:, 0].max() + 0.15])
    ax.set_ylim([points[:, 1].min() - 0.15, points[:, 1].max() + 0.15])
    ax.set_aspect('equal')
    ax.set_title(f'{method_name} (FG)', fontsize=9, fontweight='bold')
    ax.grid(True, alpha=0.2)

axes[1, 0].axis('off')

plt.suptitle('Comparing Coordinate Mapping Methods\nWhich matches Figure 4 from the paper?',
            fontsize=14, fontweight='bold')
plt.tight_layout()
output_file = Path('debug_all_methods.png')
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\n✓ Visualization saved: {output_file}")
plt.show()

print(f"\n{'='*70}")
print("ANALYSIS REQUIRED")
print(f"{'='*70}")
print("""
Compare the four sierpinski embeddings above with Figure 4 from the paper.

Looking at white pixel distribution:
1. CURRENT method: j[0], i[0], j[1], i[1], j[2], i[2]
2. ALT1 method: i[0], j[0], i[1], j[1], i[2], j[2]
3. ALT2 method: i (low positions) + j (high positions)
4. ALT3 method: j (low positions) + i (high positions)

Which one produces the correct distribution that matches the paper?
""")
