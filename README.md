# Game of Life with Wormholes

A modified implementation of Conway's Game of Life that embeds "wormhole" tunnels into the grid.
Cells that move off a tunnel‐pixel are "teleported" to its paired endpoint, then continue (or stop) according to defined rules. This allows cells to "wrap" in nontrivial ways both horizontally and vertically.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [How It Works](#how-it-works)
   - [Step 1: Tunnel Mapping](#step-1-tunnel-mapping)
   - [Steps 2 & 3: Cardinal Moves with Wormholes](#steps-2--3-cardinal-moves-with-wormholes)
   - [Step 4: Diagonal Moves with Tunnel Precedence](#step-4-diagonal-moves-with-tunnel-precedence)
   - [Step 5: Precomputing All 8 Neighbors](#step-5-precomputing-all-8-neighbors-for-every-cell)
   - [Step 6: Running the Life Simulation](#step-6-running-the-life-simulation)
4. [Usage](#usage)
5. [Dependencies](#dependencies)
6. [Customization](#customization)
7. [License](#license)

## Project Overview

This repository simulates Conway's Game of Life on a finite grid that includes special "wormhole" tunnels. Instead of the usual toroidal wrap, certain pixel‐pairs (in `horizontal_tunnel.png` or `vertical_tunnel.png`) are connected:

- **Horizontal tunnels**: Each pair of same‐colored pixels in `horizontal_tunnel.png` forms an entry/exit. A cell stepping onto one of those pixels will instantly "teleport" to its paired pixel, then (if moving horizontally) carry one more column in that direction.
- **Vertical tunnels**: Each pair of same‐colored pixels in `vertical_tunnel.png` forms an entry/exit. A cell stepping onto one of those pixels will teleport to its pair, then (if moving vertically) carry one more row in that direction.

All eight neighbor lookups—up, down, left, right, and four diagonals—are modified to account for these wormholes. The standard Game of Life rules (underpopulation, survival, overpopulation, reproduction) then apply to that new "wrapped" neighborhood.

## Directory Structure

```
game_of_life_wormhole/
├── starting_position.png       # Initial live/dead pattern (white = alive, black = dead)
├── horizontal_tunnel.png       # Horizontal‐tunnel bitmap (same‐colored border → warp pair)
├── vertical_tunnel.png         # Vertical‐tunnel bitmap (same‐colored border → warp pair)
├── outputs/                    # (Generated) output frames: 1.png, 10.png, 100.png, 1000.png
└── src/
    └── game_of_life_wormhole.py  # Main Python script implementing Steps 1–6
```

### Key Files
- At the root level:
  - `starting_position.png` is a black‐and‐white image that encodes which cells start "alive" (white) versus "dead" (black).
  - `horizontal_tunnel.png` and `vertical_tunnel.png` are color‐encoded images. Every non‐black pixel of a particular RGB color appears at least twice; the two farthest‐apart same‐color pixels form a wormhole pair.
- Inside `src/`:
  - `game_of_life_wormhole.py` loads all PNGs, builds the tunnel maps, precomputes each cell's neighbors, then advances the simulation to iterations 1, 10, 100, and 1000. The resulting PNGs are saved into `../outputs/`.

## How It Works

### Step 1: Tunnel Mapping
1. Load the two tunnel bitmaps (`horizontal_tunnel.png` and `vertical_tunnel.png`) as RGB arrays of shape (H × W × 3).
2. Group all non-black pixels by their exact RGB color.
3. For each color group (size ≥ 2):
   - If exactly two positions exist, they are the entry/exit endpoints.
   - If more than two positions (a thick border), compute the pair with maximum squared distance. Those two farthest‐apart positions become the warp endpoints.
4. Build two dictionaries:

```python
horizontal_map: Dict[(rowA, colA)] → (rowB, colB)
vertical_map:   Dict[(rowC, colC)] → (rowD, colD)
```

mapping each endpoint to its partner. At runtime, stepping onto either pixel immediately "teleports" to its partner.

### Steps 2 & 3: Cardinal Moves with Wormholes
- Cardinal neighbors ("up" = dr=−1,dc=0; "down" = dr=+1,dc=0; "left" = dr=0,dc=−1; "right" = dr=0,dc=+1) are computed by `get_cardinal_neighbor(r, c, dr, dc)`:
  1. **Bounds check**: If (r,c) is out of [0 .. H−1]×[0 .. W−1], return None.
  2. **Vertical moves** (dr ≠ 0, dc = 0):
     - Case A: If the current (r,c) is in vertical_map → teleport to partner (vr,vc) and then carry one more step vertically in direction dr. Bounds‐check that result; return it or None.
     - Case B: Otherwise, let (nr,nc) = (r+dr, c). If (nr,nc) is outside the grid → None. If (nr,nc) is in vertical_map → teleport to its partner, return that. Otherwise return (nr,nc) directly.
  3. **Horizontal moves** (dr = 0, dc ≠ 0):
     - Case C: If the current (r,c) is in horizontal_map → teleport to partner (hr,hc) and carry one more step horizontally in direction dc. Bounds‐check; return or None.
     - Case D: Otherwise, let (nr,nc) = (r, c+dc). If (nr,nc) is out of bounds → None. If (nr,nc) in horizontal_map → teleport to its partner, return that. Otherwise return (nr,nc).
  4. Any other (dr,dc) combination (not purely cardinal) → None.

### Step 4: Diagonal Moves with Tunnel Precedence
- Diagonal offsets: (dr, dc) ∈ {(-1,-1),(-1,+1),(+1,-1),(+1,+1)}.
- To move one step diagonally, we break it into two cardinal "legs": one vertical (dr, 0) and one horizontal (0, dc).
- We must decide which of the two legs to apply first if both single‐leg destinations land on tunnel endpoints. We use the precedence order:

```python
PRECEDENCE = ["top", "right", "bottom", "left"]
```

- For example, a "down‐right" step (dr=+1, dc=+1) has vertical direction "bottom" and horizontal direction "right."
- If both (r+dr, c) and (r, c+dc) are tunnel‐pixels, compare indices of "bottom" vs "right" in PRECEDENCE. Since "right" (index 1) < "bottom" (index 2), we do the horizontal leg first for "down‐right." Otherwise we default to vertical first when only one or neither leg is a tunnel.

After choosing first_leg and second_leg, we simply:

```python
inter = get_cardinal_neighbor(r, c, dr1, dc1)
if inter is None:
    return None
final = get_cardinal_neighbor(inter_row, inter_col, dr2, dc2)
return final  # or None
```

In our version we always perform both legs. That is, even if the first cardinal sub-step teleports, we still do the second sub-step from the teleported coordinate.

### Step 5: Precomputing All 8 Neighbors for Every Cell
- We allocate a 2D list of lists:

```python
neighbors: List[List[List[Tuple[int,int]]]] = [[[] for _ in range(W)] for _ in range(H)]
```

- For each cell (r,c):
  1. For each (dr,dc) in cardinal offsets, call get_cardinal_neighbor(r,c,dr,dc). If non-None, append to neighbors[r][c].
  2. For each (dr,dc) in diagonal offsets, call get_diagonal_neighbor(r,c,dr,dc). If non-None, append to neighbors[r][c].
- After this pass, neighbors[r][c] holds a list of up to 8 coordinates—each one the appropriate (possibly warped) neighbor of (r,c) under the tunnel rules.

### Step 6: Running the Life Simulation
1. Load `starting_position.png` and convert it to a binary NumPy array grid0 of shape (H × W), where 1 = alive (white pixel) and 0 = dead (black or any non-white).
2. Define the standard Life update function step(grid):

```python
new_grid = zeros((H,W), dtype=uint8)
for each cell (r,c):
    alive = (grid[r,c] == 1)
    count = number of neighbors in neighbors[r][c] that are alive (grid[nr,nc] == 1)
    if alive:
        if count == 2 or count == 3: new_grid[r,c] = 1
        else: new_grid[r,c] = 0
    else:
        if count == 3: new_grid[r,c] = 1
        else: new_grid[r,c] = 0
return new_grid
```

3. Iterate from 1 to 1000:
   - At each iteration i, call grid = step(grid).
   - If i is in [1, 10, 100, 1000], store a copy of grid in results[i].
4. When done, save each results[i] to a PNG:
   - Create a new (H × W × 3) array of type uint8.
   - For every cell with grid[r,c] == 1, set pixel to [255,255,255] (white). Others remain [0,0,0] (black).
   - Write to `outputs/1.png`, `outputs/10.png`, `outputs/100.png`, `outputs/1000.png`.

## Usage

1. Install dependencies:
```bash
pip install pillow numpy
```

2. Verify the directory structure:
```
game_of_life_wormhole/
├── starting_position.png
├── horizontal_tunnel.png
├── vertical_tunnel.png
└── src/
    └── game_of_life_wormhole.py
```

3. Run the simulator:
```bash
cd game_of_life_wormhole/src
python3 game_of_life_wormhole.py
```

4. Check the outputs in:
```
game_of_life_wormhole/outputs/
├── 1.png
├── 10.png
├── 100.png
└── 1000.png
```

## Dependencies

- Python 3.8 or newer
- NumPy
- Pillow (PIL)

## Customization

- To change the iterations at which outputs are saved, edit the line:
```python
targets = [1, 10, 100, 1000]
```
in `game_of_life_wormhole.py`.

- To modify the wormhole layout, replace `horizontal_tunnel.png` or `vertical_tunnel.png` with a new bitmap—each non-black color must appear at least twice.
- To use a different starting pattern, replace `starting_position.png` (white pixels = live cells, black = dead).

## License

This project is released under the MIT License.