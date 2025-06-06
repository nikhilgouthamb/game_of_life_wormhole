# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Implement get_diagonal_neighbor(r, c, dr, dc)
# ─────────────────────────────────────────────────────────────────────────────

# step4_diagonal.py

import os
from typing import Optional, Tuple
from PIL import Image
import numpy as np

# Re‐load tunnel maps (you can also import from step3_cardinal if you modularized)
INPUT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(INPUT_DIR, ".."))
HORIZ_PATH   = os.path.join(PROJECT_ROOT, "horizontal_tunnel.png")
VERT_PATH    = os.path.join(PROJECT_ROOT, "vertical_tunnel.png")

horiz_arr = np.array(Image.open(HORIZ_PATH).convert("RGB"))
vert_arr  = np.array(Image.open(VERT_PATH).convert("RGB"))
H, W, _   = horiz_arr.shape

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

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: get_diagonal_neighbor(r, c, dr, dc)
# ─────────────────────────────────────────────────────────────────────────────

PRECEDENCE = ["top", "right", "bottom", "left"]

def get_diagonal_neighbor(r: int, c: int, dr: int, dc: int) -> Optional[tuple[int,int]]:
    """
    Given a cell (r,c) and a diagonal offset (dr,dc) ∈ {(-1,-1),(-1,+1),(+1,-1),(+1,+1)},
    return the single grid coordinate you land on after applying the GAme-of-Life
    tunnel rules.  Return None if you go off-grid at any point.

    Implementation steps (no special “stop on first teleport”):
      1) Define orth1 = (r + dr,   c    )   # vertical‐direction candidate
         Define orth2 = (r,       c + dc)   # horizontal‐direction candidate

      2) Check if orth1 is in vertical_map (i.e. if stepping (dr,0) hits a vertical tunnel).
         Check if orth2 is in horizontal_map (i.e. if stepping (0,dc) hits a horizontal tunnel).

      3) If both orth1 and orth2 are tunnel-pixels, compare their directions (“top” vs “right” etc.)
         using PRECEDENCE = ["top","right","bottom","left"].  Whichever appears earlier
         in that list is the leg you perform first.  Otherwise:
           • If only orth1 is a vertical tunnel endpoint → do vertical first.
           • Else if only orth2 is a horizontal tunnel endpoint → do horizontal first.
           • Else (neither is a tunnel endpoint) → default to vertical first.

      4) Call get_cardinal_neighbor(r, c, dr1, dc1) for the chosen first leg → “intermediate” (r1,c1) or None.
         If that returns None, end and return None.

      5) From (r1,c1), call get_cardinal_neighbor(r1, c1, dr2, dc2) for the second leg → final (r2,c2) or None.

      6) Return final (r2,c2) or None.
    """
    # 1) Build the two “orthogonal” candidate cells (zero-based)
    orth1 = (r + dr,   c    )   # candidate if we did the vertical sub-step first
    orth2 = (r,       c + dc)   # candidate if we did the horizontal sub-step first

    # 2) Check in-bounds and if they lie on tunnel endpoints
    in1 = (0 <= orth1[0] < H and 0 <= orth1[1] < W)
    in2 = (0 <= orth2[0] < H and 0 <= orth2[1] < W)

    orth1_is_vwh = in1 and (orth1 in vertical_map)
    orth2_is_hwh = in2 and (orth2 in horizontal_map)

    # 3) Decide which sub-step to perform first
    if orth1_is_vwh and orth2_is_hwh:
        # Both sub-steps land on tunnels → compare directions
        orth1_dir = "top" if dr == -1 else "bottom"
        orth2_dir = "left" if dc == -1 else "right"
        if PRECEDENCE.index(orth1_dir) < PRECEDENCE.index(orth2_dir):
            first_leg  = (dr,   0)
            second_leg = (0,    dc)
        else:
            first_leg  = (0,    dc)
            second_leg = (dr,   0)

    elif orth1_is_vwh:
        # Only vertical sub-step is a tunnel endpoint
        first_leg  = (dr,   0)
        second_leg = (0,    dc)

    elif orth2_is_hwh:
        # Only horizontal sub-step is a tunnel endpoint
        first_leg  = (0,    dc)
        second_leg = (dr,   0)

    else:
        # Neither is a tunnel endpoint → default to vertical first
        first_leg  = (dr,   0)
        second_leg = (0,    dc)

    # 4) Perform the first leg by calling get_cardinal_neighbor
    inter = get_cardinal_neighbor(r, c, first_leg[0], first_leg[1])
    if inter is None:
        return None
    r1, c1 = inter

    # 5) Perform the second leg from the intermediate result
    final = get_cardinal_neighbor(r1, c1, second_leg[0], second_leg[1])
    return final