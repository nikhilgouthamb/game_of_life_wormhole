# ─────────── src/test_vertical.py ────────────────────────────────────────────
import os
import numpy as np
from PIL import Image

# Hard‐code the 8×12 example grid (A–H by 1–12) for just testing vertical tunnels
height, width = 12, 8

# Define exactly the two vertical tunnel pairs from your example:
#   C2 ↔ G7  and  C3 ↔ G6
# In zero‐based (row, col) that is:
#   C2 = (1, 2),  G7 = (6, 6)
#   C3 = (2, 2),  G6 = (5, 6)
vertical_map = {
    (1, 2): (6, 6),
    (6, 6): (1, 2),
    (2, 2): (5, 6),
    (5, 6): (2, 2),
}

# We do not need a horizontal_map for this test, so leave it empty:
horizontal_map = {}

PRECEDENCE = ["top", "right", "bottom", "left"]

def get_cardinal_neighbor(r: int, c: int, dr: int, dc: int):
    """
    Exactly the same logic as in game_of_life_wormhole.py:
    - If vertical move (dr != 0) into a vertical_map key, teleport and extra‐step.
    - If horizontal move (dc != 0) into a horizontal_map key, teleport and stop (not used here).
    - Else return the stepped‐into cell.
    """
    H, W = height, width
    nr, nc = r + dr, c + dc
    if not (0 <= nr < H and 0 <= nc < W):
        return None

    # Vertical tunnel
    if dr != 0 and (nr, nc) in vertical_map:
        # Teleport to partner
        nr, nc = vertical_map[(nr, nc)]
        # Then step one more in same vertical direction
        nr2, nc2 = nr + dr, nc
        if not (0 <= nr2 < H and 0 <= nc2 < W):
            return None
        return (nr2, nc2)

    # Horizontal tunnel (not used in this test)
    if dc != 0 and (nr, nc) in horizontal_map:
        return horizontal_map[(nr, nc)]

    return (nr, nc)

def get_diagonal_neighbor(r: int, c: int, dr: int, dc: int):
    """
    Exactly the same diagonal logic as in game_of_life_wormhole.py,
    but only checking vertical_map (no horizontal_map here).
    We include it for completeness, but we won’t test it in this script.
    """
    H, W = height, width
    orth1 = (r + dr, c)
    orth2 = (r, c + dc)
    is1 = 0 <= orth1[0] < H and 0 <= orth1[1] < W
    is2 = 0 <= orth2[0] < H and 0 <= orth2[1] < W
    orth1_is_vwh = is1 and (orth1 in vertical_map)
    orth2_is_hwh = is2 and (orth2 in horizontal_map)

    if not orth1_is_vwh and not orth2_is_hwh:
        if not is1:
            return None
        y1, x1 = orth1
        y2, x2 = y1, x1 + dc
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

    if orth1_is_vwh and not orth2_is_hwh:
        y1, x1 = vertical_map[orth1]
        y2, x2 = y1, x1 + dc
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

    if orth2_is_hwh and not orth1_is_vwh:
        y1, x1 = horizontal_map[orth2]
        y2, x2 = y1 + dr, x1
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

    orth1_dir = "top" if dr == -1 else "bottom"
    orth2_dir = "left" if dc == -1 else "right"
    if PRECEDENCE.index(orth1_dir) < PRECEDENCE.index(orth2_dir):
        y1, x1 = vertical_map[orth1]
        y2, x2 = y1, x1 + dc
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)
    else:
        y1, x1 = horizontal_map[orth2]
        y2, x2 = y1 + dr, x1
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

# ─── 2) Test all six vertical‐tunnel bullets ───────────────────────────────────
tests = [
    # (description, (r,c), (dr,dc), expected_output)
    ("C2 bottom",   (1, 2), (+1, 0), (6, 6)),  # C2→C3(tunnel→G6)→G7
    ("C3 top",      (2, 2), (-1, 0), (5, 6)),  # C3→C2(tunnel→G7)→G6
    ("G6 bottom",   (5, 6), (+1, 0), (2, 2)),  # G6→G7(tunnel→C2)→C3
    ("G7 top",      (6, 6), (-1, 0), (1, 2)),  # G7→G6(tunnel→C3)→C2
    ("C2 bottom-right", (1, 2), (+1, +1), (6, 7)),  # diagonal
    ("C3 top-right",    (2, 2), (-1, +1), (5, 7)),  # diagonal
]

print("\n── Vertical‐Tunnel Neighbor Tests ─────────────────────────────────\n")
for desc, (r, c), (dy, dx), expected in tests:
    if abs(dy) == 1 and abs(dx) == 1:
        actual = get_diagonal_neighbor(r, c, dy, dx)
    else:
        actual = get_cardinal_neighbor(r, c, dy, dx)
    print(f"{desc:<20} → actual {actual}, expected {expected}, {'OK' if actual == expected else 'FAIL'}")