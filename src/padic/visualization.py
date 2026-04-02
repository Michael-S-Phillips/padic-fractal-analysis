"""
Visualization and output utilities for fractal density analysis results.

Provides functions for creating publication-quality visualizations and
exporting results to GeoTIFF and other standard formats.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
import rasterio
from rasterio.transform import Affine
from typing import Optional, Tuple, Dict, List
import warnings

warnings.filterwarnings('ignore')


class FractalDensityVisualizer:
    """
    Create visualizations of fractal density analysis results.
    """

    @staticmethod
    def plot_density_map(density: np.ndarray, title: str = "Fractal Density",
                         cmap: str = 'hot', figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """
        Create a publication-quality density map visualization.

        Parameters
        ----------
        density : np.ndarray
            Fractal density map
        title : str
            Plot title
        cmap : str
            Colormap name
        figsize : Tuple[int, int]
            Figure size in inches

        Returns
        -------
        fig : plt.Figure
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Normalize density to 0-1 range for better contrast
        valid_mask = np.isfinite(density)
        vmin = np.percentile(density[valid_mask], 2)
        vmax = np.percentile(density[valid_mask], 98)

        im = ax.imshow(density, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='bilinear')

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Fractal Density', fontsize=12)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_multi_scale(pyramid_levels: List[np.ndarray], titles: Optional[List[str]] = None,
                        figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
        """
        Visualize pyramid levels at multiple scales.

        Parameters
        ----------
        pyramid_levels : List[np.ndarray]
            List of pyramid level arrays
        titles : List[str], optional
            Titles for each level
        figsize : Tuple[int, int]
            Figure size in inches

        Returns
        -------
        fig : plt.Figure
            Matplotlib figure object
        """
        num_levels = len(pyramid_levels)
        ncols = 3
        nrows = (num_levels + ncols - 1) // ncols

        fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
        axes = axes.flatten()

        for i, level in enumerate(pyramid_levels):
            ax = axes[i]

            im = ax.imshow(level, cmap='viridis', interpolation='nearest')
            ax.set_title(titles[i] if titles else f'Level {i}', fontsize=10)
            ax.axis('off')

            plt.colorbar(im, ax=ax)

        # Hide unused subplots
        for i in range(num_levels, len(axes)):
            axes[i].axis('off')

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_histogram(density: np.ndarray, title: str = "Fractal Density Distribution",
                      figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create histogram of fractal density values.

        Parameters
        ----------
        density : np.ndarray
            Fractal density map
        title : str
            Plot title
        figsize : Tuple[int, int]
            Figure size in inches

        Returns
        -------
        fig : plt.Figure
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=figsize)

        valid_data = density[np.isfinite(density)].flatten()

        ax.hist(valid_data, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Fractal Density', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add statistics
        mean_val = np.mean(valid_data)
        std_val = np.std(valid_data)
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
        ax.axvline(mean_val + std_val, color='orange', linestyle=':', linewidth=2, label=f'±σ')
        ax.axvline(mean_val - std_val, color='orange', linestyle=':', linewidth=2)

        ax.legend()
        plt.tight_layout()
        return fig

    @staticmethod
    def plot_dem_with_density_overlay(dem: np.ndarray, density: np.ndarray,
                                     figsize: Tuple[int, int] = (14, 6)) -> plt.Figure:
        """
        Display DEM with fractal density overlay.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        density : np.ndarray
            Fractal density map
        figsize : Tuple[int, int]
            Figure size in inches

        Returns
        -------
        fig : plt.Figure
            Matplotlib figure object
        """
        fig = plt.figure(figsize=figsize)
        gs = GridSpec(1, 2, figure=fig)

        # DEM subplot
        ax1 = fig.add_subplot(gs[0, 0])
        valid_mask = np.isfinite(dem)
        dem_vmin = np.percentile(dem[valid_mask], 2)
        dem_vmax = np.percentile(dem[valid_mask], 98)

        im1 = ax1.imshow(dem, cmap='gray', vmin=dem_vmin, vmax=dem_vmax)
        ax1.set_title('Digital Elevation Model', fontsize=12, fontweight='bold')
        ax1.axis('off')
        plt.colorbar(im1, ax=ax1, label='Elevation')

        # Density overlay subplot
        ax2 = fig.add_subplot(gs[0, 1])
        valid_mask_dens = np.isfinite(density)
        dens_vmin = np.percentile(density[valid_mask_dens], 2)
        dens_vmax = np.percentile(density[valid_mask_dens], 98)

        im2 = ax2.imshow(density, cmap='hot', vmin=dens_vmin, vmax=dens_vmax)
        ax2.set_title('Fractal Density', fontsize=12, fontweight='bold')
        ax2.axis('off')
        plt.colorbar(im2, ax=ax2, label='Density')

        plt.tight_layout()
        return fig

    @staticmethod
    def save_figure(fig: plt.Figure, filepath: str, dpi: int = 150,
                   bbox_inches: str = 'tight') -> None:
        """
        Save figure to file.

        Parameters
        ----------
        fig : plt.Figure
            Matplotlib figure object
        filepath : str
            Output file path
        dpi : int
            Resolution in dots per inch
        bbox_inches : str
            Bounding box setting ('tight' removes extra whitespace)
        """
        fig.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
        plt.close(fig)


class GeoTIFFExporter:
    """
    Export fractal density and other results to GeoTIFF format.
    """

    @staticmethod
    def save_density_tiff(density: np.ndarray, filepath: str,
                         transform: Optional[Affine] = None,
                         crs: Optional[str] = None,
                         nodata: float = np.nan) -> None:
        """
        Save fractal density map to GeoTIFF.

        Parameters
        ----------
        density : np.ndarray
            Fractal density array (2D)
        filepath : str
            Output GeoTIFF file path
        transform : Affine, optional
            Geospatial transform (georeferencing)
        crs : str, optional
            Coordinate reference system (e.g., 'EPSG:32630' for Mars IAU2000)
        nodata : float
            Value representing no data
        """
        height, width = density.shape

        # Default to identity transform if not provided
        if transform is None:
            transform = Affine.identity()

        with rasterio.open(
            filepath,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=rasterio.float32,
            crs=crs,
            transform=transform,
            nodata=nodata,
            compress='lzw',
        ) as dst:
            dst.write(density.astype(rasterio.float32), 1)

    @staticmethod
    def save_multi_band_tiff(bands: Dict[str, np.ndarray], filepath: str,
                            transform: Optional[Affine] = None,
                            crs: Optional[str] = None) -> None:
        """
        Save multiple analysis outputs to multi-band GeoTIFF.

        Parameters
        ----------
        bands : Dict[str, np.ndarray]
            Dictionary of band names to 2D arrays
        filepath : str
            Output GeoTIFF file path
        transform : Affine, optional
            Geospatial transform
        crs : str, optional
            Coordinate reference system
        """
        if not bands:
            raise ValueError("Must provide at least one band")

        height, width = next(iter(bands.values())).shape
        num_bands = len(bands)

        if transform is None:
            transform = Affine.identity()

        with rasterio.open(
            filepath,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=num_bands,
            dtype=rasterio.float32,
            crs=crs,
            transform=transform,
            compress='lzw',
        ) as dst:
            for band_idx, (name, data) in enumerate(bands.items(), 1):
                dst.write(data.astype(rasterio.float32), band_idx)
                dst.update_tags(band_idx, name=name)

    @staticmethod
    def save_with_dem(dem: np.ndarray, density: np.ndarray, filepath: str,
                     dem_crs: Optional[str] = None,
                     dem_transform: Optional[Affine] = None) -> None:
        """
        Save DEM and density map as multi-band GeoTIFF.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        density : np.ndarray
            Fractal density map
        filepath : str
            Output GeoTIFF file path
        dem_crs : str, optional
            Coordinate reference system
        dem_transform : Affine, optional
            Geospatial transform
        """
        bands = {
            'elevation': dem,
            'fractal_density': density,
        }

        GeoTIFFExporter.save_multi_band_tiff(
            bands, filepath,
            transform=dem_transform,
            crs=dem_crs
        )


class AnalysisReporter:
    """
    Generate analysis reports summarizing results.
    """

    @staticmethod
    def compute_statistics(density: np.ndarray) -> Dict[str, float]:
        """
        Compute summary statistics for density map.

        Parameters
        ----------
        density : np.ndarray
            Fractal density map

        Returns
        -------
        stats : Dict[str, float]
            Dictionary of statistics
        """
        valid_mask = np.isfinite(density)
        valid_data = density[valid_mask]

        if len(valid_data) == 0:
            return {}

        stats = {
            'mean': float(np.mean(valid_data)),
            'std': float(np.std(valid_data)),
            'min': float(np.min(valid_data)),
            'max': float(np.max(valid_data)),
            'median': float(np.median(valid_data)),
            'q25': float(np.percentile(valid_data, 25)),
            'q75': float(np.percentile(valid_data, 75)),
            'num_valid_pixels': int(np.sum(valid_mask)),
            'total_pixels': valid_data.size,
        }

        return stats

    @staticmethod
    def generate_report(dem: np.ndarray, density: np.ndarray,
                       title: str = "P-adic Fractal Analysis Report") -> str:
        """
        Generate comprehensive analysis report.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model
        density : np.ndarray
            Fractal density map
        title : str
            Report title

        Returns
        -------
        report : str
            Text report
        """
        dem_stats = AnalysisReporter.compute_statistics(dem)
        density_stats = AnalysisReporter.compute_statistics(density)

        report = "=" * 70 + "\n"
        report += title + "\n"
        report += "=" * 70 + "\n\n"

        # DEM statistics
        report += "DIGITAL ELEVATION MODEL STATISTICS\n"
        report += "-" * 70 + "\n"
        report += f"Mean elevation:        {dem_stats.get('mean', 0):.2f} m\n"
        report += f"Std deviation:         {dem_stats.get('std', 0):.2f} m\n"
        report += f"Min elevation:         {dem_stats.get('min', 0):.2f} m\n"
        report += f"Max elevation:         {dem_stats.get('max', 0):.2f} m\n"
        report += f"Median elevation:      {dem_stats.get('median', 0):.2f} m\n"
        report += f"Total relief:          {dem_stats.get('max', 0) - dem_stats.get('min', 0):.2f} m\n\n"

        # Fractal density statistics
        report += "FRACTAL DENSITY STATISTICS\n"
        report += "-" * 70 + "\n"
        report += f"Mean density:          {density_stats.get('mean', 0):.4f}\n"
        report += f"Std deviation:         {density_stats.get('std', 0):.4f}\n"
        report += f"Min density:           {density_stats.get('min', 0):.4f}\n"
        report += f"Max density:           {density_stats.get('max', 0):.4f}\n"
        report += f"Median density:        {density_stats.get('median', 0):.4f}\n"
        report += f"Q25-Q75 range:         [{density_stats.get('q25', 0):.4f}, {density_stats.get('q75', 0):.4f}]\n"
        report += f"Valid pixels:          {density_stats.get('num_valid_pixels', 0)}\n\n"

        # High-density regions
        high_density_threshold = density_stats.get('q75', 0)
        high_density_pixels = np.sum(density >= high_density_threshold)
        high_density_fraction = high_density_pixels / density_stats.get('num_valid_pixels', 1)

        report += "HIGH-DENSITY REGIONS (>Q75)\n"
        report += "-" * 70 + "\n"
        report += f"Number of pixels:      {high_density_pixels}\n"
        report += f"Fraction of domain:    {high_density_fraction:.1%}\n\n"

        report += "=" * 70 + "\n"

        return report
