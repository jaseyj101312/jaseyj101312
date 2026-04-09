# retrocausal_overlay_transmitter.py
from PIL import Image, ImageDraw
import colorsys
import random
import reedsolo

GRID_SIZE = 32
RS_N, RS_K = 255, 223
BRIGHTNESS = 0.06
SECRET_SEED = 0xBEEFCAFEDEADBEEF
NOISE_RANGE = 2

message = b"Layered color grid overlay test with chained differential encoding"

# RS encode (forward symbols)
data_bytes = bytearray(message)
blocks_needed = (len(data_bytes) + RS_K - 1) // RS_K
encoder = reedsolo.RSCodec(RS_N - RS_K)
forward_symbols = []
for i in range(blocks_needed):
    chunk = data_bytes[i*RS_K:(i+1)*RS_K]
    block = chunk + b'\x00' * (RS_K - len(chunk))
    forward_symbols.extend(list(encoder.encode(block)))
forward_symbols += [0] * (GRID_SIZE*GRID_SIZE - len(forward_symbols))

# Mirror layer (bit-flipped complement of forward symbols, retrocausal direction)
mirror_symbols = [s ^ 0xFF for s in forward_symbols]

# Chained differential encoding: each symbol XORed with previous
def chained_differential_encode(symbols):
    encoded = [symbols[0]]
    for i in range(1, len(symbols)):
        encoded.append(symbols[i] ^ symbols[i - 1])
    return encoded

chained_forward = chained_differential_encode(forward_symbols)
chained_mirror = chained_differential_encode(mirror_symbols)

# Combine forward and mirror layers into a single overlay grid
combined = [(chained_forward[i] ^ chained_mirror[i]) & 0xFF
            for i in range(GRID_SIZE * GRID_SIZE)]

# Map a symbol value [0–255] to an RGB color using HSV with fixed low brightness
def symbol_to_color(sym):
    hue = sym / 255.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, BRIGHTNESS)
    return (int(r * 255), int(g * 255), int(b * 255))

# Render the 32×32 color grid as a PIL image
CELL_SIZE = 16
img_size = GRID_SIZE * CELL_SIZE
img = Image.new("RGB", (img_size, img_size), (0, 0, 0))
draw = ImageDraw.Draw(img)

rng = random.Random(SECRET_SEED)
for row in range(GRID_SIZE):
    for col in range(GRID_SIZE):
        idx = row * GRID_SIZE + col
        base_color = symbol_to_color(combined[idx])
        # Apply seeded per-cell noise for subtle variation
        color = tuple(min(255, max(0, c + rng.randint(-NOISE_RANGE, NOISE_RANGE))) for c in base_color)
        x0 = col * CELL_SIZE
        y0 = row * CELL_SIZE
        x1 = x0 + CELL_SIZE - 1
        y1 = y0 + CELL_SIZE - 1
        draw.rectangle([x0, y0, x1, y1], fill=color)

output_path = "retrocausal_overlay.png"
img.save(output_path)
print(f"Saved {output_path} ({img_size}x{img_size} px, {GRID_SIZE}x{GRID_SIZE} grid)")
