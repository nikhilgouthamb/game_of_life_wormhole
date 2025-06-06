

## `game_of_life_wormhole.py` (Fully Commented)


import os
from typing import Optional, Tuple, List
from PIL import Image
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Build Tunnel Maps
# ─────────────────────────────────────────────────────────────────────────────

INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))

# Paths to the two tunnel‐bitmap PNGs and the starting grid image
HORIZ_PATH     = os.path.join(PROJECT_ROOT, "horizontal_tunnel.png")
VERT_PATH      = os.path.join(PROJECT_ROOT, "vertical_tunnel.png")
START_POS_PATH = os.path.join(PROJECT_ROOT, "starting_position.png")

# Load each tunnel image as an H×W×3 NumPy array
horiz_arr = np.array(Image.open(HORIZ_PATH).convert("RGB"))
vert_arr  = np.array(Image.open(VERT_PATH).convert("RGB"))
H, W, _   = horiz_arr.shape
# (We assume `starting_position.png` has the same height/width.)

def build_tunnel_map(arr: np.ndarray) -> dict[tuple[int,int], tuple[int,int]]:
    """
    Build a mapping of warp‐endpoints from a color‐coded tunnel image.

    1) For each RGB color (excluding pure black), collect all pixels (r,c) of that color.
    2) If a color appears exactly 2×, those two coordinates become the tunnel endpoints.
    3) If a color appears >2× (a thick border), find the pair of pixels with the maximum
       squared‐Euclidean distance.  Those two become the endpoints.
    4) Return a dict mapping each endpoint → its partner.

    Returns:
        tunnel_map: { (r1,c1): (r2,c2), (r2,c2): (r1,c1) }
    """
    Ht, Wt, _ = arr.shape

    # Step 1: Group all non‐black pixels by their RGB value
    color_to_positions: dict[tuple[int,int,int], List[tuple[int,int]]] = {}
    for r in range(Ht):
        for c in range(Wt):
            rgb = tuple(int(x) for x in arr[r, c])  # Convert pixel to (R,G,B)
            if rgb != (0, 0, 0):  # Skip black pixels
                color_to_positions.setdefault(rgb, []).append((r, c))

    tunnel_map: dict[tuple[int,int], tuple[int,int]] = {}

    # Step 2: For each color, determine the two “endpoints”
    for rgb, positions in color_to_positions.items():
        if len(positions) < 2:
            raise ValueError(
                f"Color {rgb} appears only {len(positions)} times (expected ≥ 2)."
            )

        # If exactly 2 positions, they are the endpoints
        if len(positions) == 2:
            (r1, c1), (r2, c2) = positions
            tunnel_map[(r1, c1)] = (r2, c2)
            tunnel_map[(r2, c2)] = (r1, c1)
            continue

        # Otherwise, find the pair of positions farthest apart
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

        # Sanity check: we must have found two farthest‐apart pixels
        if end1 is None or end2 is None:
            raise RuntimeError(f"Failed to pick endpoints for color {rgb}.")

        tunnel_map[end1] = end2
        tunnel_map[end2] = end1

    return tunnel_map

# Build both horizontal and vertical warp‐maps
horizontal_map = build_tunnel_map(horiz_arr)
vertical_map   = build_tunnel_map(vert_arr)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 & 3: Cardinal Neighbor with Wormhole Logic
# ─────────────────────────────────────────────────────────────────────────────

