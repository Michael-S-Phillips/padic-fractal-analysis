#!/bin/bash

# Master script to build, inspect, and visualize the p-adic quadtree

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "P-ADIC QUADTREE: BUILD, INSPECT, AND VISUALIZE"
echo "================================================================================"
echo

# Step 1: Build and save quadtree
echo "STEP 1: Build and save quadtree"
echo "------------------------------------------------------------------------"
python3 01_build_and_save_quadtree.py
echo

# Step 2: Inspect tree
echo "STEP 2: Inspect quadtree structure"
echo "------------------------------------------------------------------------"
python3 02_inspect_quadtree.py
echo

# Step 3: Visualize
echo "STEP 3: Visualize quadtree"
echo "------------------------------------------------------------------------"
python3 03_visualize_quadtree.py
echo

echo "================================================================================"
echo "✓ ALL STEPS COMPLETE"
echo "================================================================================"
