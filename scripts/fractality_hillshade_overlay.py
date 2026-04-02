#!/usr/bin/env python3
"""
Overlay local Sierpinski self-similarity on DEM hillshade for geological context.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, Normalize
from pathlib import Path

def create_hillshade(dem, azimuth=315, altitude=45):
    """Create hillshade from DEM using light source."""
    ls = LightSource(azdeg=azimuth, altdeg=altitude)
    hillshade = ls.hillshade(dem, vert_exag=0.1)
    return hillshade

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    
    # Load data
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    fractality_data = np.load(str(cache_dir / 'local_sierpinski_similarity.npy'))
    
    print("=" * 70)
    print("FRACTALITY-HILLSHADE OVERLAY VISUALIZATION")
    print("=" * 70)
    print(f"\nLoading data...")
    print(f"  DEM shape: {dem_data.shape}")
    print(f"  Fractality shape: {fractality_data.shape}")
    
    # Create hillshade
    print(f"\nGenerating hillshade...")
    hillshade = create_hillshade(dem_data)
    
    # Create visualization
    fig = plt.figure(figsize=(20, 12))
    
    # Panel 1: Hillshade only
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(hillshade, cmap='gray', aspect='auto')
    ax1.set_title('DEM Hillshade\n(Topographic Context)', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Pixel X')
    ax1.set_ylabel('Pixel Y')
    
    # Panel 2: Fractality only
    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(fractality_data, cmap='hot', aspect='auto')
    ax2.set_title('Local Sierpinski Self-Similarity\n(Fractality Score)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Pixel X')
    ax2.set_ylabel('Pixel Y')
    cbar2 = plt.colorbar(im2, ax=ax2)
    cbar2.set_label('Similarity Score')
    
    # Panel 3: Hillshade + fractality overlay (colored)
    ax3 = plt.subplot(2, 3, 3)
    # Normalize hillshade to 0-1
    hillshade_norm = (hillshade - hillshade.min()) / (hillshade.max() - hillshade.min())
    # Create RGB image: use hillshade for intensity, fractality for color
    overlay_rgb = np.zeros((*dem_data.shape, 3), dtype=float)
    overlay_rgb[:, :, 0] = hillshade_norm  # Red channel = hillshade
    overlay_rgb[:, :, 1] = hillshade_norm  # Green channel = hillshade
    overlay_rgb[:, :, 2] = hillshade_norm  # Blue channel = hillshade
    
    # Overlay fractality as a warm color (red-yellow) on top
    frac_norm = Normalize(vmin=fractality_data.min(), vmax=fractality_data.max())
    frac_normalized = frac_norm(fractality_data)
    
    # Use hot colormap for fractality
    from matplotlib.cm import hot
    frac_colors = hot(frac_normalized)
    
    # Blend: darken hillshade by fractality intensity
    alpha = 0.7
    overlay_rgb = (1 - alpha) * overlay_rgb[:, :, :3] + alpha * frac_colors[:, :, :3]
    
    ax3.imshow(overlay_rgb, aspect='auto')
    ax3.set_title('Fractality Overlay on Hillshade\n(Hot = Most Fractal)', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Pixel X')
    ax3.set_ylabel('Pixel Y')
    
    # Panel 4: High fractality regions only
    ax4 = plt.subplot(2, 3, 4)
    threshold = np.percentile(fractality_data[fractality_data > 0], 75)
    high_frac = fractality_data > threshold
    ax4.imshow(hillshade, cmap='gray', aspect='auto', alpha=0.7)
    ax4.imshow(np.where(high_frac, fractality_data, np.nan), cmap='hot', aspect='auto', alpha=0.8)
    ax4.set_title(f'High Fractality Regions (Top 25%)\nThreshold: {threshold:.4f}', 
                  fontsize=13, fontweight='bold')
    ax4.set_xlabel('Pixel X')
    ax4.set_ylabel('Pixel Y')
    
    # Panel 5: Very high fractality (top 5%)
    ax5 = plt.subplot(2, 3, 5)
    very_high_threshold = np.percentile(fractality_data[fractality_data > 0], 95)
    very_high_frac = fractality_data > very_high_threshold
    ax5.imshow(hillshade, cmap='gray', aspect='auto', alpha=0.7)
    ax5.imshow(np.where(very_high_frac, fractality_data, np.nan), cmap='hot', aspect='auto', alpha=0.9)
    ax5.set_title(f'Peak Fractality Regions (Top 5%)\nThreshold: {very_high_threshold:.4f}', 
                  fontsize=13, fontweight='bold')
    ax5.set_xlabel('Pixel X')
    ax5.set_ylabel('Pixel Y')
    
    # Panel 6: Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    valid_pixels = fractality_data > 0
    stats_text = f"""
FRACTALITY-HILLSHADE ANALYSIS

Data Summary:
  Total pixels: {fractality_data.size:,}
  Valid pixels: {valid_pixels.sum():,}
  
Similarity Statistics:
  Min: {fractality_data[valid_pixels].min():.6f}
  Max: {fractality_data[valid_pixels].max():.6f}
  Mean: {fractality_data[valid_pixels].mean():.6f}
  Median: {np.median(fractality_data[valid_pixels]):.6f}
  Std Dev: {fractality_data[valid_pixels].std():.6f}

Percentile Regions:
  Top 25% threshold: {threshold:.6f}
  Top 5% threshold: {very_high_threshold:.6f}
  
Peak Region Count:
  Pixels > 75th percentile: {(fractality_data > threshold).sum():,}
  Pixels > 95th percentile: {(fractality_data > very_high_threshold).sum():,}
  
Interpretation:
  • Bright areas = most fractal
  • Aligned with hillshade = geological structure
  • Clustered = scale-dependent structure
    """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
             fontsize=11, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('Local Sierpinski Self-Similarity on DEM Hillshade\nFractality Intensity Overlaid on Topography',
                fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_file = results_dir / '11_fractality_hillshade_overlay.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()
    
    # Create a high-quality single-panel version for presentations
    fig, ax = plt.subplots(figsize=(16, 14))
    
    ax.imshow(overlay_rgb, aspect='auto')
    ax.set_title('Local Sierpinski Self-Similarity Overlaid on Terrain\n(Bright Colors = Most Fractal)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Pixel X', fontsize=13)
    ax.set_ylabel('Pixel Y', fontsize=13)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=hot, norm=frac_norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Similarity to Global Sierpinski Pattern', fontsize=12)
    
    plt.tight_layout()
    output_file2 = results_dir / '11_fractality_hillshade_single.png'
    plt.savefig(output_file2, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file2}")
    plt.close()
    
    print("\n✓ Visualization complete!")

if __name__ == '__main__':
    main()
