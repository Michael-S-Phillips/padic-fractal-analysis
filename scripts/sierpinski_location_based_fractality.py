#!/usr/bin/env python3
"""
2D Sierpinski Spatial Fractality Analysis (Location-Based)

Correctly maps pixel locations (i,j) to sierpinski coordinates, 
then analyzes elevation distributions at those locations.

Key insight: 
- Pixel location (i,j) → sierpinski coordinate (deterministic mapping)
- Elevation value at (i,j) → what we analyze at that sierpinski location
- For fractality: compare elevation distributions across sierpinski regions
  between local window and global image
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

def embed_pixel_coords_to_sierpinski(pixel_coords_2d, p=3, l=6):
    """
    Embed pixel coordinates into sierpinski space independently.

    Embeds X and Y coordinates separately to create a true 2D sierpinski space,
    avoiding any dimensional reduction artifacts like the "jail bar" stripes.

    pixel_coords_2d: (N, 2) array of [y, x] coordinates
    Returns: sierpinski (x_sier, y_sier) coordinates for each pixel
    """
    h_max = pixel_coords_2d[:, 0].max() + 1
    w_max = pixel_coords_2d[:, 1].max() + 1

    # Normalize coordinates to [0, 1]
    y_norm = pixel_coords_2d[:, 0] / h_max
    x_norm = pixel_coords_2d[:, 1] / w_max

    # Convert to p-adic integers for both dimensions
    y_padic = np.round(y_norm * (p**l - 1)).astype(int)
    x_padic = np.round(x_norm * (p**l - 1)).astype(int)

    # Embed X and Y independently into sierpinski space
    s = get_paper_s("sierpinski_carpet", p=p, corrected=True)
    x_embeddings = embed_padic_cloud(x_padic, p=p, l=l, s=s, m=0)
    y_embeddings = embed_padic_cloud(y_padic, p=p, l=l, s=s, m=0)

    # Use first dimension of each embedding as coordinates in 2D sierpinski space
    return x_embeddings[:, 0], y_embeddings[:, 0]

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    h, w = dem_data.shape
    
    print("=" * 70)
    print("2D SIERPINSKI SPATIAL FRACTALITY (LOCATION-BASED)")
    print("=" * 70)
    print(f"DEM shape: {dem_data.shape}")
    
    # Step 1: Generate all pixel coordinates and embed into sierpinski space
    print("\nEmbedding ALL pixel coordinates into sierpinski space...")
    y_coords, x_coords = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    pixel_coords = np.column_stack([y_coords.flatten(), x_coords.flatten()])
    
    global_sierpinski_x, global_sierpinski_y = embed_pixel_coords_to_sierpinski(pixel_coords)
    
    print(f"  Sierpinski X range: [{global_sierpinski_x.min():.3f}, {global_sierpinski_x.max():.3f}]")
    print(f"  Sierpinski Y range: [{global_sierpinski_y.min():.3f}, {global_sierpinski_y.max():.3f}]")
    
    # Step 2: Build global reference: elevation distribution across sierpinski space
    print("\nBuilding global elevation distribution across sierpinski regions...")
    dem_flat = dem_data.flatten()
    
    # Create 2D histogram: elevation values distributed across sierpinski regions
    global_hist, x_edges, y_edges = np.histogram2d(
        global_sierpinski_x, 
        global_sierpinski_y,
        bins=50,
        weights=dem_flat
    )
    global_counts, _, _ = np.histogram2d(
        global_sierpinski_x,
        global_sierpinski_y,
        bins=50
    )
    
    # Average elevation per sierpinski bin
    global_elev_avg = np.divide(global_hist, global_counts, where=global_counts>0, out=np.zeros_like(global_hist))
    
    print(f"  Global elevation histogram shape: {global_elev_avg.shape}")
    print(f"  Non-empty sierpinski regions: {np.sum(global_counts > 0)}")
    
    # Initialize output map
    similarity_map = np.zeros((h, w), dtype=np.float32)
    
    window_size = 27
    half_window = window_size // 2
    
    print(f"\nProcessing {h:,} rows × {w:,} cols with {window_size}×{window_size} windows...")
    
    # Step 3: For each pixel, analyze its local window
    for y in range(h):
        if y % 100 == 0:
            print(f"  Row {y}/{h}...")
        
        for x in range(w):
            # Extract window bounds
            y1 = max(0, y - half_window)
            y2 = min(h, y + half_window + 1)
            x1 = max(0, x - half_window)
            x2 = min(w, x + half_window + 1)
            
            # Get window pixel coordinates
            window_y, window_x = np.meshgrid(np.arange(y1, y2), np.arange(x1, x2), indexing='ij')
            window_coords = np.column_stack([window_y.flatten(), window_x.flatten()])
            window_indices = window_y.flatten() * w + window_x.flatten()
            
            if len(window_indices) < 9:
                continue
            
            # Get sierpinski coordinates for this window
            window_sierpinski_x = global_sierpinski_x[window_indices]
            window_sierpinski_y = global_sierpinski_y[window_indices]
            window_elevations = dem_flat[window_indices]
            
            # Create local elevation histogram in sierpinski space
            local_hist, _, _ = np.histogram2d(
                window_sierpinski_x,
                window_sierpinski_y,
                bins=50,
                weights=window_elevations
            )
            local_counts, _, _ = np.histogram2d(
                window_sierpinski_x,
                window_sierpinski_y,
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
    np.save(str(cache_dir / 'sierpinski_location_based_fractality.npy'), similarity_map)
    print(f"\n✓ Saved: sierpinski_location_based_fractality.npy")
    
    # Visualization
    create_visualization(dem_data, similarity_map, global_sierpinski_x, global_sierpinski_y, results_dir)

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
    ax2.set_title('Sierpinski Location-Based Similarity\n(Elevation Distribution Match)', fontsize=13, fontweight='bold')
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
    # Sample every 10th pixel to avoid overplotting
    sample_step = 10
    sample_indices = np.arange(0, len(global_x), sample_step)
    scatter = ax4.scatter(global_x[sample_indices], global_y[sample_indices],
                         c=dem_data.flatten()[sample_indices], s=3, alpha=0.7,
                         cmap='terrain', rasterized=True)
    ax4.set_xlim(global_x.min() - 0.05, global_x.max() + 0.05)
    ax4.set_ylim(global_y.min() - 0.05, global_y.max() + 0.05)
    ax4.set_title(f'Pixels in Sierpinski Space\n(Sampled 1/{sample_step}, Colored by Elevation)',
                  fontsize=13, fontweight='bold')
    ax4.set_xlabel('Sierpinski X (from pixel X)')
    ax4.set_ylabel('Sierpinski Y (from pixel Y)')
    ax4.set_aspect('equal')
    cbar4 = plt.colorbar(scatter, ax=ax4)
    cbar4.set_label('Elevation (m)')
    
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
    stats_text = f"""2D SIERPINSKI LOCATION-BASED ANALYSIS

Method:
  • Embed pixel locations (i,j) → sierpinski
  • Build elevation distribution across
    sierpinski regions (GLOBALLY)
  • For each 27×27 window, compare its
    elevation distribution across sierpinski
    to the global pattern
  
Similarity Statistics:
  Min: {valid.min():.4f}
  Max: {valid.max():.4f}
  Mean: {valid.mean():.4f}
  Median: {np.median(valid):.4f}
  Std: {valid.std():.4f}

Interpretation:
  • High correlation = local window's
    elevation pattern across sierpinski
    locations matches global pattern
  • "Most fractal" regions replicate
    global elevation structure
  • Identifies self-similar areas
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('2D Sierpinski Spatial Fractality: Location-Based Elevation Distribution Analysis',
                fontsize=15, fontweight='bold')
    plt.tight_layout()
    
    output_file = results_dir / '12_sierpinski_location_based_fractality.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    main()
