# step2_build_maps.py

import os
from PIL import Image
import numpy as np

# 1) Define paths
INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))
HORIZ_PATH   = os.path.join(PROJECT_ROOT, "horizontal_tunnel.png")
VERT_PATH    = os.path.join(PROJECT_ROOT, "vertical_tunnel.png")

# 2) Load each image as RGB array
horiz_arr = np.array(Image.open(HORIZ_PATH).convert("RGB"))
vert_arr  = np.array(Image.open(VERT_PATH).convert("RGB"))
H, W, _   = horiz_arr.shape

def build_tunnel_map(tarr: np.ndarray) -> dict[tuple[int,int], tuple[int,int]]:
    """
    For a tunnel‐bitmap array tarr of shape (H, W, 3), return a dict that
    maps each non‐black coordinate → its partner coordinate.
    """
    color_to_positions = {}
    Ht, Wt, _ = tarr.shape

    # a) Group each non‐black pixel by its RGB color
    for r in range(Ht):
        for c in range(Wt):
            rgb = tuple(int(x) for x in tarr[r, c])
            if rgb != (0, 0, 0):
                color_to_positions.setdefault(rgb, []).append((r, c))

    # b) Each color must appear exactly twice. Build the two‐way map.
    tunnel_map = {}
    for color, positions in color_to_positions.items():
        if len(positions) != 2:
            raise ValueError(f"Color {color} appears {len(positions)} times (expected 2).")
        (r1, c1), (r2, c2) = positions
        tunnel_map[(r1, c1)] = (r2, c2)
        tunnel_map[(r2, c2)] = (r1, c1)

    return tunnel_map

horizontal_map = build_tunnel_map(horiz_arr)
vertical_map   = build_tunnel_map(vert_arr)

print("STEP 2: Built wormhole maps")
print(f"  Horizontal‐tunnel endpoints: {len(horizontal_map)}")
print(f"    → That means {len(horizontal_map)//2} distinct pairs.")
print(f"  Vertical‐tunnel endpoints: {len(vertical_map)}")
print(f"    → That means {len(vertical_map)//2} distinct pairs.")

# (Optional) Print out the actual pairs (only if there are few)
if len(horizontal_map)//2 <= 10:
    print("\n  Horizontal pairs:")
    seen = set()
    for src, dst in horizontal_map.items():
        if (src, dst) not in seen and (dst, src) not in seen:
            print(f"    {src} ↔ {dst}")
            seen.add((src, dst))
            seen.add((dst, src))

if len(vertical_map)//2 <= 10:
    print("\n  Vertical pairs:")
    seen = set()
    for src, dst in vertical_map.items():
        if (src, dst) not in seen and (dst, src) not in seen:
            print(f"    {src} ↔ {dst}")
            seen.add((src, dst))
            seen.add((dst, src))

print(len(horizontal_map))
print(len(vertical_map))