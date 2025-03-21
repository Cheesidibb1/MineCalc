import os
import json
import numpy as np
from perlin_noise import PerlinNoise
from PIL import Image

# ---- CONFIG ----
MAP_SIZE = 256  # Biome map size
CHUNK_SIZE = 16  # Each chunk is 16x16 blocks
SCALE = 0.02  # Controls biome spread (lower value for larger islands)
TEMP_SCALE = 0.05  # Controls temperature variation
HUMIDITY_SCALE = 0.05  # Controls humidity variation
RIVER_SCALE = 0.05  # Larger scale for rivers

# Load biomes configuration
def load_json_config(filename):
    with open(filename, "r") as f:
        return json.load(f)

biomes_config = load_json_config("config/biomes.json")

# Convert biomes to a dictionary for easy access
biomes = {biome["name"].lower(): biome for biome in biomes_config["biomes"]}

# Biome Colors
BIOME_COLORS = {
    biome["name"].lower(): tuple(int(biome.get("color", "#000000")[i:i+2], 16) for i in (1, 3, 5))
    for biome in biomes_config["biomes"]
}

# Add sub-biomes to BIOME_COLORS
for biome in biomes_config["biomes"]:
    if "sub_biomes" in biome:
        for sub_biome in biome["sub_biomes"]:
            BIOME_COLORS[sub_biome["name"].lower()] = tuple(int(sub_biome.get("color", "#000000")[i:i+2], 16) for i in (1, 3, 5))

# Add a default color for missing biomes
DEFAULT_BIOME_COLOR = (0, 0, 0)  # Black

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
    terrain_noise = PerlinNoise(octaves=5, seed=seed)  # Adjust octaves for more natural terrain
    river_noise = PerlinNoise(octaves=6, seed=seed + 100)
    temp_noise = PerlinNoise(octaves=4, seed=seed + 200)
    humidity_noise = PerlinNoise(octaves=4, seed=seed + 300)

    biome_map = np.full((MAP_SIZE, MAP_SIZE), "ocean", dtype=object)  # Default to ocean

    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            terrain_value = terrain_noise([x * SCALE, y * SCALE])
            river_value = river_noise([x * RIVER_SCALE, y * RIVER_SCALE])
            temp_value = temp_noise([x * TEMP_SCALE, y * TEMP_SCALE])
            humidity_value = humidity_noise([x * HUMIDITY_SCALE, y * HUMIDITY_SCALE])

            # Distance from the center of the map
            distance = np.sqrt((x - MAP_SIZE / 2) ** 2 + (y - MAP_SIZE / 2) ** 2) / (MAP_SIZE / 2)

            # Determine base biome by elevation and distance
            if terrain_value > 0.1 and distance < 0.7:  # Increase threshold for land and limit distance
                if terrain_value < 0.3:
                    biome = "plains"
                elif terrain_value < 0.5:
                    biome = "forest"
                else:
                    biome = "mountains"

                # Apply temperature & humidity constraints
                if temp_value < -0.2 and terrain_value > 0.4:
                    biome = "tundra"  # Snow biome in cold areas
                if temp_value > 0.4 and humidity_value < 0.3:
                    biome = "desert"  # Desert in hot, dry regions

                # Overlay river (low values = water)
                if river_value < -0.1:
                    biome = "water"

                biome_map[x][y] = biome
            else:
                # Determine ocean sub-biomes based on temperature
                if temp_value < -0.4:
                    biome_map[x][y] = "ice ocean"
                elif temp_value < -0.2:
                    biome_map[x][y] = "cold ocean"
                else:
                    biome_map[x][y] = "ocean"

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
    filename = os.path.join(world_folder, "biome_map", "biome_map.json")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return np.array(json.load(f), dtype=object)
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
    filename = os.path.join(world_folder, "biome_map", "biome_map.png")
    img = Image.new("RGB", (MAP_SIZE, MAP_SIZE))
    pixels = img.load()
    
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            biome = biome_map[x][y]
            color = BIOME_COLORS.get(biome, DEFAULT_BIOME_COLOR)
            if color == DEFAULT_BIOME_COLOR:
                print(f"Missing color for biome: {biome}")
            pixels[x, y] = color
    
    img.save(filename)
    print(f"Biome map image saved as {filename}")

# ---- MAIN TESTING ----
def make_biome_map(world_name):
    biome_map = load_biome_map(world_name)  # Load or generate the map
    generate_biome_image(biome_map, world_name)  # Create biome image

if __name__ == "__main__":
    world_name = input("Enter world name: ")
    make_biome_map(world_name)
