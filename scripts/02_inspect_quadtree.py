#!/usr/bin/env python3
"""
Inspect the p-adic quadtree structure.

This script analyzes:
1. Tree structure and depth
2. Node distribution across levels
3. Variance patterns
4. Spatial extent of nodes
"""

import pickle
from pathlib import Path
from collections import deque

CACHE_DIR = Path('/Volumes/Fangorn/padic_fractal_analysis/cache')
QUADTREE_CACHE = CACHE_DIR / 'quadtree.pkl'


def load_quadtree():
    """Load saved quadtree."""
    if not QUADTREE_CACHE.exists():
        print(f"ERROR: Quadtree cache not found at {QUADTREE_CACHE}")
        print("Run: python3 01_build_and_save_quadtree.py")
        return None

    with open(QUADTREE_CACHE, 'rb') as f:
        qtree = pickle.load(f)

    return qtree


def analyze_tree(qtree):
    """Analyze quadtree structure."""

    print("=" * 80)
    print("QUADTREE STRUCTURE ANALYSIS")
    print("=" * 80)

    # Basic info
    print(f"\n1. Basic Information:")
    print(f"   Max depth: {qtree.max_depth}")
    print(f"   Height: {qtree.height}")
    print(f"   Width: {qtree.width}")
    print(f"   Total pixels: {qtree.height * qtree.width}")

    # Root node
    print(f"\n2. Root Node:")
    root = qtree.root
    print(f"   Level: {root.level}")
    print(f"   Bounds: {root.bounds}")
    print(f"   Num pixels: {root.num_pixels}")
    print(f"   Num children: {len(root.children)}")
    print(f"   Elevation mean: {root.elevation_mean:.2f}")
    print(f"   Elevation variance: {root.elevation_variance:.6f}")
    print(f"   Elevation min/max: {root.elevation_min:.2f} / {root.elevation_max:.2f}")

    # Level distribution
    print(f"\n3. Level Distribution:")
    level_info = {}

    queue = deque([root])
    while queue:
        node = queue.popleft()

        if node.level not in level_info:
            level_info[node.level] = {
                'count': 0,
                'variances': [],
                'num_pixels_list': [],
                'min_bounds': None,
                'max_bounds': None,
            }

        level_info[node.level]['count'] += 1
        level_info[node.level]['variances'].append(node.elevation_variance)
        level_info[node.level]['num_pixels_list'].append(node.num_pixels)

        if level_info[node.level]['min_bounds'] is None:
            level_info[node.level]['min_bounds'] = node.bounds
            level_info[node.level]['max_bounds'] = node.bounds
        else:
            # Track min/max bounds
            min_r, max_r, min_c, max_c = node.bounds
            current_min = level_info[node.level]['min_bounds']
            current_max = level_info[node.level]['max_bounds']

            level_info[node.level]['min_bounds'] = (
                min(current_min[0], min_r),
                max(current_min[1], max_r),
                min(current_min[2], min_c),
                max(current_min[3], max_c),
            )

        for child in node.children:
            queue.append(child)

    print(
        "   Level | Count | Avg Var | Std Var | Min Pix | Max Pix | Avg Pix"
    )
    print("   " + "-" * 70)

    for level in sorted(level_info.keys()):
        info = level_info[level]
        count = info['count']
        variances = info['variances']
        num_pixels = info['num_pixels_list']

        import numpy as np

        avg_var = np.mean(variances)
        std_var = np.std(variances)
        min_pix = np.min(num_pixels)
        max_pix = np.max(num_pixels)
        avg_pix = np.mean(num_pixels)

        print(
            f"   {level:5d} | {count:5d} | {avg_var:7.6f} | {std_var:7.6f} | {min_pix:7d} | {max_pix:7d} | {avg_pix:7.1f}"
        )

    # Sample node inspection
    print(f"\n4. Sample Node Inspection:")
    print("   Checking specific nodes at each level...\n")

    def get_node_at_level(node, target_level):
        """Get first node at target level."""
        if node.level == target_level:
            return node
        for child in node.children:
            result = get_node_at_level(child, target_level)
            if result:
                return result
        return None

    for level in [0, 1, 2, 3, 4, 5, min(6, qtree.max_depth)]:
        if level <= qtree.max_depth:
            sample_node = get_node_at_level(root, level)
            if sample_node:
                print(f"   Level {level}:")
                print(f"      Bounds: {sample_node.bounds}")
                print(f"      Size: {sample_node.bounds[1] - sample_node.bounds[0]} x {sample_node.bounds[3] - sample_node.bounds[2]}")
                print(f"      Num pixels: {sample_node.num_pixels}")
                print(f"      Num children: {len(sample_node.children)}")
                print(f"      Variance: {sample_node.elevation_variance:.6f}")
                print(f"      Is leaf: {sample_node.is_leaf()}")
                print()

    # Variance progression
    print(f"5. Variance Progression by Level:")
    print("   (Shows how variance changes as we go up the tree)")
    print()

    import numpy as np

    for level in sorted(level_info.keys())[:10]:  # First 10 levels
        variances = np.array(level_info[level]['variances'])
        print(
            f"   Level {level:2d}: min={np.min(variances):.6f}, mean={np.mean(variances):.6f}, max={np.max(variances):.6f}"
        )

    print("\n" + "=" * 80)
    print("✓ ANALYSIS COMPLETE")
    print("=" * 80)
    print()


