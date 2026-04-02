#!/usr/bin/env python3
"""
2D Sierpinski Space Fractality Analysis (Optimized)

Compares geometric structure of elevation distributions in sierpinski space.
Uses caching to speed up the computation significantly.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import entropy
from scipy.special import rel_entr
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

def embed_elevations_to_sierpinski(elevations_flat, dem_flat, p=3, l=6):
    """
    Embed elevation values into 2D sierpinski space.
    Returns (x, y) coordinates in sierpinski plane.
    """
    # Normalize elevations
    e_min, e_max = dem_flat.min(), dem_flat.max()
    e_norm = (elevations_flat - e_min) / (e_max - e_min)
    
    # Convert to p-adic integers
    padic_ints = np.round(e_norm * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)
    
    # Embed in sierpinski space
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)
    
    return embeddings[:, 0], embeddings[:, 1]

def compute_2d_histogram(x, y, bins=50):
    """Create 2D histogram with normalized probabilities."""
    hist, xedges, yedges = np.histogram2d(x, y, bins=bins, density=False)
    hist_norm = hist / hist.sum()
    return hist_norm, xedges, yedges

def js_divergence(p, q):
    """Jensen-Shannon divergence between two probability distributions."""
    p = np.asarray(p).flatten()
    q = np.asarray(q).flatten()
    
    # Handle zeros
    p = np.maximum(p, 1e-10)
    q = np.maximum(q, 1e-10)
    p = p / p.sum()
    q = q / q.sum()
    
    m = 0.5 * (p + q)
    return 0.5 * np.sum(rel_entr(p, m)) + 0.5 * np.sum(rel_entr(q, m))

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    
    # Load DEM
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape
    dem_flat = dem_data.flatten()
    
    print("=" * 70)
    print("2D SIERPINSKI SPATIAL FRACTALITY ANALYSIS (OPTIMIZED)")
    print("=" * 70)
    print(f"\nDEM shape: {dem_data.shape}")
    print(f"Total pixels: {len(dem_flat):,}")
    
    # Check if global embedding is cached
    global_embedding_file = cache_dir / 'sierpinski_2d_global_embedding.npz'
    
    if global_embedding_file.exists():
        print("\nLoading cached global sierpinski embedding...")
        cached = np.load(str(global_embedding_file))
        global_x = cached['x']
        global_y = cached['y']
        global_hist = cached['hist']
        print(f"  Loaded {len(global_x):,} global points")
    else:
        print("\nComputing and caching global sierpinski embedding...")
        global_x, global_y = embed_elevations_to_sierpinski(dem_flat, dem_flat)
        print(f"  Global range: X=[{global_x.min():.3f}, {global_x.max():.3f}], Y=[{global_y.min():.3f}, {global_y.max():.3f}]")
        
        print("  Creating global 2D histogram...")
        global_hist, _, _ = compute_2d_histogram(global_x, global_y, bins=60)
        
        # Cache for future use
        np.savez(str(global_embedding_file), x=global_x, y=global_y, hist=global_hist)
        print(f"  Cached to {global_embedding_file.name}")
    
    # Initialize output maps
    similarity_map_hist = np.zeros((h, w), dtype=np.float32)
    similarity_map_js = np.zeros((h, w), dtype=np.float32)
    
    window_size = 27
    half_window = window_size // 2
    global_flat = global_hist.flatten()
    
    print(f"\nProcessing {h:,} rows × {w:,} cols with {window_size}×{window_size} windows...")
    
    # Process each pixel
    for y in range(h):
        if y % 50 == 0:
            print(f"  Row {y}/{h}...")
        
        for x in range(w):
            # Extract window
            y1 = max(0, y - half_window)
            y2 = min(h, y + half_window + 1)
            x1 = max(0, x - half_window)
            x2 = min(w, x + half_window + 1)
            
            window = dem_data[y1:y2, x1:x2].flatten()
            
            if len(window) < 9:  # Too close to edge
                continue
            
            # Embed local window in sierpinski space
            local_x, local_y = embed_elevations_to_sierpinski(window, dem_flat)
            
            if len(local_x) < 3:  # Not enough points
                continue
            
            # Compute local 2D histogram
            local_hist, _, _ = compute_2d_histogram(local_x, local_y, bins=60)
            local_flat = local_hist.flatten()
            
            # Method 1: 2D Histogram Correlation (Pearson)
            try:
                corr = np.corrcoef(global_flat, local_flat)[0, 1]
                similarity_map_hist[y, x] = max(0, corr if not np.isnan(corr) else 0)
            except:
                similarity_map_hist[y, x] = 0
            
            # Method 2: Jensen-Shannon Divergence
            js_div = js_divergence(global_flat, local_flat)
            similarity_map_js[y, x] = 1.0 / (1.0 + js_div)
    
    print(f"\n✓ Analysis complete!")
    
    # Statistics
    print(f"\n2D Histogram Correlation Statistics:")
    valid_hist = similarity_map_hist[similarity_map_hist > 0]
    if len(valid_hist) > 0:
        print(f"  Min: {valid_hist.min():.4f}")
        print(f"  Max: {valid_hist.max():.4f}")
        print(f"  Mean: {valid_hist.mean():.4f}")
        print(f"  Median: {np.median(valid_hist):.4f}")
        print(f"  Std: {valid_hist.std():.4f}")
    
    print(f"\nJensen-Shannon Divergence Statistics:")
    valid_js = similarity_map_js[similarity_map_js > 0]
    if len(valid_js) > 0:
        print(f"  Min: {valid_js.min():.4f}")
        print(f"  Max: {valid_js.max():.4f}")
        print(f"  Mean: {valid_js.mean():.4f}")
        print(f"  Median: {np.median(valid_js):.4f}")
        print(f"  Std: {valid_js.std():.4f}")
    
    # Save results
    np.save(str(cache_dir / 'sierpinski_2d_histogram_correlation.npy'), similarity_map_hist)
    np.save(str(cache_dir / 'sierpinski_2d_js_divergence.npy'), similarity_map_js)
    print(f"\n✓ Saved: sierpinski_2d_histogram_correlation.npy")
    print(f"✓ Saved: sierpinski_2d_js_divergence.npy")
    
    # Create visualization
    create_visualization(dem_data, similarity_map_hist, similarity_map_js, 
                       global_x, global_y, results_dir)

def create_visualization(dem_data, sim_hist, sim_js, global_x, global_y, results_dir):
    """Create comparison visualization."""
    
    print("\nCreating visualization...")
    
    hillshade = create_hillshade(dem_data)
    
    fig = plt.figure(figsize=(20, 10))
    
    # Panel 1: Hillshade
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(hillshade, cmap='gray', aspect='auto')
    ax1.set_title('DEM Hillshade', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Pixel X')
    ax1.set_ylabel('Pixel Y')
    
    # Panel 2: Histogram Correlation
    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(sim_hist, cmap='hot', aspect='auto', vmin=0)
    ax2.set_title('2D Histogram Correlation\n(Pearson r)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Pixel X')
    ax2.set_ylabel('Pixel Y')
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label('Correlation')
    
    # Panel 3: JS Divergence
    ax3 = plt.subplot(2, 3, 3)
    im3 = ax3.imshow(sim_js, cmap='hot', aspect='auto', vmin=0)
    ax3.set_title('JS Divergence Similarity\n(1/(1+divergence))', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Pixel X')
    ax3.set_ylabel('Pixel Y')
    cbar3 = plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    cbar3.set_label('Similarity')
    
    # Panel 4: Global sierpinski distribution
    ax4 = plt.subplot(2, 3, 4)
    ax4.scatter(global_x, global_y, s=1, alpha=0.3, c='black', rasterized=True)
    ax4.set_xlim(global_x.min() - 0.05, global_x.max() + 0.05)
    ax4.set_ylim(global_y.min() - 0.05, global_y.max() + 0.05)
    ax4.set_title(f'Global Sierpinski Distribution\n({len(global_x):,} pixels)', 
                 fontsize=13, fontweight='bold')
    ax4.set_xlabel('Sierpinski X')
    ax4.set_ylabel('Sierpinski Y')
    ax4.set_aspect('equal')
    
    # Panel 5: Combined comparison
    ax5 = plt.subplot(2, 3, 5)
    hillshade_norm = (hillshade - hillshade.min()) / (hillshade.max() - hillshade.min())
    overlay_rgb = np.zeros((*dem_data.shape, 3), dtype=float)
    overlay_rgb[:, :, 0] = hillshade_norm
    overlay_rgb[:, :, 1] = hillshade_norm
    overlay_rgb[:, :, 2] = hillshade_norm
    
    # Use JS divergence for overlay
    js_norm = Normalize(vmin=sim_js.min(), vmax=sim_js.max())
    js_normalized = js_norm(sim_js)
    from matplotlib.cm import hot
    js_colors = hot(js_normalized)
    
    alpha = 0.7
    overlay_rgb = (1 - alpha) * overlay_rgb[:, :, :3] + alpha * js_colors[:, :, :3]
    ax5.imshow(overlay_rgb, aspect='auto')
    ax5.set_title('JS Similarity on Hillshade\n(Hot = Most Fractal)', fontsize=13, fontweight='bold')
    ax5.set_xlabel('Pixel X')
    ax5.set_ylabel('Pixel Y')
    
    # Panel 6: Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    valid_hist = sim_hist[sim_hist > 0]
    valid_js = sim_js[sim_js > 0]
    
    if len(valid_hist) > 0:
        hist_min, hist_max, hist_mean, hist_median, hist_std = valid_hist.min(), valid_hist.max(), valid_hist.mean(), np.median(valid_hist), valid_hist.std()
    else:
        hist_min = hist_max = hist_mean = hist_median = hist_std = 0
        
    if len(valid_js) > 0:
        js_min, js_max, js_mean, js_median, js_std = valid_js.min(), valid_js.max(), valid_js.mean(), np.median(valid_js), valid_js.std()
    else:
        js_min = js_max = js_mean = js_median = js_std = 0
    
    stats_text = f"""2D SIERPINSKI SPATIAL FRACTALITY

Histogram Correlation (Pearson r):
  Range: {hist_min:.4f} to {hist_max:.4f}
  Mean: {hist_mean:.4f}
  Median: {hist_median:.4f}
  Std: {hist_std:.4f}

Jensen-Shannon Divergence:
  Range: {js_min:.4f} to {js_max:.4f}
  Mean: {js_mean:.4f}
  Median: {js_median:.4f}
  Std: {js_std:.4f}

Method: 27×27 sliding windows
Embedding in sierpinski space,
comparing 2D distributions
using correlation + JS divergence.
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('2D Sierpinski Spatial Fractality: Local vs Global Structure',
                fontsize=15, fontweight='bold')
    plt.tight_layout()
    
    output_file = results_dir / '12_sierpinski_2d_spatial_fractality.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    main()
