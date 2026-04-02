#!/usr/bin/env python3
"""
Generate per-pixel fractal complexity maps using p-adic embeddings.

Creates full-resolution maps showing terrain complexity, hierarchical levels,
and clustering tendency at each pixel location.
"""

import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')
from padic.padic_embedding import embed_padic_cloud, get_paper_s

def extract_local_window(dem, x, y, window_size=5):
    """Extract normalized elevation window around pixel (x, y)."""
    h, w = dem.shape
    half = window_size // 2

    # Boundaries with padding
    y1 = max(0, y - half)
    y2 = min(h, y + half + 1)
    x1 = max(0, x - half)
    x2 = min(w, x + half + 1)

    window = dem[y1:y2, x1:x2].flatten()

    if len(window) == 0:
        return None

    # Normalize to [0, 1]
    wmin, wmax = window.min(), window.max()
    if wmax == wmin:
        window_norm = np.zeros_like(window)
    else:
        window_norm = (window - wmin) / (wmax - wmin)

    return window_norm

def compute_local_fractal_metrics(window_norm, p=3, l=3):
    """
    Compute fractal metrics for a local elevation window.

    Returns:
        complexity: Shannon entropy of elevation distribution
        clustering: Density coefficient of variation
        mean_distance: Mean pairwise distance in neighborhood
    """
    if window_norm is None or len(window_norm) < 2:
        return 0.0, 0.0, 0.0

    # Convert to p-adic integers
    padic_ints = np.round(window_norm * (3**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, 3**l - 1)

    # Get embeddings
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    try:
        embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)
    except:
        return 0.0, 0.0, 0.0

    # Compute complexity (entropy)
    hist, _ = np.histogram(window_norm, bins=5)
    hist = hist[hist > 0]
    if len(hist) == 0:
        entropy = 0.0
    else:
        hist_norm = hist / hist.sum()
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))

    # Compute clustering (density CV)
    distances_from_origin = np.sqrt(embeddings[:, 0]**2 + embeddings[:, 1]**2)
    if len(distances_from_origin) > 1:
        density_cv = np.std(distances_from_origin) / (np.mean(distances_from_origin) + 1e-6)
    else:
        density_cv = 0.0

    # Mean pairwise distance
    if len(embeddings) > 1:
        dists = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                d = np.sqrt(np.sum((embeddings[i] - embeddings[j])**2))
                dists.append(d)
        mean_dist = np.mean(dists) if dists else 0.0
    else:
        mean_dist = 0.0

    return entropy, density_cv, mean_dist

def generate_perpixel_maps(dem_path, output_dir, window_sizes=[3, 5, 7], l=3):
    """Generate per-pixel complexity maps at multiple scales."""

    print(f"📍 Generating per-pixel fractal maps")
    print(f"   DEM: {dem_path}")
    print(f"   Window sizes: {window_sizes}")
    print(f"   P-adic level: {l}")

    # Load DEM
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))

    h, w = dem_data.shape
    print(f"\n   Processing {h} × {w} = {h*w:,} pixels")

    results = {}

    for window_size in window_sizes:
        print(f"\n⚙️  Window size: {window_size}×{window_size}")

        complexity_map = np.zeros((h, w))
        clustering_map = np.zeros((h, w))
        distance_map = np.zeros((h, w))

        # Process each pixel
        for y in range(h):
            if y % 100 == 0:
                print(f"   Row {y}/{h}")

            for x in range(w):
                window = extract_local_window(dem_data, x, y, window_size)
                entropy, cv, mean_dist = compute_local_fractal_metrics(window, p=3, l=l)

                complexity_map[y, x] = entropy
                clustering_map[y, x] = cv
                distance_map[y, x] = mean_dist

        results[window_size] = {
            'complexity': complexity_map,
            'clustering': clustering_map,
            'distance': distance_map
        }

        # Save
        np.save(str(output_dir / f'perpixel_complexity_w{window_size}.npy'), complexity_map)
        np.save(str(output_dir / f'perpixel_clustering_w{window_size}.npy'), clustering_map)
        np.save(str(output_dir / f'perpixel_distance_w{window_size}.npy'), distance_map)

        print(f"   ✓ Complexity: min={complexity_map.min():.3f}, max={complexity_map.max():.3f}, mean={complexity_map.mean():.3f}")
        print(f"   ✓ Clustering: min={clustering_map.min():.3f}, max={clustering_map.max():.3f}, mean={clustering_map.mean():.3f}")

    return results

if __name__ == '__main__':
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    output_dir = cache_dir / 'perpixel'
    output_dir.mkdir(exist_ok=True)

    dem_path = '/Volumes/Fangorn/padic_fractal_analysis/data/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif'

    results = generate_perpixel_maps(dem_path, output_dir, window_sizes=[3, 5, 7], l=3)

    print(f"\n✓ Per-pixel maps generated in {output_dir.name}/")
