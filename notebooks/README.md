# Notebooks

Analysis notebooks in execution order. Run from the repo root after activating the environment.

| Notebook | Description | Status |
|---|---|---|
| `01_synthetic_terrain_validation.ipynb` | Validate synthetic terrain generators and fractal dimension estimation | Complete |
| `02_mars_dem_analysis.ipynb` | Core Mars DEM pipeline on Jezero crater data | Complete |
| `03_mars_samples_validation.ipynb` | Overlay Mars 2020 sample locations on terrain analysis | Complete |
| `04_per_pixel_padic_methods.ipynb` | Four per-pixel complexity methods (roughness, entropy, wavelet, ultrametric) | Mostly complete |
| `05_padic_visualization.ipynb` | Basic p-adic embedding visualization experiments | Partial |
| `06_quadtree_build_inspect_visualize.ipynb` | Quadtree construction, inspection, Sierpinski visualizations | Mostly complete |
| `07_mnist_padic_visualization.ipynb` | MNIST digit embeddings in p-adic space | Mostly complete |
| `08_padic_terrain_visualization.ipynb` | Terrain complexity visualizations | Complete |
| `09_padic_terrain_complexity.ipynb` | Terrain complexity analysis | Complete |
| `10_enhanced_padic_visualization.ipynb` | Enhanced embedding visualizations, parameter exploration | Complete |
| `11_chistyakov_parameter_validation.ipynb` | Parameter sweep and validation against Chistyakov (1996) values | Complete |
| `12_mnist_padic_figure4_corrected.ipynb` | Figure 4 recreation using MNIST digits — clean Sierpinski structure confirmed | Complete |
| `18_perpixel_fractal_maps.ipynb` | Per-pixel fractal maps from cached numpy arrays | Mostly complete |
| `19_figure4_paper_reproduction.ipynb` | Earlier Figure 4 attempt — **superseded by notebook 20** | Superseded |
| `20_figure4_definitive.ipynb` | **Definitive Figure 4 reproduction** (Zúñiga-Galindo 2023): correct params, MNIST "5", proper layout | Active |

## Key Result: Figure 4

The target is Figure 4 from Zúñiga-Galindo et al. (2023) (`references/ptad061fig4.jpeg`):
- **Left panel**: Sierpinski triangle embedding in complex plane (p=3, l=6, m=0, s≈0.46), colored by pixel foreground/background
- **Right panel**: Source 27×27 binary image (MNIST digit "5")

Parameters confirmed working in notebook 12. Definitive reproduction in notebook 20.
