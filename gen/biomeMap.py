import os
import json
import numpy as np
from perlin_noise import PerlinNoise

# ---- CONFIG ----
MAP_SIZE = 128  # Biome map size
CHUNK_SIZE = 16  # Each chunk is 16x16 blocks
SCALE = 0.1  # Controls biome spread
TEMP_SCALE = 0.05  # Controls temperature variation
HUMIDITY_SCALE = 0.07  # Controls humidity variation
RIVER_SCALE = 0.05  # Larger scale for rivers
WORLD_FOLDER = "/usb/mc_world/"  # USB storage location

# Biome IDs
PLAINS, FOREST, MOUNTAINS, DESERT, WATER, SNOW = 0, 1, 2, 3, 4, 5

# Ensure world folder exists
if not os.path.exists(WORLD_FOLDER):
    os.makedirs(WORLD_FOLDER)

# ---- GENERATE BIOME MAP ----
def generate_biome_map(seed=42):
    """Generates a biome map with temperature and humidity layers."""
    np.random.seed(seed)
    terrain_noise = PerlinNoise(octaves=4, seed=seed)
    river_noise = PerlinNoise(octaves=3, seed=seed + 100)
    temp_noise = PerlinNoise(octaves=2, seed=seed + 200)
    humidity_noise = PerlinNoise(octaves=2, seed=seed + 300)

    biome_map = np.zeros((MAP_SIZE, MAP_SIZE), dtype=int)

    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            terrain_value = terrain_noise([x * SCALE, y * SCALE])
            river_value = river_noise([x * RIVER_SCALE, y * RIVER_SCALE])
            temp_value = temp_noise([x * TEMP_SCALE, y * TEMP_SCALE])
            humidity_value = humidity_noise([x * HUMIDITY_SCALE, y * HUMIDITY_SCALE])

            # Determine base biome by elevation
            if terrain_value < -0.2:
                biome = PLAINS
            elif terrain_value < 0.2:
                biome = FOREST
            else:
                biome = MOUNTAINS

            # Apply temperature & humidity constraints
            if temp_value < -0.1 and terrain_value > 0.1:
                biome = SNOW  # Snow biome in cold areas
            if temp_value > 0.3 and humidity_value < 0:
                biome = DESERT  # Desert in hot, dry regions

            # Overlay river (low values = water)
            if river_value < -0.15:
                biome = WATER

            biome_map[x][y] = biome

    return biome_map

# ---- SAVE & LOAD BIOME MAP ----
def save_biome_map(biome_map, filename=f"{WORLD_FOLDER}/biome_map.json"):
    """Saves the biome map as a JSON file."""
    with open(filename, "w") as f:
        json.dump(biome_map.tolist(), f)

def load_biome_map(filename=f"{WORLD_FOLDER}/biome_map.json"):
    """Loads a biome map from JSON or generates a new one."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return np.array(json.load(f))
    else:
        biome_map = generate_biome_map()
        save_biome_map(biome_map)
        return biome_map

# ---- GET BIOME AT CHUNK LEVEL ----
def get_biome_at(cx, cy, biome_map):
    """Returns the biome type at a given chunk coordinate."""
    x = cx % MAP_SIZE
    y = cy % MAP_SIZE
    return biome_map[x][y]

# ---- BIOME BLENDING ----
def blend_biomes(x, y, biome_map):
    """Blends biomes by averaging neighboring biome values."""
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_SIZE and 0 <= ny < MAP_SIZE:
                neighbors.append(biome_map[nx][ny])
    return round(sum(neighbors) / len(neighbors))

# ---- MAIN TESTING ----
if __name__ == "__main__":
    biome_map = load_biome_map()  # Load or generate the map

    # Print a simple text visualization
    biome_symbols = {PLAINS: ".", FOREST: "T", MOUNTAINS: "^", DESERT: "#", WATER: "~", SNOW: "*"}
    
    for y in range(20):  # Print only a small section
        row = "".join(biome_symbols[blend_biomes(x, y, biome_map)] for x in range(40))
        print(row)
