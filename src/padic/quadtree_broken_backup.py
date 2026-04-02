"""
P-adic quadtree spatial data structure for hierarchical terrain encoding.

Implements ultrametric spatial indexing with aggregated statistics,
enabling O(log n) spatial queries and O(n) total storage for terrain analysis.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from collections import deque


@dataclass
class QuadtreeNode:
    """
    Node in a p-adic quadtree representing a spatial region.

    Attributes
    ----------
    level : int
        Tree level (0 = finest resolution, increasing = coarser)
    bounds : tuple
        (min_row, max_row, min_col, max_col) spatial extent
    morton_code : int
        Z-order curve code for space-filling curve ordering
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
        Child nodes (empty list for leaf nodes)
    parent : Optional[QuadtreeNode]
        Parent node (None for root)
    """
    level: int
    bounds: Tuple[int, int, int, int]
    morton_code: int
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
        center_row = (min_row + max_row) / 2
        center_col = (min_col + max_col) / 2
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

    Builds a complete quaternary tree bottom-up from pixels, aggregating
    statistics at each level to enable efficient hierarchical queries.
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

        # Ensure dimensions are powers of 2 (pad if necessary)
        self._pad_to_power_of_2()

        # Build the tree bottom-up
        self.root = self._build_tree()
        self.max_depth = self._compute_max_depth()

    def _pad_to_power_of_2(self) -> None:
        """Pad DEM dimensions to nearest power of 2."""
        max_dim = max(self.dem.shape)
        new_size = 2 ** int(np.ceil(np.log2(max_dim)))

        if new_size > max(self.dem.shape):
            padded = np.full((new_size, new_size), np.nan, dtype=np.float32)
            padded[:self.height, :self.width] = self.dem
            self.dem = padded
            self.height, self.width = self.dem.shape

    def _build_tree(self) -> QuadtreeNode:
        """Build quadtree bottom-up from pixels."""
        # Create leaf nodes (one per pixel)
        leaves = {}
        for i in range(self.height):
            for j in range(self.width):
                val = self.dem[i, j]
                morton = self._compute_morton_code(i, j)
                leaves[(i, j)] = QuadtreeNode(
                    level=0,
                    bounds=(i, i + 1, j, j + 1),
                    morton_code=morton,
                    elevation_mean=val,
                    elevation_variance=0.0,
                    elevation_min=val,
                    elevation_max=val,
                    roughness=0.0,
                    num_pixels=1,
                )

        # Aggregate upward through tree
        current_nodes = leaves
        level = 1

        while len(current_nodes) > 1:
            next_level_nodes = {}

            # Group nodes into 2x2 blocks
            for (i, j), node in current_nodes.items():
                # Find which 2x2 block this pixel belongs to
                parent_i = i // 2
                parent_j = j // 2
                parent_key = (parent_i, parent_j)

                if parent_key not in next_level_nodes:
                    next_level_nodes[parent_key] = QuadtreeNode(
                        level=level,
                        bounds=(0, 0, 0, 0),  # Will be computed from children
                        morton_code=self._compute_morton_code(parent_i, parent_j),
                    )

                next_level_nodes[parent_key].children.append(node)
                node.parent = next_level_nodes[parent_key]

            # Aggregate statistics for each parent
            for parent in next_level_nodes.values():
                # Compute bounds from children
                child_bounds = [child.bounds for child in parent.children]
                min_row = min(b[0] for b in child_bounds)
                max_row = max(b[1] for b in child_bounds)
                min_col = min(b[2] for b in child_bounds)
                max_col = max(b[3] for b in child_bounds)
                parent.bounds = (min_row, max_row, min_col, max_col)

                # Aggregate statistics from children
                means = []
                variances = []
                mins = []
                maxs = []
                num_pixels = 0

                for child in parent.children:
                    means.append(child.elevation_mean)
                    variances.append(child.elevation_variance)
                    mins.append(child.elevation_min)
                    maxs.append(child.elevation_max)
                    num_pixels += child.num_pixels

                # Aggregate mean: weighted average of child means
                means = np.array(means)
                parent.elevation_mean = np.mean(means)

                # Aggregate variance: sum of within-group and between-group variance
                # var_total = E[var_i] + var(E[X_i])
                variances = np.array(variances)
                between_var = np.var(means)  # Variance of means
                within_var = np.mean(variances)  # Average of variances
                parent.elevation_variance = within_var + between_var

                # Aggregate min/max
                parent.elevation_min = np.min(mins)
                parent.elevation_max = np.max(maxs)

                # Roughness is std of child means
                parent.roughness = np.std(means)
                parent.num_pixels = num_pixels

            current_nodes = next_level_nodes
            level += 1

        # Return the root (should be single node)
        return list(current_nodes.values())[0]

    def _compute_morton_code(self, i: int, j: int) -> int:
        """
        Compute Morton code (Z-order curve) for coordinates (i, j).

        Interleaves binary representations: ...i2j2i1j1i0j0
        """
        code = 0
        for k in range(16):  # Support up to 2^16 x 2^16 grids
            code |= ((i >> k) & 1) << (2 * k)
            code |= ((j >> k) & 1) << (2 * k + 1)
        return code

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

            child_idx = 0
            if i >= mid_row:
                child_idx += 2
            if j >= mid_col:
                child_idx += 1

            current = current.children[child_idx]

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

        # Find lowest common ancestor
        node1 = self.find_node_at(i1, j1)
        node2 = self.find_node_at(i2, j2)

        # Trace upward until finding common ancestor
        nodes1 = [node1]
        current = node1
        while current.parent is not None:
            current = current.parent
            nodes1.append(current)

        nodes1_set = set(nodes1)

        current = node2
        while current not in nodes1_set:
            current = current.parent

        # current is now the lowest common ancestor
        lca_level = current.level

        # Distance is 2^(-level) where level is measured from root
        # Normalize so finest level (0) has distance 2^0 = 1
        distance = 2.0 ** (-lca_level)

        return distance

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

        # Compute grid size at this level
        grid_size = 2 ** level
        mean_grid = np.zeros((grid_size, grid_size), dtype=np.float32)
        var_grid = np.zeros((grid_size, grid_size), dtype=np.float32)
        roughness_grid = np.zeros((grid_size, grid_size), dtype=np.float32)

        for node in nodes:
            min_row, max_row, min_col, max_col = node.bounds
            mean_grid[min_row:max_row, min_col:max_col] = node.elevation_mean
            var_grid[min_row:max_row, min_col:max_col] = node.elevation_variance
            roughness_grid[min_row:max_row, min_col:max_col] = node.roughness

        return mean_grid, var_grid, roughness_grid

    def save_structure(self, filepath: str) -> None:
        """
        Save quadtree structure to file.

        Parameters
        ----------
        filepath : str
            Output file path (.npz format)
        """
        # Extract all nodes via level-order traversal
        all_nodes = []
        queue = deque([self.root])

        while queue:
            node = queue.popleft()
            all_nodes.append(node)
            queue.extend(node.children)

        # Save node data
        np.savez(
            filepath,
            height=self.height,
            width=self.width,
            base_resolution=self.base_resolution,
            max_depth=self.max_depth,
            num_nodes=len(all_nodes),
        )

    def __repr__(self) -> str:
        """String representation of quadtree."""
        return (f"PadicQuadtree(shape={self.height}x{self.width}, "
                f"depth={self.max_depth}, resolution={self.base_resolution}m)")


def build_padic_quadtree(dem: np.ndarray, base_resolution: float = 1.0) -> PadicQuadtree:
    """
    Convenience function to build a p-adic quadtree from a DEM.

    Parameters
    ----------
    dem : np.ndarray
        Digital elevation model
    base_resolution : float
        Cell size at finest level in meters

    Returns
    -------
    quadtree : PadicQuadtree
        Built quadtree
    """
    return PadicQuadtree(dem, base_resolution)
