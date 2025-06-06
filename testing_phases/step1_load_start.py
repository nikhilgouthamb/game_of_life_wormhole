# step1_load_start.py

import os
from PIL import Image
import numpy as np

# 1) Locate the starting image:
INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))       # …/game_of_life_wormhole/src
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))   # …/game_of_life_wormhole
START_IMG    = os.path.join(PROJECT_ROOT, "starting_position.png")

# 2) Open it as RGB and convert to a NumPy array:
img = Image.open(START_IMG).convert("RGB")
W, H = img.width, img.height
arr = np.array(img)   # shape (H, W, 3)

# 3) Build a binary (H × W) grid0: white=(255,255,255) → 1, else 0
grid0 = np.zeros((H, W), dtype=np.uint8)
grid0[np.all(arr == [255, 255, 255], axis=2)] = 1

# 4) Print some diagnostics:
print("STEP 1: Loaded starting_position.png")
print(f"Dimensions: H = {H}, W = {W}")
print(f"Total alive cells: {grid0.sum()} out of {H*W} (should match the number of white pixels)")

# 5) (Optional) print the coordinates of the alive cells (if not too many):
coords = list(zip(*np.where(grid0 == 1)))
print("is ")
if len(coords) <= 50:
    print("Alive‐cell coordinates (row, col):")
    for (r, c) in coords:
        print(f"  ({r}, {c})")