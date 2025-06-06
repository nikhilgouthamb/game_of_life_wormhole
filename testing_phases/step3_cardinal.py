# step3_cardinal.py

import os
from typing import Optional, Tuple
from PIL import Image
import numpy as np

# We assume horizontal_map and vertical_map already exist—so let’s load them again:
INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))
HORIZ_PATH   = os.path.join(PROJECT_ROOT, "horizontal_tunnel.png")
VERT_PATH    = os.path.join(PROJECT_ROOT, "vertical_tunnel.png")

horiz_arr  = np.array(Image.open(HORIZ_PATH).convert("RGB"))
vert_arr   = np.array(Image.open(VERT_PATH).convert("RGB"))
H, W, _    = horiz_arr.shape

def build_tunnel_map(tarr: np.ndarray) -> dict[Tuple[int,int], Tuple[int,int]]:
    color_to_positions = {}
    Ht, Wt, _ = tarr.shape
    for r in range(Ht):
        for c in range(Wt):
            rgb = tuple(int(x) for x in tarr[r, c])
            if rgb != (0, 0, 0):
                color_to_positions.setdefault(rgb, []).append((r, c))

    tunnel_map = {}
    for _, positions in color_to_positions.items():
        (r1, c1), (r2, c2) = positions
        tunnel_map[(r1, c1)] = (r2, c2)
        tunnel_map[(r2, c2)] = (r1, c1)
    return tunnel_map

horizontal_map = build_tunnel_map(horiz_arr)
vertical_map   = build_tunnel_map(vert_arr)

def get_cardinal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[Tuple[int,int]]:
    """
    Return the single neighbor of (r,c) when moving by (dr,dc) in one of the
    four cardinal directions: (dr,dc) ∈ {(-1,0),(+1,0),(0,-1),(0,+1)}.
    If that move goes off-grid or is not purely vertical/horizontal, return None.

    Vertical‐tunnel rules (dr != 0, dc == 0):
      A) If (r,c) itself is a vertical‐tunnel endpoint:
         1) Teleport to vertical_map[(r,c)]
         2) Carry one more step in the same vertical direction dr
            → (partner_row + dr, partner_col)
         3) If that is off-grid, return None; otherwise return it.
      B) Otherwise (starting cell not a tunnel), let (nr,nc) = (r+dr, c).
         1) If (nr,nc) is off-grid, return None
         2) If (nr,nc) is a vertical‐tunnel endpoint, teleport to vertical_map[(nr,nc)]
            and STOP (no extra carry). Return that partner.
         3) Otherwise, return (nr,nc).

    Horizontal‐tunnel rules (dr == 0, dc != 0):
      C) If (r,c) itself is a horizontal‐tunnel endpoint:
         1) Teleport to horizontal_map[(r,c)]
         2) Carry one more step in the same horizontal direction dc
            → (partner_row, partner_col + dc)
         3) If that is off-grid, return None; otherwise return it.
      D) Otherwise (starting cell not a tunnel), let (nr,nc) = (r, c+dc).
         1) If (nr,nc) is off-grid, return None
         2) If (nr,nc) is a horizontal‐tunnel endpoint, teleport to horizontal_map[(nr,nc)]
            and STOP (no carry). Return that partner.
         3) Otherwise, return (nr,nc).

    For any other (dr,dc) combination, return None.
    """
    # 0) Bounds check for starting cell (just to be safe)
    if r < 0 or r >= H or c < 0 or c >= W:
        return None

    # ─── Case A: Vertical move, starting on a vertical endpoint? ─────────────────
    if dr != 0 and dc == 0 and (r, c) in vertical_map:
        # 1) Teleport off the starting cell
        vr, vc = vertical_map[(r, c)]
        # 2) Carry one more step in the same vertical direction
        nr2, nc2 = vr + dr, vc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # ─── Case B: Vertical move, stepping into a vertical endpoint? ──────────────
    if dr != 0 and dc == 0:
        nr, nc = r + dr, c
        # 1) Off-grid?
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        # 2) If target is a vertical endpoint, teleport & STOP
        if (nr, nc) in vertical_map:
            return vertical_map[(nr, nc)]
        # 3) Otherwise, return the ordinary neighbor
        return (nr, nc)

    # ─── Case C: Horizontal move, starting on a horizontal endpoint? ────────────
    if dr == 0 and dc != 0 and (r, c) in horizontal_map:
        # 1) Teleport off the starting cell
        hr, hc = horizontal_map[(r, c)]
        # 2) Carry one more step in the same horizontal direction
        nr2, nc2 = hr, hc + dc
        if nr2 < 0 or nr2 >= H or nc2 < 0 or nc2 >= W:
            return None
        return (nr2, nc2)

    # ─── Case D: Horizontal move, stepping into a horizontal endpoint? ───────────
    if dr == 0 and dc != 0:
        nr, nc = r, c + dc
        # 1) Off-grid?
        if nr < 0 or nr >= H or nc < 0 or nc >= W:
            return None
        # 2) If target is a horizontal endpoint, teleport & STOP
        if (nr, nc) in horizontal_map:
            return horizontal_map[(nr, nc)]
        # 3) Otherwise, return the ordinary neighbor
        return (nr, nc)

    # Any other (dr,dc) combination not purely cardinal → no neighbor
    return None

