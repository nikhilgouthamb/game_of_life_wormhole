# ─────────── src/test_horizontal.py ──────────────────────────────────────────
import numpy as np

# We’re testing exactly the 8×12 grid with horizontal tunnels:
#   A2 ↔ F6   (i.e. (row=1,col=0) ↔ (row=5,col=5))
#   B2 ↔ G6   (i.e. (row=1,col=1) ↔ (row=5,col=6))
# No vertical tunnels in this test, so leave that empty.

height, width = 12, 8
horizontal_map = {
    (1, 0): (5, 5),
    (5, 5): (1, 0),
    (1, 1): (5, 6),
    (5, 6): (1, 1),
}
vertical_map = {}  # not used in these tests

PRECEDENCE = ["top", "right", "bottom", "left"]  # for diagonals

def get_cardinal_neighbor(r: int, c: int, dr: int, dc: int):
    H, W = height, width
    nr, nc = r + dr, c + dc
    if not (0 <= nr < H and 0 <= nc < W):
        return None

    # Horizontal tunnels: teleport and stop
    if dc != 0 and (nr, nc) in horizontal_map:
        return horizontal_map[(nr, nc)]
    # Vertical tunnels: none exist here, so normal neighbor
    return (nr, nc)

def get_diagonal_neighbor(r: int, c: int, dr: int, dc: int):
    H, W = height, width
    orth1 = (r + dr, c)      # vertical leg
    orth2 = (r, c + dc)      # horizontal leg

    is1 = (0 <= orth1[0] < H and 0 <= orth1[1] < W)
    is2 = (0 <= orth2[0] < H and 0 <= orth2[1] < W)
    orth1_is_vwh = False  # no vertical tunnels in this test
    orth2_is_hwh = is2 and (orth2 in horizontal_map)

    # Case A: neither leg hits a tunnel
    if not orth1_is_vwh and not orth2_is_hwh:
        if not is1:
            return None
        y1, x1 = orth1
        y2, x2 = y1, x1 + dc
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

    # Case B: orth1 is not a tunnel, orth2 is a horizontal tunnel
    if orth2_is_hwh and not orth1_is_vwh:
        # Step into orth2, teleport to partner, then step vertically
        y1, x1 = horizontal_map[orth2]
        y2, x2 = y1 + dr, x1
        if not (0 <= y2 < H and 0 <= x2 < W):
            return None
        return (y2, x2)

    # (No Case C or D for vertical here, since there are no vertical tunnels.)

    return None

# ─── Run the six horizontal bullets and check their results ───────────────────
tests = [
    ("A2 right",         (1, 0),  (0, +1), (5,  6)),  # A2→B2(tunnel→G6)
    ("B2 left",          (1, 1),  (0, -1), (5,  5)),  # B2→A2(tunnel→F6)
    ("G6 left",          (5, 6),  (0, -1), (1,  0)),  # G6→F6(tunnel→A2)
    ("F6 right",         (5, 5),  (0, +1), (1,  1)),  # F6→G6(tunnel→B2)
    ("A2 bottom-right",  (1, 0),  (+1, +1), (6, 6)),  # diag: right first→B2(tunnel→G6) then down→G7
    ("B2 bottom-left",   (1, 1),  (+1, -1), (6, 5)),  # diag: left first→A2(tunnel→F6) then down→F7
]

print("\n── Horizontal‐Tunnel Neighbor Tests ─────────────────────────────────\n")
for desc, (r, c), (dy, dx), expected in tests:
    if abs(dy) == 1 and abs(dx) == 1:
        actual = get_diagonal_neighbor(r, c, dy, dx)
    else:
        actual = get_cardinal_neighbor(r, c, dy, dx)
    result = "OK" if actual == expected else "FAIL"
    print(f"{desc:<20} → actual {actual}, expected {expected}, {result}")