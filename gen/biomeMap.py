import os
import json
import numpy as np
from perlin_noise import PerlinNoise
from PIL import Image

# ---- CONFIG ----
MAP_SIZE = 256  # Biome map size
CHUNK_SIZE = 16  # Each chunk is 16x16 blocks
SCALE = 0.05  # Controls biome spread (lower value for larger islands)
TEMP_SCALE = 0.05  # Controls temperature variation
HUMIDITY_SCALE = 0.07  # Controls humidity variation
RIVER_SCALE = 0.05  # Larger scale for rivers

# Biome IDs
PLAINS, FOREST, MOUNTAINS, DESERT, WATER, SNOW = 0, 1, 2, 3, 4, 5

# Biome Colors
BIOME_COLORS = {
    PLAINS: (144, 238, 144),  # Light Green
    FOREST: (34, 139, 34),    # Dark Green
    MOUNTAINS: (139, 137, 137),  # Gray
    DESERT: (237, 201, 175),  # Sandy
    WATER: (0, 0, 255),       # Blue
    SNOW: (255, 250, 250)     # White
}

# Ensure world folder exists
def ensure_world_folder(world_name):
    world_folder = os.path.join(os.getcwd(), "saves", world_name)
    if not os.path.exists(world_folder):
        os.makedirs(world_folder)
    return world_folder

# ---- GENERATE BIOME MAP ----
def generate_biome_map(seed=42):
    """Generates a biome map with temperature and humidity layers."""
    np.random.seed(seed)
    terrain_noise = PerlinNoise(octaves=2, seed=seed)  # Lower frequency for larger islands
    river_noise = PerlinNoise(octaves=3, seed=seed + 100)
    temp_noise = PerlinNoise(octaves=2, seed=seed + 200)
    humidity_noise = PerlinNoise(octaves=2, seed=seed + 300)

    biome_map = np.full((MAP_SIZE, MAP_SIZE), WATER, dtype=int)  # Default to water

    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            terrain_value = terrain_noise([x * SCALE, y * SCALE])
            river_value = river_noise([x * RIVER_SCALE, y * RIVER_SCALE])
            temp_value = temp_noise([x * TEMP_SCALE, y * TEMP_SCALE])
            humidity_value = humidity_noise([x * HUMIDITY_SCALE, y * HUMIDITY_SCALE])

            # Distance from the center of the map
            distance = np.sqrt((x - MAP_SIZE / 2) ** 2 + (y - MAP_SIZE / 2) ** 2) / (MAP_SIZE / 2)

            # Determine base biome by elevation and distance
            if terrain_value > 0.1 and distance < 0.5:  # Increase threshold for land and limit distance
                if terrain_value < 0.2:
                    biome = PLAINS
                elif terrain_value < 0.4:
                    biome = FOREST
                else:
                    biome = MOUNTAINS

                # Apply temperature & humidity constraints
                if temp_value < -0.1 and terrain_value > 0.3:
                    biome = SNOW  # Snow biome in cold areas
                if temp_value > 0.3 and humidity_value < 0:
                    biome = DESERT  # Desert in hot, dry regions

                # Overlay river (low values = water)
                if river_value < -0.0:
                    biome = WATER

                biome_map[x][y] = biome

    return biome_map

# ---- SAVE & LOAD BIOME MAP ----
def save_biome_map(biome_map, world_name):
    """Saves the biome map as a JSON file."""
    world_folder = ensure_world_folder(world_name)
    filename = os.path.join(world_folder, "biome_map", "biome_map.json")
    with open(filename, "w") as f:
        json.dump(biome_map.tolist(), f)

def load_biome_map(world_name):
    """Loads a biome map from JSON or generates a new one."""
    world_folder = ensure_world_folder(world_name)
    filename = os.path.join(world_folder, "biome_map","biome_map.json")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return np.array(json.load(f))
    else:
        biome_map = generate_biome_map()
        save_biome_map(biome_map, world_name)
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

# ---- GENERATE IMAGE ----
def generate_biome_image(biome_map, world_name):
    """Generates an image representation of the biome map."""
    world_folder = ensure_world_folder(world_name)
    filename = os.path.join(world_folder, "biome_map","biome_map.png")
    img = Image.new("RGB", (MAP_SIZE, MAP_SIZE))
    pixels = img.load()
    
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            pixels[x, y] = BIOME_COLORS[biome_map[x][y]]
    
    img.save(filename)
    print(f"Biome map image saved as {filename}")

# ---- MAIN TESTING ----
def make_biome_map(world_name):
    biome_map = load_biome_map(world_name)  # Load or generate the map
    generate_biome_image(biome_map, world_name)  # Create biome image

if __name__ == "__main__":
    world_name = input("Enter world name: ")
    make_biome_map(world_name)