def check_tree_validity(qtree):
    """Verify tree structure is valid."""

    print("=" * 80)
    print("TREE VALIDITY CHECK")
    print("=" * 80)

    root = qtree.root
    errors = []

    # Check 1: All nodes should have parent-child relationships
    print("\n1. Checking parent-child relationships...")

    def check_node(node, parent=None):
        issues = []
        if parent is not None and node.parent != parent:
            issues.append(f"Node level {node.level} has wrong parent")

        for child in node.children:
            if child.parent != node:
                issues.append(f"Child of level {node.level} has wrong parent")
            issues.extend(check_node(child, node))

        return issues

    issues = check_node(root)
    if issues:
        print(f"   ✗ Found {len(issues)} parent-child issues:")
        for issue in issues[:5]:
            print(f"      - {issue}")
        errors.extend(issues)
    else:
        print("   ✓ All parent-child relationships correct")

    # Check 2: Verify num_pixels is consistent
    print("\n2. Checking num_pixels consistency...")

    def check_pixels(node):
        issues = []
        if len(node.children) == 0:
            # Leaf node should have num_pixels = 1
            if node.num_pixels != 1:
                issues.append(
                    f"Leaf node level {node.level} has num_pixels={node.num_pixels}, expected 1"
                )
        else:
            # Internal node should sum children's pixels
            child_pixels = sum(child.num_pixels for child in node.children)
            if node.num_pixels != child_pixels:
                issues.append(
                    f"Node level {node.level} num_pixels={node.num_pixels}, children sum={child_pixels}"
                )

        for child in node.children:
            issues.extend(check_pixels(child))

        return issues

    issues = check_pixels(root)
    if issues:
        print(f"   ✗ Found {len(issues)} num_pixels issues:")
        for issue in issues[:5]:
            print(f"      - {issue}")
        errors.extend(issues)
    else:
        print("   ✓ All num_pixels values consistent")

    # Check 3: Verify variance values
    print("\n3. Checking variance values...")

    def check_variance(node):
        issues = []
        if node.elevation_variance < 0:
            issues.append(
                f"Node level {node.level} has negative variance: {node.elevation_variance}"
            )
        if node.elevation_variance != node.elevation_variance:  # NaN check
            issues.append(f"Node level {node.level} has NaN variance")

        for child in node.children:
            issues.extend(check_variance(child))

        return issues

    issues = check_variance(root)
    if issues:
        print(f"   ✗ Found {len(issues)} variance issues:")
        for issue in issues[:5]:
            print(f"      - {issue}")
        errors.extend(issues)
    else:
        print("   ✓ All variance values valid")

    # Summary
    print("\n" + "=" * 80)
    if errors:
        print(f"✗ VALIDITY CHECK FAILED ({len(errors)} errors)")
    else:
        print("✓ VALIDITY CHECK PASSED")
    print("=" * 80)
    print()

    return len(errors) == 0


if __name__ == '__main__':
    qtree = load_quadtree()
    if qtree:
        analyze_tree(qtree)
        is_valid = check_tree_validity(qtree)

        if is_valid:
            print("Tree is valid and ready for visualization!")
        else:
            print("WARNING: Tree has issues - visualization may be incorrect")
