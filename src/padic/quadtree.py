"""
P-adic quadtree spatial data structure for hierarchical terrain encoding.

Implements ultrametric spatial indexing with aggregated statistics,
using TOP-DOWN recursive subdivision (correct approach).
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple
from collections import deque


@dataclass
class QuadtreeNode:
    """
    Node in a p-adic quadtree representing a spatial region.

    Attributes
    ----------
    level : int
        Tree level (0 = root/coarsest, increasing = finer resolution)
    bounds : tuple
        (min_row, max_row, min_col, max_col) spatial extent
    elevation_mean : float
        Mean elevation in this region
    elevation_variance : float
        Elevation variance in this region
    elevation_min : float
        Minimum elevation in this region
    elevation_max : float
        Maximum elevation in this region
    roughness : float
        Terrain roughness measure
    num_pixels : int
        Number of pixels represented by this node
    children : List[QuadtreeNode]
        Child nodes (4 for internal, empty for leaf)
    parent : Optional[QuadtreeNode]
        Parent node (None for root)
    """
    level: int
    bounds: Tuple[int, int, int, int]
    elevation_mean: float = 0.0
    elevation_variance: float = 0.0
    elevation_min: float = 0.0
    elevation_max: float = 0.0
    roughness: float = 0.0
    num_pixels: int = 0
    children: List['QuadtreeNode'] = None
    parent: Optional['QuadtreeNode'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0

    def get_center(self) -> Tuple[float, float]:
        """Get center coordinates of this node's spatial extent."""
        min_row, max_row, min_col, max_col = self.bounds
        center_row = (min_row + max_row) / 2.0
        center_col = (min_col + max_col) / 2.0
        return center_row, center_col

    def get_size(self) -> Tuple[int, int]:
        """Get height and width of spatial extent."""
        min_row, max_row, min_col, max_col = self.bounds
        height = max_row - min_row
        width = max_col - min_col
        return height, width


