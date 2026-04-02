"""
Ultrametric distance computation and hierarchical clustering.

Implements ultrametric distance metrics on hierarchical terrain data,
enabling robust single-linkage agglomerative clustering with O(n log n)
complexity via tree-based algorithms.
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
from typing import Tuple, List, Dict, Optional, Callable
from .quadtree import PadicQuadtree, QuadtreeNode


class UltrametricDistance:
    """
    Compute and manage ultrametric distances for hierarchical terrain data.
    """

    def __init__(self, quadtree: PadicQuadtree, dem: np.ndarray):
        """
        Initialize ultrametric distance calculator.

        Parameters
        ----------
        quadtree : PadicQuadtree
            P-adic quadtree spatial index
        dem : np.ndarray
            Digital elevation model
        """
        self.quadtree = quadtree
        self.dem = dem
        self.height, self.width = dem.shape

    def spatial_distance(self, i1: int, j1: int, i2: int, j2: int) -> float:
        """
        Compute spatial ultrametric distance based on quadtree hierarchy.

        Distance = 2^(-k) where k is the deepest tree level containing both points.

        Parameters
        ----------
        i1, j1, i2, j2 : int
            Coordinates of two pixels

        Returns
        -------
        distance : float
            Ultrametric spatial distance
        """
        return self.quadtree.get_ultrametric_distance(i1, j1, i2, j2)

    def elevation_distance(self, i1: int, j1: int, i2: int, j2: int,
                          normalized: bool = True) -> float:
        """
        Compute elevation-based distance between two pixels.

        Parameters
        ----------
        i1, j1, i2, j2 : int
            Coordinates of two pixels
        normalized : bool
            Whether to normalize by elevation variance

        Returns
        -------
        distance : float
            Elevation distance
        """
        if not (0 <= i1 < self.height and 0 <= j1 < self.width):
            return np.inf
        if not (0 <= i2 < self.height and 0 <= j2 < self.width):
            return np.inf

        elev_diff = abs(self.dem[i1, j1] - self.dem[i2, j2])

        if normalized:
            valid_data = self.dem[np.isfinite(self.dem)]
            elev_std = np.std(valid_data)
            return elev_diff / (elev_std + 1e-8)
        else:
            return elev_diff

    def combined_distance(self, i1: int, j1: int, i2: int, j2: int,
                         spatial_weight: float = 1.0,
                         elevation_weight: float = 1.0) -> float:
        """
        Combine spatial and elevation distances using ultrametric max norm.

        Parameters
        ----------
        i1, j1, i2, j2 : int
            Coordinates of two pixels
        spatial_weight : float
            Weight for spatial distance
        elevation_weight : float
            Weight for elevation distance

        Returns
        -------
        distance : float
            Combined ultrametric distance
        """
        d_spatial = self.spatial_distance(i1, j1, i2, j2)
        d_elevation = self.elevation_distance(i1, j1, i2, j2)

        # Ultrametric max norm preserves ultrametric property
        distance = max(spatial_weight * d_spatial, elevation_weight * d_elevation)

        return distance

    def compute_distance_matrix(self, sample_indices: Optional[List[Tuple[int, int]]] = None,
                               distance_func: Callable = None) -> np.ndarray:
        """
        Compute pairwise distance matrix between sample points.

        For full data, sample_indices=None. For subsampling, provide list of
        (i, j) coordinates.

        Parameters
        ----------
        sample_indices : List[Tuple[int, int]], optional
            List of sample coordinates. If None, use all pixels.
        distance_func : Callable, optional
            Distance function to use. If None, use combined_distance.

        Returns
        -------
        distance_matrix : np.ndarray
            Symmetric distance matrix
        """
        if distance_func is None:
            distance_func = self.combined_distance

        if sample_indices is None:
            # Sample 1% of pixels for efficiency
            total_pixels = self.height * self.width
            num_samples = max(100, int(0.01 * total_pixels))
            indices = np.random.choice(total_pixels, num_samples, replace=False)
            sample_indices = [(i // self.width, i % self.width) for i in indices]

        n = len(sample_indices)
        distance_matrix = np.zeros((n, n), dtype=np.float32)

        for i in range(n):
            for j in range(i + 1, n):
                i1, j1 = sample_indices[i]
                i2, j2 = sample_indices[j]
                dist = distance_func(i1, j1, i2, j2)
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist

        return distance_matrix


class HierarchicalClustering:
    """
    Hierarchical clustering using ultrametric distances.

    Implements single-linkage agglomerative clustering on ultrametric spaces,
    producing dendrograms that preserve hierarchical terrain structure.
    """

    def __init__(self, distance_matrix: np.ndarray, labels: Optional[List[str]] = None):
        """
        Initialize clustering with distance matrix.

        Parameters
        ----------
        distance_matrix : np.ndarray
            Symmetric distance matrix
        labels : List[str], optional
            Labels for data points
        """
        self.distance_matrix = distance_matrix
        self.n = distance_matrix.shape[0]
        self.labels = labels or [str(i) for i in range(self.n)]

    def single_linkage(self) -> Tuple[np.ndarray, Dict]:
        """
        Perform single-linkage agglomerative clustering.

        Uses scipy linkage function with 'single' method.

        Returns
        -------
        linkage_matrix : np.ndarray
            Linkage matrix encoding dendrogram structure
        stats : dict
            Clustering statistics
        """
        # Convert distance matrix to condensed form
        condensed = squareform(self.distance_matrix)

        # Perform single-linkage clustering
        linkage_matrix = linkage(condensed, method='single')

        # Compute statistics
        stats = {
            'num_clusters': self.n,
            'max_distance': np.max(self.distance_matrix),
            'min_distance': np.min(self.distance_matrix[self.distance_matrix > 0]),
        }

        return linkage_matrix, stats

    def complete_linkage(self) -> Tuple[np.ndarray, Dict]:
        """
        Perform complete-linkage agglomerative clustering.

        Uses maximum inter-cluster distance.

        Returns
        -------
        linkage_matrix : np.ndarray
            Linkage matrix encoding dendrogram structure
        stats : dict
            Clustering statistics
        """
        condensed = squareform(self.distance_matrix)
        linkage_matrix = linkage(condensed, method='complete')

        stats = {
            'method': 'complete_linkage',
            'num_samples': self.n,
            'max_distance': np.max(self.distance_matrix),
        }

        return linkage_matrix, stats

    def average_linkage(self) -> Tuple[np.ndarray, Dict]:
        """
        Perform average-linkage (UPGMA) clustering.

        Uses mean inter-cluster distance.

        Returns
        -------
        linkage_matrix : np.ndarray
            Linkage matrix encoding dendrogram structure
        stats : dict
            Clustering statistics
        """
        condensed = squareform(self.distance_matrix)
        linkage_matrix = linkage(condensed, method='average')

        stats = {
            'method': 'average_linkage',
            'num_samples': self.n,
        }

        return linkage_matrix, stats

    def cut_dendrogram(self, linkage_matrix: np.ndarray, height: float) -> np.ndarray:
        """
        Cut dendrogram at specified height to extract clusters.

        Parameters
        ----------
        linkage_matrix : np.ndarray
            Linkage matrix from clustering
        height : float
            Height at which to cut the dendrogram

        Returns
        -------
        cluster_labels : np.ndarray
            Cluster assignment for each data point
        """
        from scipy.cluster.hierarchy import fcluster

        # Use distance threshold to cut tree
        clusters = fcluster(linkage_matrix, height, criterion='distance')
        return clusters

    def validate_ultrametric(self) -> Tuple[bool, Dict]:
        """
        Validate that distance matrix satisfies ultrametric property.

        Strong triangle inequality: d(x,z) <= max(d(x,y), d(y,z))

        Returns
        -------
        is_ultrametric : bool
            Whether all triples satisfy ultrametric property
        stats : dict
            Validation statistics
        """
        violations = 0
        total_checks = 0

        for i in range(self.n):
            for j in range(i + 1, self.n):
                for k in range(j + 1, self.n):
                    d_ij = self.distance_matrix[i, j]
                    d_jk = self.distance_matrix[j, k]
                    d_ik = self.distance_matrix[i, k]

                    # Check strong triangle inequality
                    max_ij_jk = max(d_ij, d_jk)
                    if d_ik > max_ij_jk + 1e-10:  # Small tolerance for numerical errors
                        violations += 1

                    total_checks += 1

        is_ultrametric = violations == 0
        violation_rate = violations / total_checks if total_checks > 0 else 0

        stats = {
            'is_ultrametric': is_ultrametric,
            'total_triples': total_checks,
            'violations': violations,
            'violation_rate': violation_rate,
        }

        return is_ultrametric, stats


class TerrainSegmentation:
    """
    Segment terrain using hierarchical clustering on ultrametric distances.
    """

    def __init__(self, quadtree: PadicQuadtree, dem: np.ndarray):
        """
        Initialize terrain segmentation.

        Parameters
        ----------
        quadtree : PadicQuadtree
            P-adic quadtree spatial index
        dem : np.ndarray
            Digital elevation model
        """
        self.quadtree = quadtree
        self.dem = dem
        self.height, self.width = dem.shape

    def segment_by_scale(self, target_level: int) -> np.ndarray:
        """
        Segment terrain at a specific pyramid scale.

        Parameters
        ----------
        target_level : int
            Pyramid level for segmentation

        Returns
        -------
        segmentation : np.ndarray
            Cluster labels at base resolution
        """
        nodes = self.quadtree.get_level_nodes(target_level)

        # Create segmentation map
        segmentation = np.zeros((self.height, self.width), dtype=np.int32)

        for cluster_id, node in enumerate(nodes):
            min_row, max_row, min_col, max_col = node.bounds
            segmentation[min_row:max_row, min_col:max_col] = cluster_id

        return segmentation

    def compute_cluster_properties(self, cluster_labels: np.ndarray) -> Dict:
        """
        Compute properties for each cluster.

        Parameters
        ----------
        cluster_labels : np.ndarray
            Cluster assignment for each pixel

        Returns
        -------
        properties : dict
            Properties indexed by cluster ID
        """
        properties = {}
        unique_labels = np.unique(cluster_labels[cluster_labels >= 0])

        for cluster_id in unique_labels:
            mask = cluster_labels == cluster_id
            cluster_data = self.dem[mask]

            properties[int(cluster_id)] = {
                'num_pixels': np.sum(mask),
                'mean_elevation': float(np.mean(cluster_data)),
                'std_elevation': float(np.std(cluster_data)),
                'min_elevation': float(np.min(cluster_data)),
                'max_elevation': float(np.max(cluster_data)),
                'slope': float(np.max(cluster_data) - np.min(cluster_data)),
            }

        return properties
