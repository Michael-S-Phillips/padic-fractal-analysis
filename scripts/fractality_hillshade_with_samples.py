#!/usr/bin/env python3
"""
Overlay fractality on hillshade with example Sierpinski distributions from
peak fractal regions and low fractal regions.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, Normalize
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from pathlib import Path
import sys

sys.path.insert(0, '/Volumes/Fangorn/padic_fractal_analysis/src')

def create_hillshade(dem, azimuth=315, altitude=45):
    """Create hillshade from DEM using light source."""
    ls = LightSource(azdeg=azimuth, altdeg=altitude)
    hillshade = ls.hillshade(dem, vert_exag=0.1)
    return hillshade

def compute_sierpinski_distribution(elevations, p=3, l=6, bins=729):
    """Compute Sierpinski distribution for elevations."""
    if len(elevations) == 0:
        return np.zeros(bins)
    
    e_min, e_max = elevations.min(), elevations.max()
    if e_max == e_min:
        e_norm = np.zeros_like(elevations)
    else:
        e_norm = (elevations - e_min) / (e_max - e_min)
    
    padic_ints = np.round(e_norm * (p**l - 1)).astype(int)
    padic_ints = np.clip(padic_ints, 0, p**l - 1)
    
    hist, _ = np.histogram(padic_ints, bins=np.arange(bins + 1))
    return hist.astype(float)

def main():
    cache_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
    results_dir = Path('/Volumes/Fangorn/padic_fractal_analysis/results')
    
    # Load data
    dem_data = np.load(str(cache_dir / 'dem_clean.npy'))
    fractality_data = np.load(str(cache_dir / 'local_sierpinski_similarity.npy'))
    
    print("=" * 70)
    print("FRACTALITY-HILLSHADE WITH SIERPINSKI SAMPLES")
    print("=" * 70)
    
    # Create hillshade
    hillshade = create_hillshade(dem_data)
    
    # Compute global sierpinski distribution
    print("\nComputing global Sierpinski distribution...")
    global_dist = compute_sierpinski_distribution(dem_data.flatten(), p=3, l=6)
    global_dist_norm = global_dist / global_dist.sum()
    
    # Find example pixels from different fractality levels
    print("Finding example pixels...")
    fractality_flat = fractality_data.flatten()
    
    # Peak fractality pixels
    peak_threshold = np.percentile(fractality_flat[fractality_flat > 0], 95)
    peak_indices = np.where(fractality_flat > peak_threshold)[0]
    
    # Low fractality pixels
    low_threshold = np.percentile(fractality_flat[fractality_flat > 0], 25)
    low_indices = np.where((fractality_flat > 0) & (fractality_flat < low_threshold))[0]
    
    # Select random examples
    np.random.seed(42)
    peak_samples_idx = np.random.choice(peak_indices, size=3, replace=False)
    low_samples_idx = np.random.choice(low_indices, size=1, replace=False)
    
    # Convert to 2D coordinates
    h, w = dem_data.shape
    peak_samples = [(idx // w, idx % w) for idx in peak_samples_idx]
    low_samples = [(idx // w, idx % w) for idx in low_samples_idx]
    
    print(f"  Peak fractality samples (y, x): {peak_samples}")
    print(f"  Low fractality samples (y, x): {low_samples}")
    
    # Compute distributions for samples
    window_size = 27
    half_window = window_size // 2
    
    distributions = {}
    labels = {}
    
    # Global
    distributions['global'] = global_dist_norm
    labels['global'] = f"Global Distribution\n(All {dem_data.size:,} pixels)"
    
    # Peak fractality samples
    for i, (y, x) in enumerate(peak_samples):
        y1 = max(0, y - half_window)
        y2 = min(h, y + half_window + 1)
        x1 = max(0, x - half_window)
        x2 = min(w, x + half_window + 1)
        
        window = dem_data[y1:y2, x1:x2].flatten()
        local_dist = compute_sierpinski_distribution(window, p=3, l=6)
        local_dist_norm = local_dist / (local_dist.sum() + 1e-10)
        
        frac_score = fractality_data[y, x]
        distributions[f'peak_{i}'] = local_dist_norm
        labels[f'peak_{i}'] = f"Peak Fractal #{i+1}\n({y}, {x})\nSim: {frac_score:.4f}"
    
    # Low fractality sample
    y, x = low_samples[0]
    y1 = max(0, y - half_window)
    y2 = min(h, y + half_window + 1)
    x1 = max(0, x - half_window)
    x2 = min(w, x + half_window + 1)
    
    window = dem_data[y1:y2, x1:x2].flatten()
    local_dist = compute_sierpinski_distribution(window, p=3, l=6)
    local_dist_norm = local_dist / (local_dist.sum() + 1e-10)
    
    frac_score = fractality_data[y, x]
    distributions['low'] = local_dist_norm
    labels['low'] = f"Low Fractal\n({y}, {x})\nSim: {frac_score:.4f}"
    
    # Create main visualization with GridSpec
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(2, 6, figure=fig, hspace=0.3, wspace=0.3)
    
    # Panel 1: Hillshade
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(hillshade, cmap='gray', aspect='auto')
    ax1.set_title('DEM Hillshade', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Pixel X', fontsize=10)
    ax1.set_ylabel('Pixel Y', fontsize=10)
    
    # Mark sample locations
    for (y, x) in peak_samples:
        ax1.plot(x, y, 'r+', markersize=15, markeredgewidth=2)
    for (y, x) in low_samples:
        ax1.plot(x, y, 'b+', markersize=15, markeredgewidth=2)
    
    # Panel 2: Fractality only
    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(fractality_data, cmap='hot', aspect='auto')
    ax2.set_title('Fractality Score', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Pixel X', fontsize=10)
    ax2.set_ylabel('Pixel Y', fontsize=10)
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label('Similarity', fontsize=9)
    
    # Mark sample locations
    for (y, x) in peak_samples:
        ax2.plot(x, y, 'r+', markersize=15, markeredgewidth=2)
    for (y, x) in low_samples:
        ax2.plot(x, y, 'b+', markersize=15, markeredgewidth=2)
    
    # Panel 3: Overlay
    ax3 = fig.add_subplot(gs[0, 2])
    hillshade_norm = (hillshade - hillshade.min()) / (hillshade.max() - hillshade.min())
    overlay_rgb = np.zeros((*dem_data.shape, 3), dtype=float)
    overlay_rgb[:, :, 0] = hillshade_norm
    overlay_rgb[:, :, 1] = hillshade_norm
    overlay_rgb[:, :, 2] = hillshade_norm
    
    frac_norm = Normalize(vmin=fractality_data.min(), vmax=fractality_data.max())
    frac_normalized = frac_norm(fractality_data)
    from matplotlib.cm import hot
    frac_colors = hot(frac_normalized)
    
    alpha = 0.7
    overlay_rgb = (1 - alpha) * overlay_rgb[:, :, :3] + alpha * frac_colors[:, :, :3]
    
    ax3.imshow(overlay_rgb, aspect='auto')
    ax3.set_title('Fractality on Hillshade', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Pixel X', fontsize=10)
    ax3.set_ylabel('Pixel Y', fontsize=10)
    
    # Mark sample locations
    for (y, x) in peak_samples:
        ax3.plot(x, y, 'r+', markersize=15, markeredgewidth=2)
    for (y, x) in low_samples:
        ax3.plot(x, y, 'b+', markersize=15, markeredgewidth=2)
    
    # Panels 4-18: 4x4 Sierpinski distributions grid
    gs_samples = GridSpecFromSubplotSpec(4, 4, subplot_spec=gs[:, 3:], 
                                        hspace=0.4, wspace=0.4)
    
    dist_keys = ['global', 'peak_0', 'peak_1', 'peak_2', 'low']
    colors_map = {
        'global': 'black',
        'peak_0': 'red',
        'peak_1': 'darkred',
        'peak_2': 'crimson',
        'low': 'blue'
    }
    
    plot_idx = 0
    for i in range(4):
        for j in range(4):
            ax = fig.add_subplot(gs_samples[i, j])
            
            if plot_idx < len(dist_keys):
                key = dist_keys[plot_idx]
                dist = distributions[key]
                
                ax.bar(np.arange(len(dist)), dist, width=1.0, 
                       color=colors_map[key], alpha=0.7, edgecolor='none')
                
                ax.set_title(labels[key], fontsize=9, fontweight='bold')
                ax.set_ylim(0, dist.max() * 1.1)
            
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            
            plot_idx += 1
    
    plt.suptitle('Local Sierpinski Self-Similarity on DEM Hillshade\nFractality Intensity with Example Sierpinski Distributions (27×27 windows)',
                fontsize=15, fontweight='bold')
    
    output_file = results_dir / '11_fractality_hillshade_with_samples.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()
    
    print("\n✓ Visualization complete!")

if __name__ == '__main__':
    main()