class PadicQuadtree:
    """
    P-adic quadtree for hierarchical spatial indexing of terrain data.

    Builds a complete quaternary tree TOP-DOWN by recursive subdivision,
    aggregating statistics at each level.
    """

    def __init__(self, dem: np.ndarray, base_resolution: float = 1.0):
        """
        Initialize quadtree from DEM.

        Parameters
        ----------
        dem : np.ndarray
            Digital elevation model (2D array)
        base_resolution : float
            Cell size at finest level in meters
        """
        self.dem = dem.copy()
        self.base_resolution = base_resolution
        self.height, self.width = dem.shape

        # Build the tree top-down
        print(f"Building quadtree from {self.height}×{self.width} DEM...")
        self.root = self._build_tree_recursive(
            bounds=(0, self.height, 0, self.width),
            level=0,
            parent=None
        )
        self.max_depth = self._compute_max_depth()
        print(f"✓ Built tree with max_depth={self.max_depth}")

    def _build_tree_recursive(self, bounds: Tuple[int, int, int, int],
                             level: int, parent: Optional[QuadtreeNode]) -> QuadtreeNode:
        """
        Recursively build quadtree using top-down approach.

        Parameters
        ----------
        bounds : tuple
            (min_row, max_row, min_col, max_col)
        level : int
            Current tree level (0 = root)
        parent : QuadtreeNode or None
            Parent node reference

        Returns
        -------
        node : QuadtreeNode
            The root of this subtree
        """
        min_row, max_row, min_col, max_col = bounds

        # Extract region from DEM
        region = self.dem[min_row:max_row, min_col:max_col]

        # Compute statistics for this region
        valid_data = region[np.isfinite(region)]

        if len(valid_data) > 0:
            elevation_mean = np.mean(valid_data)
            elevation_variance = np.var(valid_data)
            elevation_min = np.min(valid_data)
            elevation_max = np.max(valid_data)
            roughness = np.std(valid_data)
        else:
            elevation_mean = np.nan
            elevation_variance = 0.0
            elevation_min = np.nan
            elevation_max = np.nan
            roughness = 0.0

        num_pixels = region.size

        # Create node
        node = QuadtreeNode(
            level=level,
            bounds=bounds,
            elevation_mean=elevation_mean,
            elevation_variance=elevation_variance,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            roughness=roughness,
            num_pixels=num_pixels,
            parent=parent
        )

        # Decide whether to subdivide
        # Subdivide if region is larger than 1×1 pixels
        height = max_row - min_row
        width = max_col - min_col

        if height > 1 and width > 1:
            # Compute midpoints
            mid_row = (min_row + max_row) // 2
            mid_col = (min_col + max_col) // 2

            # Create four children (NW, NE, SW, SE)
            children_bounds = [
                (min_row, mid_row, min_col, mid_col),      # NW
                (min_row, mid_row, mid_col, max_col),      # NE
                (mid_row, max_row, min_col, mid_col),      # SW
                (mid_row, max_row, mid_col, max_col),      # SE
            ]

            for child_bounds in children_bounds:
                child = self._build_tree_recursive(
                    bounds=child_bounds,
                    level=level + 1,
                    parent=node
                )
                node.children.append(child)

        return node

    def _compute_max_depth(self) -> int:
        """Compute maximum depth of tree."""
        def max_depth_recursive(node: QuadtreeNode) -> int:
            if node.is_leaf():
                return 0
            return 1 + max(max_depth_recursive(child) for child in node.children)

        return max_depth_recursive(self.root)

    def find_node_at(self, i: int, j: int, target_level: Optional[int] = None) -> QuadtreeNode:
        """
        Find quadtree node containing pixel (i, j).

        Parameters
        ----------
        i, j : int
            Pixel coordinates
        target_level : int, optional
            Target tree level. If None, returns finest-resolution node.

        Returns
        -------
        node : QuadtreeNode
            Node containing the pixel
        """
        current = self.root

        while not current.is_leaf():
            if target_level is not None and current.level >= target_level:
                return current

            # Find which child contains this pixel
            min_row, max_row, min_col, max_col = current.bounds
            mid_row = (min_row + max_row) // 2
            mid_col = (min_col + max_col) // 2

            # Determine which quadrant
            if i < mid_row:
                if j < mid_col:
                    current = current.children[0]  # NW
                else:
                    current = current.children[1]  # NE
            else:
                if j < mid_col:
                    current = current.children[2]  # SW
                else:
                    current = current.children[3]  # SE

        return current

    def get_ultrametric_distance(self, i1: int, j1: int, i2: int, j2: int) -> float:
        """
        Compute ultrametric distance between two pixels.

        Distance equals 2^(-k) where k is the finest tree level containing both pixels.

        Parameters
        ----------
        i1, j1, i2, j2 : int
            Coordinates of two pixels

        Returns
        -------
        distance : float
            Ultrametric distance
        """
        if i1 == i2 and j1 == j2:
            return 0.0

        # Find nodes at each level and check if they share a parent
        node1 = self.find_node_at(i1, j1)
        node2 = self.find_node_at(i2, j2)

        # Trace up the tree until finding common ancestor
        ancestors1 = []
        current = node1
        while current is not None:
            ancestors1.append(current)
            current = current.parent

        ancestors1_dict = {id(node): node for node in ancestors1}

        # Find common ancestor level
        current = node2
        while current is not None:
            if id(current) in ancestors1_dict:
                # Found common ancestor
                lca_level = current.level
                distance = 2.0 ** (-lca_level)
                return distance
            current = current.parent

        # Should never reach here
        return float('inf')

    def query_neighborhood(self, i: int, j: int, radius: float) -> List[QuadtreeNode]:
        """
        Query all nodes within ultrametric distance radius of (i, j).

        Parameters
        ----------
        i, j : int
            Center pixel coordinates
        radius : float
            Ultrametric distance radius

        Returns
        -------
        nodes : List[QuadtreeNode]
            Nodes within radius
        """
        center_node = self.find_node_at(i, j)
        results = []

        # Breadth-first search from center
        queue = deque([center_node])
        visited = set()

        while queue:
            node = queue.popleft()
            if id(node) in visited:
                continue
            visited.add(id(node))

            # Check if node's center is within radius
            ni, nj = node.get_center()
            dist = self.get_ultrametric_distance(int(ni), int(nj), i, j)

            if dist <= radius:
                results.append(node)

                # Add children to queue
                if not node.is_leaf():
                    queue.extend(node.children)

            # Add siblings and parent
            if node.parent is not None:
                for sibling in node.parent.children:
                    if id(sibling) not in visited:
                        queue.append(sibling)

        return results

    def get_level_nodes(self, level: int) -> List[QuadtreeNode]:
        """
        Get all nodes at a specific tree level.

        Parameters
        ----------
        level : int
            Tree level (0 = root, increasing = finer)

        Returns
        -------
        nodes : List[QuadtreeNode]
            All nodes at specified level
        """
        nodes = []
        queue = deque([self.root])

        while queue:
            node = queue.popleft()

            if node.level == level:
                nodes.append(node)
            elif node.level < level:
                queue.extend(node.children)

        return nodes

    def extract_statistics_grid(self, level: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract elevation statistics at a tree level as 2D grids.

        Parameters
        ----------
        level : int
            Tree level

        Returns
        -------
        mean_grid : np.ndarray
            Mean elevation at each spatial location
        var_grid : np.ndarray
            Variance at each spatial location
        roughness_grid : np.ndarray
            Roughness at each spatial location
        """
        nodes = self.get_level_nodes(level)

        # Initialize output grids
        mean_grid = np.full((self.height, self.width), np.nan, dtype=np.float32)
        var_grid = np.full((self.height, self.width), np.nan, dtype=np.float32)
        roughness_grid = np.full((self.height, self.width), np.nan, dtype=np.float32)

        # Fill grids from nodes
        for node in nodes:
            min_row, max_row, min_col, max_col = node.bounds
            mean_grid[min_row:max_row, min_col:max_col] = node.elevation_mean
            var_grid[min_row:max_row, min_col:max_col] = node.elevation_variance
            roughness_grid[min_row:max_row, min_col:max_col] = node.roughness

        return mean_grid, var_grid, roughness_grid