def get_cardinal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[Tuple[int,int]]:
    """
    Return the warped neighbor of cell (r,c) in a purely cardinal direction (dr,dc).
    (dr,dc) must be one of: (-1,0), (+1,0), (0,-1), (0,+1).  Otherwise, return None.

    Logic:
    1) Bounds‐check (r,c). If out‐of‐range, return None.

    Vertical moves (dr != 0, dc == 0):
      A) If (r,c) is in vertical_map (warp endpoint):
         - Teleport to (vr,vc) = vertical_map[(r,c)].
         - Carry one more step: return (vr + dr, vc) if in‐bounds; else None.
      B) Otherwise, let (nr,nc) = (r + dr, c):
         - If out‐of‐bounds → None.
         - If (nr,nc) in vertical_map → teleport to that partner, return partner.
         - Else return (nr,nc) normally.

    Horizontal moves (dr == 0, dc != 0):
      C) If (r,c) is in horizontal_map:
         - Teleport to (hr,hc) = horizontal_map[(r,c)].
         - Carry one more step: return (hr, hc + dc) if in‐bounds; else None.
      D) Otherwise, let (nr,nc) = (r, c + dc):
         - If out‐of‐bounds → None.
         - If (nr,nc) in horizontal_map → teleport & return partner.
         - Else return (nr,nc).

    Any other (dr,dc) combination → return None.
    """
    # 0) Bounds check for (r,c)
    if r < 0 or r >= H or c < 0 or c >= W:
        return None

    # ─── Case A: vertical move AND (r,c) is a vertical tunnel endpoint
    if dr != 0 and dc == 0 and (r, c) in vertical_map:
        # Teleport off (r,c)
        vr, vc = vertical_map[(r, c)]
        # Carry one more step vertically
        nr2, nc2 = vr + dr, vc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # ─── Case B: vertical move stepping into a tunnel
    if dr != 0 and dc == 0:
        nr, nc = r + dr, c
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        if (nr, nc) in vertical_map:
            # Teleport & stop
            return vertical_map[(nr, nc)]
        return (nr, nc)

    # ─── Case C: horizontal move AND (r,c) is a horizontal tunnel endpoint
    if dr == 0 and dc != 0 and (r, c) in horizontal_map:
        hr, hc = horizontal_map[(r, c)]
        nr2, nc2 = hr, hc + dc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # ─── Case D: horizontal move stepping into a tunnel
    if dr == 0 and dc != 0:
        nr, nc = r, c + dc
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        if (nr, nc) in horizontal_map:
            # Teleport & stop
            return horizontal_map[(nr, nc)]
        return (nr, nc)

    # Not a valid cardinal move
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Diagonal Neighbor with Precedence (always both legs)
# ─────────────────────────────────────────────────────────────────────────────

PRECEDENCE = ["top", "right", "bottom", "left"]

def get_diagonal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[Tuple[int,int]]:
    """
    Return the warped neighbor of cell (r,c) when moving one step diagonally (dr,dc).
    (dr,dc) must be in {(-1,-1),(-1,+1),(+1,-1),(+1,+1)}.
    Always perform both cardinal sub‐steps; no early stop.

    Algorithm:
    1) orth1 = (r + dr,  c)        # if we did vertical sub‐step first
       orth2 = (r,        c + dc)   # if we did horizontal sub‐step first
    2) Check if orth1 is a vertical‐tunnel endpoint, orth2 is a horizontal‐tunnel 
       endpoint (and ensure they’re in‐bounds).
    3) If both are tunnel endpoints, compare directions:
       - orth1_dir = "top"  if dr == -1 else "bottom"
       - orth2_dir = "left" if dc == -1 else "right"
       Choose first_leg according to which direction has smaller index in PRECEDENCE.
       Otherwise, if only orth1 is a tunnel → do vertical first; elif only orth2 is a 
       tunnel → do horizontal first; else do vertical first by default.
    4) Call get_cardinal_neighbor(r, c, dr1, dc1) → inter (or None).
       If inter is None, return None.
    5) Call get_cardinal_neighbor(inter_r, inter_c, dr2, dc2) → final (or None).
       Return final.
    """
    # 1) Two possible orthogonal candidates
    orth1 = (r + dr,   c    )
    orth2 = (r,       c + dc)

    # 2) Check in‐bounds and tunnel‐endpoint status
    in1 = (0 <= orth1[0] < H and 0 <= orth1[1] < W)
    in2 = (0 <= orth2[0] < H and 0 <= orth2[1] < W)

    orth1_is_vwh = in1 and (orth1 in vertical_map)
    orth2_is_hwh = in2 and (orth2 in horizontal_map)

    # 3) Decide leg order by precedence
    if orth1_is_vwh and orth2_is_hwh:
        orth1_dir = "top" if dr == -1 else "bottom"
        orth2_dir = "left" if dc == -1 else "right"
        if PRECEDENCE.index(orth1_dir) < PRECEDENCE.index(orth2_dir):
            first_leg  = (dr,   0)  # vertical first
            second_leg = (0,    dc)
        else:
            first_leg  = (0,    dc)  # horizontal first
            second_leg = (dr,   0)
    elif orth1_is_vwh:
        first_leg  = (dr,   0)
        second_leg = (0,    dc)
    elif orth2_is_hwh:
        first_leg  = (0,    dc)
        second_leg = (dr,   0)
    else:
        # Neither leg lands on a tunnel endpoint → vertical first
        first_leg  = (dr,   0)
        second_leg = (0,    dc)

    # 4) Perform first cardinal sub‐step
    inter = get_cardinal_neighbor(r, c, first_leg[0], first_leg[1])
    if inter is None:
        return None
    r1, c1 = inter

    # 5) Perform second sub‐step unconditionally
    final = get_cardinal_neighbor(r1, c1, second_leg[0], second_leg[1])
    return final


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Precompute All 8 Neighbors for Every Cell
# ─────────────────────────────────────────────────────────────────────────────

