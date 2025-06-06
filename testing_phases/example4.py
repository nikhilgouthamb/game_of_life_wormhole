

import os
from typing import Optional, Tuple, List
from PIL import Image
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Re‐import or re‐define Steps 1–5 (tunnel maps, neighbor functions, and precomputed `neighbors`)
# ─────────────────────────────────────────────────────────────────────────────

INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))

# (1) Paths to tunnel bitmaps and starting position
HORIZ_PATH        = os.path.join(PROJECT_ROOT, "horizontal_tunnel.png")
VERT_PATH         = os.path.join(PROJECT_ROOT, "vertical_tunnel.png")
START_POS_PATH    = os.path.join(PROJECT_ROOT, "starting_position.png")

# (2) Load tunnel images and build tunnel maps
horiz_arr = np.array(Image.open(HORIZ_PATH).convert("RGB"))
vert_arr  = np.array(Image.open(VERT_PATH).convert("RGB"))
H, W, _   = horiz_arr.shape  # assume starting_position.png is also H×W

def build_tunnel_map(arr: np.ndarray) -> dict[tuple[int,int], tuple[int,int]]:
    """
    Given an H×W×3 RGB array `arr`, group all non-black pixels by color.
    For each color‐group of size ≥ 2, find the two pixels that are farthest
    apart (max squared distance).  Those two become the tunnel endpoints:
      endpoint1 ↔ endpoint2.

    Returns a dict mapping each of those two endpoints to its partner.
    """
    Ht, Wt, _ = arr.shape

    # 1) Collect all positions for each non-black RGB value
    color_to_positions: dict[tuple[int,int,int], list[tuple[int,int]]] = {}
    for r in range(Ht):
        for c in range(Wt):
            rgb = tuple(int(x) for x in arr[r, c])
            if rgb != (0, 0, 0):
                color_to_positions.setdefault(rgb, []).append((r, c))

    tunnel_map: dict[tuple[int,int], tuple[int,int]] = {}

    # 2) For each color, find the pair of positions with maximum squared distance
    for rgb, positions in color_to_positions.items():
        if len(positions) < 2:
            raise ValueError(
                f"Color {rgb} appears only {len(positions)} times (expected at least 2)."
            )

        # If exactly 2 positions, they are our endpoints:
        if len(positions) == 2:
            (r1, c1), (r2, c2) = positions
            tunnel_map[(r1, c1)] = (r2, c2)
            tunnel_map[(r2, c2)] = (r1, c1)
            continue

        # Otherwise, find the farthest‐apart pair
        max_d2 = -1
        end1 = end2 = None
        for i in range(len(positions)):
            r1, c1 = positions[i]
            for j in range(i + 1, len(positions)):
                r2, c2 = positions[j]
                d2 = (r1 - r2)**2 + (c1 - c2)**2
                if d2 > max_d2:
                    max_d2 = d2
                    end1, end2 = (r1, c1), (r2, c2)

        # If something went wrong, sanity check
        if end1 is None or end2 is None:
            raise RuntimeError(f"Failed to pick endpoints for color {rgb}.")

        tunnel_map[end1] = end2
        tunnel_map[end2] = end1

    return tunnel_map

horizontal_map = build_tunnel_map(horiz_arr)
vertical_map   = build_tunnel_map(vert_arr)

# (3) Step 3: get_cardinal_neighbor
def get_cardinal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[Tuple[int,int]]:
    # Bounds check
    if r < 0 or r >= H or c < 0 or c >= W:
        return None

    # Case A: vertical move starting on vertical tunnel endpoint
    if dr != 0 and dc == 0 and (r, c) in vertical_map:
        vr, vc = vertical_map[(r, c)]
        nr2, nc2 = vr + dr, vc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # Case B: vertical move stepping into vertical endpoint
    if dr != 0 and dc == 0:
        nr, nc = r + dr, c
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        if (nr, nc) in vertical_map:
            return vertical_map[(nr, nc)]
        return (nr, nc)

    # Case C: horizontal move starting on horizontal tunnel endpoint
    if dr == 0 and dc != 0 and (r, c) in horizontal_map:
        hr, hc = horizontal_map[(r, c)]
        nr2, nc2 = hr, hc + dc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # Case D: horizontal move stepping into horizontal endpoint
    if dr == 0 and dc != 0:
        nr, nc = r, c + dc
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        if (nr, nc) in horizontal_map:
            return horizontal_map[(nr, nc)]
        return (nr, nc)

    # Otherwise not a valid cardinal move
    return None

