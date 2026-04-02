#!/usr/bin/env python3
"""
2D Sierpinski Terrain Fractality Analysis (Corrected)

Uses hierarchical ternary digit interleaving (from MNIST notebook)
to correctly map pixel coordinates to p-adic integers.

Key insight:
- Pixel location (i,j) → ternary digit hierarchy → p-adic integer
- p-adic integer → sierpinski coordinate (via Chistyakov embedding)
- Elevation value at (i,j) → data at sierpinski coordinate
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, Normalize
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def create_hillshade(dem, azimuth=315, altitude=45):
    """Create hillshade from DEM using light source."""
    ls = LightSource(azdeg=azimuth, altdeg=altitude)
    hillshade = ls.hillshade(dem, vert_exag=0.1)
    return hillshade

def coords_to_padic(i, j, p=3, l=6):
    """
    Convert 2D pixel coordinates to p-adic integer using hierarchical digit interleaving.

    This is the CORRECT method from the MNIST notebook.
    For a 27×27 image with p=3, each coordinate extracts 3 ternary digits.
    Digits are interleaved: j[0], i[0], j[1], i[1], j[2], i[2]
    """
    # Extract ternary digits (base 3)
    i_digits = [i % 3, (i // 3) % 3, (i // 9) % 3]
    j_digits = [j % 3, (j // 3) % 3, (j // 9) % 3]

    # Hierarchically interleave: alternating j and i digits
    padic_int = 0
    for k in range(l):
        # Alternate: k=0 uses j[0], k=1 uses i[0], k=2 uses j[1], k=3 uses i[1], etc.
        digit = j_digits[k // 2] if k % 2 == 0 else i_digits[k // 2]
        padic_int += digit * (p ** k)

    return padic_int

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')

    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape

    print("=" * 70)
    print("SIERPINSKI TERRAIN FRACTALITY (CORRECTED - HIERARCHICAL INTERLEAVING)")
    print("=" * 70)
    print(f"DEM shape: {dem_data.shape}")
    print(f"DEM range: [{dem_data.min():.1f}, {dem_data.max():.1f}] meters")

    # P-adic parameters (corrected)
    p = 3
    l = 6
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    m = 0

    print(f"\nP-Adic Parameters (CORRECTED):")
    print(f"  p = {p}")
    print(f"  l = {l}")
    print(f"  s = {s:.4f} (corrected sign)")
    print(f"  m = {m}")
    print(f"  Total p-adic regions: {p**l}")

    # Step 1: Generate p-adic mappings for all pixels
    print(f"\nGenerating p-adic mappings for all {h*w:,} pixels...")
    padic_indices = np.zeros(h * w, dtype=np.int32)
    pixel_idx = 0
    for i in range(h):
        if i % 200 == 0:
            print(f"  Row {i}/{h}...")
        for j in range(w):
            padic_indices[pixel_idx] = coords_to_padic(i, j, p=p, l=l)
            pixel_idx += 1

    print(f"  P-adic range: [{padic_indices.min()}, {padic_indices.max()}]")
    print(f"  Expected range: [0, {p**l - 1}]")

    # Step 2: Embed p-adic integers into sierpinski space
    print(f"\nEmbedding {len(padic_indices):,} p-adic integers into sierpinski space...")
    sierpinski_coords = embed_padic_cloud(padic_indices, p=p, l=l, s=s, m=m)

    print(f"  Sierpinski X range: [{sierpinski_coords[:, 0].min():.3f}, {sierpinski_coords[:, 0].max():.3f}]")
    print(f"  Sierpinski Y range: [{sierpinski_coords[:, 1].min():.3f}, {sierpinski_coords[:, 1].max():.3f}]")

    # Step 3: Build global elevation distribution across sierpinski regions
    print(f"\nBuilding global elevation distribution across sierpinski coordinates...")
    dem_flat = dem_data.flatten()

    # Create 2D histogram: elevation values distributed across sierpinski space
    global_hist, x_edges, y_edges = np.histogram2d(
        sierpinski_coords[:, 0],
        sierpinski_coords[:, 1],
        bins=50,
        weights=dem_flat
    )
    global_counts, _, _ = np.histogram2d(
        sierpinski_coords[:, 0],
        sierpinski_coords[:, 1],
        bins=50
    )

    # Average elevation per sierpinski region
    global_elev_avg = np.divide(global_hist, global_counts, where=global_counts>0, out=np.zeros_like(global_hist))

    print(f"  Global elevation histogram shape: {global_elev_avg.shape}")
    print(f"  Non-empty sierpinski regions: {np.sum(global_counts > 0)}")

    # Initialize output map
    similarity_map = np.zeros((h, w), dtype=np.float32)

    window_size = 27
    half_window = window_size // 2

    print(f"\nProcessing {h:,} rows × {w:,} cols with {window_size}×{window_size} windows...")

    # Step 4: For each pixel, analyze its local window
    for y in range(h):
        if y % 100 == 0:
            print(f"  Row {y}/{h}...")

        for x in range(w):
            # Extract window bounds
            y1 = max(0, y - half_window)
            y2 = min(h, y + half_window + 1)
            x1 = max(0, x - half_window)
            x2 = min(w, x + half_window + 1)

            # Get window pixel coordinates and p-adic mappings
            window_padic_list = []
            window_elevations = []

            for wi in range(y1, y2):
                for wj in range(x1, x2):
                    padic_int = coords_to_padic(wi, wj, p=p, l=l)
                    window_padic_list.append(padic_int)
                    window_elevations.append(dem_data[wi, wj])

            if len(window_padic_list) < 9:
                continue

            window_padic_array = np.array(window_padic_list, dtype=np.int32)
            window_elevations_array = np.array(window_elevations, dtype=np.float32)

            # Embed window p-adic integers into sierpinski space
            window_sierpinski = embed_padic_cloud(window_padic_array, p=p, l=l, s=s, m=m)

            # Create local elevation histogram in sierpinski space
            local_hist, _, _ = np.histogram2d(
                window_sierpinski[:, 0],
                window_sierpinski[:, 1],
                bins=50,
                weights=window_elevations_array
            )
            local_counts, _, _ = np.histogram2d(
                window_sierpinski[:, 0],
                window_sierpinski[:, 1],
                bins=50
            )

            # Average elevation in this local window
            local_elev_avg = np.divide(local_hist, local_counts, where=local_counts>0, out=np.zeros_like(local_hist))

            # Compare elevation distributions using correlation
            global_flat = global_elev_avg.flatten()
            local_flat = local_elev_avg.flatten()

            # Only compare at bins with valid data
            valid_idx = (global_counts.flatten() > 0) & (local_counts.flatten() > 0)

            if np.sum(valid_idx) > 2:
                try:
                    corr = np.corrcoef(global_flat[valid_idx], local_flat[valid_idx])[0, 1]
                    similarity_map[y, x] = max(0, corr if not np.isnan(corr) else 0)
                except:
                    similarity_map[y, x] = 0

    print(f"\n✓ Analysis complete!")

    # Statistics
    valid = similarity_map[similarity_map > 0]
    if len(valid) > 0:
        print(f"\nSimilarity Statistics:")
        print(f"  Min: {valid.min():.4f}")
        print(f"  Max: {valid.max():.4f}")
        print(f"  Mean: {valid.mean():.4f}")
        print(f"  Median: {np.median(valid):.4f}")
        print(f"  Std: {valid.std():.4f}")

    # Save results
    np.save(str(cache_dir / 'sierpinski_terrain_fractality_corrected.npy'), similarity_map)
    print(f"\n✓ Saved: sierpinski_terrain_fractality_corrected.npy")

    # Visualization
    create_visualization(dem_data, similarity_map, sierpinski_coords, results_dir)

def create_visualization(dem_data, sim_map, sierpinski_coords, results_dir):
    print("\nCreating visualization...")

    hillshade = create_hillshade(dem_data)

    fig = plt.figure(figsize=(20, 10))

    # Panel 1: Hillshade
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(hillshade, cmap='gray', aspect='auto')
    ax1.set_title('DEM Hillshade', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Pixel X')
    ax1.set_ylabel('Pixel Y')

    # Panel 2: Similarity map
    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(sim_map, cmap='hot', aspect='auto', vmin=0)
    ax2.set_title('Sierpinski Terrain Fractality\n(Corrected: Hierarchical Interleaving)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Pixel X')
    ax2.set_ylabel('Pixel Y')
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label('Correlation')

    # Panel 3: Overlay
    ax3 = plt.subplot(2, 3, 3)
    hillshade_norm = (hillshade - hillshade.min()) / (hillshade.max() - hillshade.min())
    overlay_rgb = np.zeros((*dem_data.shape, 3), dtype=float)
    overlay_rgb[:, :, 0] = hillshade_norm
    overlay_rgb[:, :, 1] = hillshade_norm
    overlay_rgb[:, :, 2] = hillshade_norm

    norm = Normalize(vmin=sim_map.min(), vmax=sim_map.max())
    from matplotlib.cm import hot
    colors = hot(norm(sim_map))
    alpha = 0.7
    overlay = (1 - alpha) * overlay_rgb + alpha * colors[:, :, :3]
    ax3.imshow(overlay, aspect='auto')
    ax3.set_title('Similarity on Hillshade\n(Hot = Most Fractal)', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Pixel X')
    ax3.set_ylabel('Pixel Y')

    # Panel 4: Sierpinski space colored by elevation (sampled for visibility)
    ax4 = plt.subplot(2, 3, 4)
    # Sample every 10th point to avoid overplotting
    sample_step = 10
    sample_indices = np.arange(0, len(sierpinski_coords), sample_step)
    scatter = ax4.scatter(sierpinski_coords[sample_indices, 0],
                         sierpinski_coords[sample_indices, 1],
                         c=dem_data.flatten()[sample_indices],
                         s=3, alpha=0.7,
                         cmap='terrain', rasterized=True)
    ax4.set_xlim([sierpinski_coords[:, 0].min() - 0.1, sierpinski_coords[:, 0].max() + 0.1])
    ax4.set_ylim([sierpinski_coords[:, 1].min() - 0.1, sierpinski_coords[:, 1].max() + 0.1])
    ax4.set_title(f'Sierpinski Space\n(Sampled 1/{sample_step}, Colored by Elevation)',
                  fontsize=13, fontweight='bold')
    ax4.set_xlabel('Sierpinski X')
    ax4.set_ylabel('Sierpinski Y')
    ax4.set_aspect('equal')
    cbar4 = plt.colorbar(scatter, ax=ax4)
    cbar4.set_label('Elevation (m)')

    # Panel 5: High similarity regions
    ax5 = plt.subplot(2, 3, 5)
    threshold = np.percentile(sim_map[sim_map > 0], 75) if np.sum(sim_map > 0) > 0 else 0
    high_sim = sim_map > threshold
    ax5.imshow(hillshade, cmap='gray', aspect='auto', alpha=0.7)
    ax5.imshow(np.where(high_sim, sim_map, np.nan), cmap='hot', aspect='auto', alpha=0.8)
    ax5.set_title(f'High Similarity Regions (Top 25%)\nThreshold: {threshold:.4f}', fontsize=13, fontweight='bold')
    ax5.set_xlabel('Pixel X')
    ax5.set_ylabel('Pixel Y')

    # Panel 6: Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    valid = sim_map[sim_map > 0]
    stats_text = f"""SIERPINSKI TERRAIN FRACTALITY (CORRECTED)

Method:
  • Hierarchical ternary digit interleaving
  • Map pixel (i,j) → p-adic integer via
    alternating j and i digit extraction
  • Embed p-adic → sierpinski via
    Chistyakov transformation
  • Compare elevation distributions
    across sierpinski regions

Parameters: p=3, l=6, s=0.5, m=0

Similarity Statistics:
  Min: {valid.min():.4f}
  Max: {valid.max():.4f}
  Mean: {valid.mean():.4f}
  Median: {np.median(valid):.4f}
  Std: {valid.std():.4f}

Interpretation:
  • High correlation = local elevation
    pattern matches global pattern
  • Identifies self-similar terrain
  • "Most fractal" regions replicate
    global sierpinski structure
    """

    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.suptitle('Sierpinski Terrain Fractality Analysis (Corrected)',
                fontsize=15, fontweight='bold')
    plt.tight_layout()

    output_file = results_dir / '13_sierpinski_terrain_fractality_corrected.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    main()
