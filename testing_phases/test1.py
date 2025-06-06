import numpy as np
from PIL import Image

# (1) Load your output (from outputs/1.png) and the expected image
actual = Image.open("outputs/1.png").convert("RGB")
expected = Image.open("expected/expected-1.png").convert("RGB")
a_arr = np.array(actual)
e_arr = np.array(expected)

# (2) Count alive pixels in each
a_alive = np.all(a_arr == [255,255,255], axis=2).sum()
e_alive = np.all(e_arr == [255,255,255], axis=2).sum()
print(f"Actual alive  count: {a_alive}")
print(f"Expected alive count: {e_alive}")

# (3) Build a mask of where “alive/dead” differs
diff_mask = (np.all(a_arr == [255,255,255], axis=2) != np.all(e_arr == [255,255,255], axis=2))
diff_positions = list(zip(*np.where(diff_mask)))
print(f"Number of differing pixels: {len(diff_positions)}")
print("Sample differences (row, col):", diff_positions[:10])

# (4) Create a “red overlay” image highlighting those pixels
H, W, _ = a_arr.shape
overlay = np.zeros((H, W, 3), dtype=np.uint8)
for (r, c) in diff_positions:
    overlay[r, c] = [255, 0, 0]   # mark differences in red

Image.fromarray(overlay).save("diff_overlay.png")
print("Saved diff_overlay.png (red marks mismatches).")