# (4) Step 4: get_diagonal_neighbor (always both legs)
PRECEDENCE = ["top", "right", "bottom", "left"]

def get_diagonal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[Tuple[int,int]]:
    orth1 = (r + dr,   c    )
    orth2 = (r,       c + dc)

    in1 = (0 <= orth1[0] < H and 0 <= orth1[1] < W)
    in2 = (0 <= orth2[0] < H and 0 <= orth2[1] < W)

    orth1_is_vwh = in1 and (orth1 in vertical_map)
    orth2_is_hwh = in2 and (orth2 in horizontal_map)

    if orth1_is_vwh and orth2_is_hwh:
        orth1_dir = "top" if dr == -1 else "bottom"
        orth2_dir = "left" if dc == -1 else "right"
        if PRECEDENCE.index(orth1_dir) < PRECEDENCE.index(orth2_dir):
            first_leg  = (dr,   0)
            second_leg = (0,    dc)
        else:
            first_leg  = (0,    dc)
            second_leg = (dr,   0)
    elif orth1_is_vwh:
        first_leg  = (dr,   0)
        second_leg = (0,    dc)
    elif orth2_is_hwh:
        first_leg  = (0,    dc)
        second_leg = (dr,   0)
    else:
        first_leg  = (dr,   0)
        second_leg = (0,    dc)

    inter = get_cardinal_neighbor(r, c, first_leg[0], first_leg[1])
    if inter is None:
        return None
    r1, c1 = inter

    final = get_cardinal_neighbor(r1, c1, second_leg[0], second_leg[1])
    return final

# (5) Step 5: Precompute neighbors[r][c]
CARDINAL_OFFSETS = [(-1,  0), (+1,  0), (0, -1), (0, +1)]
DIAGONAL_OFFSETS = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

neighbors: list[list[Tuple[int,int]]] = [[[] for _ in range(W)] for _ in range(H)]
for rr in range(H):
    for cc in range(W):
        for (dr, dc) in CARDINAL_OFFSETS:
            nbr = get_cardinal_neighbor(rr, cc, dr, dc)
            if nbr is not None:
                neighbors[rr][cc].append(nbr)
        for (dr, dc) in DIAGONAL_OFFSETS:
            nbr = get_diagonal_neighbor(rr, cc, dr, dc)
            if nbr is not None:
                neighbors[rr][cc].append(nbr)

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Run the Game‐of‐Life update and save outputs
# ─────────────────────────────────────────────────────────────────────────────

# (6a) Load starting_position.png into a binary grid0 (alive=1, dead=0)
start_img = Image.open(START_POS_PATH).convert("RGB")
start_pixels = np.array(start_img)  # shape (H, W, 3)

grid0 = np.zeros((H, W), dtype=np.uint8)
grid0[np.all(start_pixels == [255, 255, 255], axis=2)] = 1

# (6b) Define a single‐step update using precomputed neighbors
def step(grid: np.ndarray) -> np.ndarray:
    new_grid = np.zeros_like(grid)
    for rr in range(H):
        for cc in range(W):
            alive = (grid[rr, cc] == 1)
            count = 0
            for (nr, nc) in neighbors[rr][cc]:
                if grid[nr, nc] == 1:
                    count += 1
            if alive:
                new_grid[rr, cc] = 1 if (2 <= count <= 3) else 0
            else:
                new_grid[rr, cc] = 1 if (count == 3) else 0
    return new_grid

# (6c) Run the simulation for iterations 1, 10, 100, 1000
targets = [1, 10, 100, 1000]
results: dict[int, np.ndarray] = {}
grid = grid0.copy()
max_iter = max(targets)

for it in range(1, max_iter + 1):
    grid = step(grid)
    if it in targets:
        results[it] = grid.copy()

# (6d) Save each result as a PNG (alive=white, dead=black) in “outputs/”
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

for it, g in results.items():
    out_img = np.zeros((H, W, 3), dtype=np.uint8)
    out_img[g == 1] = [255, 255, 255]
    fname = os.path.join(OUTPUT_DIR, f"{it}.png")
    Image.fromarray(out_img).save(fname)
    live_count = np.sum(g)
    print(f"Iteration {it}: saved '{it}.png' with {live_count} live cells.")

print("Step 6 complete: all target frames are in 'outputs/'.")