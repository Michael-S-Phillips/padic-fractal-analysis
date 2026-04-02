#!/usr/bin/env python3
"""
2D Sierpinski Space Fractality Analysis (Sampled Global Distribution)

More practical approach: Sample global distribution (every Nth pixel)
instead of embedding all 2.4M points.
"""

import numpy as np
import matplotlib.pyplot as plt
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
    """Embed elevation values into 2D sierpinski space."""
    e_min, e_max = dem_flat.min(), dem_flat.max()
    e_norm = (elevations_flat - e_min) / (e_max - e_min)
    padic_ints = np.round(e_norm * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)
    
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    embeddings = embed_padic_cloud(padic_ints, p=p, l=l, s=s, m=0)
    return embeddings[:, 0], embeddings[:, 1]

def compute_2d_histogram(x, y, bins=50):
    """Create 2D histogram with normalized probabilities."""
    hist, xedges, yedges = np.histogram2d(x, y, bins=bins, density=False)
    return hist / hist.sum(), xedges, yedges

def js_divergence(p, q):
    """Jensen-Shannon divergence."""
    p = np.asarray(p).flatten()
    q = np.asarray(q).flatten()
    p = np.maximum(p, 1e-10)
    q = np.maximum(q, 1e-10)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return 0.5 * np.sum(rel_entr(p, m)) + 0.5 * np.sum(rel_entr(q, m))

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape
    dem_flat = dem_data.flatten()
    
    print("=" * 70)
    print("2D SIERPINSKI SPATIAL FRACTALITY (SAMPLED)")
    print("=" * 70)
    print(f"DEM shape: {dem_data.shape}")
    
    # Sample global distribution (every 100th pixel for speed)
    print("\nSampling global sierpinski distribution (every 100th pixel)...")
    sample_rate = 100
    sample_indices = np.arange(0, len(dem_flat), sample_rate)
    global_sample = dem_flat[sample_indices]
    
    print(f"  Sampled {len(global_sample):,} pixels from {len(dem_flat):,} total")
    print(f"  Embedding sample into sierpinski space...")
    global_x, global_y = embed_elevations_to_sierpinski(global_sample, dem_flat)
    
    print(f"  Creating global 2D histogram...")
    global_hist, _, _ = compute_2d_histogram(global_x, global_y, bins=50)
    global_flat = global_hist.flatten()
    
    # Initialize output maps
    similarity_map = np.zeros((h, w), dtype=np.float32)
    
    window_size = 27
    half_window = window_size // 2
    
    print(f"\nProcessing {h:,} rows × {w:,} cols...")
    
    # Process every other pixel (for speed)
    step = 2
    count = 0
    for y in range(0, h, step):
        if y % 100 == 0:
            print(f"  Row {y}/{h}...")
        
        for x in range(0, w, step):
            # Extract window
            y1 = max(0, y - half_window)
            y2 = min(h, y + half_window + 1)
            x1 = max(0, x - half_window)
            x2 = min(w, x + half_window + 1)
            
            window = dem_data[y1:y2, x1:x2].flatten()
            
            if len(window) < 9:
                continue
            
            try:
                # Embed local window
                local_x, local_y = embed_elevations_to_sierpinski(window, dem_flat)
                
                if len(local_x) < 3:
                    continue
                
                # Compute local 2D histogram
                local_hist, _, _ = compute_2d_histogram(local_x, local_y, bins=50)
                local_flat = local_hist.flatten()
                
                # Compute JS divergence
                js_div = js_divergence(global_flat, local_flat)
                similarity_map[y, x] = 1.0 / (1.0 + js_div)
                count += 1
                
            except:
                pass
    
    print(f"\n✓ Processed {count:,} pixels")
    
    # Interpolate to full resolution using scipy
    from scipy.ndimage import zoom
    factor = 1.0 / step
    full_map = zoom(similarity_map[::step, ::step], (1/factor, 1/factor), order=1)
    full_map = full_map[:h, :w]
    
    # Statistics
    valid = full_map[full_map > 0]
    if len(valid) > 0:
        print(f"\nSimilarity Statistics:")
        print(f"  Min: {valid.min():.4f}")
        print(f"  Max: {valid.max():.4f}")
        print(f"  Mean: {valid.mean():.4f}")
        print(f"  Median: {np.median(valid):.4f}")
    
    # Save results
    np.save(str(cache_dir / 'sierpinski_2d_js_sampled.npy'), full_map)
    print(f"\n✓ Saved: sierpinski_2d_js_sampled.npy")
    
    # Visualization
    create_visualization(dem_data, full_map, global_x, global_y, results_dir)

def create_visualization(dem_data, sim_map, global_x, global_y, results_dir):
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
    ax2.set_title('2D Sierpinski Similarity\n(Jensen-Shannon Divergence)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Pixel X')
    ax2.set_ylabel('Pixel Y')
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label('Similarity')
    
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
    
    # Panel 4: Global sierpinski distribution
    ax4 = plt.subplot(2, 3, 4)
    ax4.scatter(global_x, global_y, s=2, alpha=0.4, c='black', rasterized=True)
    ax4.set_xlim(global_x.min() - 0.05, global_x.max() + 0.05)
    ax4.set_ylim(global_y.min() - 0.05, global_y.max() + 0.05)
    ax4.set_title(f'Global Sierpinski Distribution\n(Sampled: {len(global_x):,} pixels)', 
                 fontsize=13, fontweight='bold')
    ax4.set_xlabel('Sierpinski X')
    ax4.set_ylabel('Sierpinski Y')
    ax4.set_aspect('equal')
    
    # Panel 5: High similarity regions
    ax5 = plt.subplot(2, 3, 5)
    threshold = np.percentile(sim_map[sim_map > 0], 75)
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
    stats_text = f"""2D SIERPINSKI SPATIAL FRACTALITY

Method: Sampled Global Distribution
  Global sample: Every 100th pixel
  Local windows: 27×27 pixels
  Per-pixel step: Every 2nd pixel
  
Similarity Metrics:
  Metric: Jensen-Shannon Divergence
  Range: {valid.min():.4f} to {valid.max():.4f}
  Mean: {valid.mean():.4f}
  Median: {np.median(valid):.4f}
  Std: {valid.std():.4f}

Interpretation:
  • Higher similarity = local elevation
    pattern matches global structure
  • Identifies "most fractal" regions
  • Bright = local pattern replicates
    the global sierpinski distribution
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('2D Sierpinski Spatial Fractality: Geometric Structure Comparison',
                fontsize=15, fontweight='bold')
    plt.tight_layout()
    
    output_file = results_dir / '12_sierpinski_2d_spatial_fractality.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    main()