CARDINAL_OFFSETS = [(-1,  0), (+1,  0), (0, -1), (0, +1)]
DIAGONAL_OFFSETS = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

# Allocate H×W lists of neighbor‐coordinates
neighbors: list[list[Tuple[int,int]]] = [[[] for _ in range(W)] for _ in range(H)]
for rr in range(H):
    for cc in range(W):
        # (a) Cardinal neighbors
        for (dr, dc) in CARDINAL_OFFSETS:
            nbr = get_cardinal_neighbor(rr, cc, dr, dc)
            if nbr is not None:
                neighbors[rr][cc].append(nbr)

        # (b) Diagonal neighbors
        for (dr, dc) in DIAGONAL_OFFSETS:
            nbr = get_diagonal_neighbor(rr, cc, dr, dc)
            if nbr is not None:
                neighbors[rr][cc].append(nbr)

# At this point, neighbors[r][c] is a list of valid neighbor‐coordinates (0–8 items)


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Run the Game‐of‐Life Update & Save Output Frames
# ─────────────────────────────────────────────────────────────────────────────

# (6a) Load the initial grid (white=alive, black=dead)
start_img = Image.open(START_POS_PATH).convert("RGB")
start_pixels = np.array(start_img)  # shape (H, W, 3)

grid0 = np.zeros((H, W), dtype=np.uint8)
# Any pixel exactly [255,255,255] is alive; else dead
grid0[np.all(start_pixels == [255, 255, 255], axis=2)] = 1

def step(grid: np.ndarray) -> np.ndarray:
    """
    Perform one generation of Conway’s Game of Life on `grid` using
    the precomputed `neighbors`.  Return the next‐generation grid.

    Rules (for each cell):
      - Count how many of its neighbors are alive.
      - If the cell is alive:
          – It stays alive if the count is 2 or 3; otherwise it dies.
        If the cell is dead:
          – It becomes alive if the count is exactly 3; otherwise remains dead.
    """
    new_grid = np.zeros_like(grid)
    for rr in range(H):
        for cc in range(W):
            alive = (grid[rr, cc] == 1)
            count = 0
            # Sum up how many neighbors are alive
            for (nr, nc) in neighbors[rr][cc]:
                if grid[nr, nc] == 1:
                    count += 1

            # Apply standard Conway rules
            if alive:
                new_grid[rr, cc] = 1 if (2 <= count <= 3) else 0
            else:
                new_grid[rr, cc] = 1 if (count == 3) else 0

    return new_grid

# (6c) Iterate through frames 1, 10, 100, 1000
targets = [1, 10, 100, 1000]
results: dict[int, np.ndarray] = {}
grid = grid0.copy()
max_iter = max(targets)

for it in range(1, max_iter + 1):
    grid = step(grid)
    if it in targets:
        results[it] = grid.copy()

# (6d) Save each result as a PNG (white=alive, black=dead)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

for it, g in results.items():
    out_img = np.zeros((H, W, 3), dtype=np.uint8)
    out_img[g == 1] = [255, 255, 255]  # white for alive
    fname = os.path.join(OUTPUT_DIR, f"{it}.png")
    Image.fromarray(out_img).save(fname)
    live_count = np.sum(g)
    print(f"Iteration {it}: saved '{it}.png' with {live_count} live cells.")

print("Step 6 complete: all target frames are in 'outputs/'.")