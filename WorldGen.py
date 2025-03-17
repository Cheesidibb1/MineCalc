import os
import json
import random

def make_world_folder(name):
    return f"./saves/{name}"

# ---- CONFIG ----
WORLD_FOLDER = make_world_folder(input("name: ")) # Folder for world data
WORLD_FOLDER_CHUNKS = f"{WORLD_FOLDER}/chunks"  # Folder for chunk storage
WORLD_FOLDER_NBTS = f"{WORLD_FOLDER}/nbts"  # Folder for NBT storage
CHUNK_SIZE = 16   # 16x16 blocks per chunk
CHUNK_HEIGHT = 256  # Max height of a chunk
CACHE_LIMIT = 50  # Max chunks in memory before unloading
CHUNK_AMT_X = 10  # Amount of chunks to generate (x-axis)
CHUNK_AMT_Y = 10  # Amount of chunks to generate (y-axis)

# ---- BLOCKS ----
AIR, STONE, GRASS, DIRT, OAKWOOD, LEAVES, BEDROCK = "mnclc:air", "mnclc:stone", "mnclc:grass", "mnclc:OAKWOOD", "mnclc:tree", "mnclc:leaves", "mnclc:bedrock"

# ---- BIOMES ----
BIOMES = {
    "plains": {"height": 4, "blocks": [GRASS, DIRT]},
    "forest": {"height": 6, "blocks": [GRASS, DIRT, OAKWOOD]},
    "mountain": {"height": 10, "blocks": [STONE, DIRT]},
}

# Ensure world folder exists
if not os.path.exists(WORLD_FOLDER):
    os.makedirs(WORLD_FOLDER)

if not os.path.exists(WORLD_FOLDER_CHUNKS):
    os.makedirs(WORLD_FOLDER_CHUNKS)
if not os.path.exists(WORLD_FOLDER_NBTS):
    os.makedirs(WORLD_FOLDER_NBTS)


# ---- CHUNK HANDLING ----
chunk_cache = {}

def save_chunk(cx, cy, chunk_data):
    """Saves a chunk as JSON on USB storage."""
    filepath = f"{WORLD_FOLDER_CHUNKS}/chunk_{cx}_{cy}.json"
    with open(filepath, "w") as f:
        json.dump(chunk_data, f)

def load_chunk(cx, cy):
    """Loads a chunk from JSON or generates it."""
    filepath = f"{WORLD_FOLDER}/chunk_{cx}_{cy}.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        return generate_chunk(cx, cy)

def get_chunk(cx, cy):
    """Loads a chunk from cache, storage, or generates it."""
    if (cx, cy) not in chunk_cache:
        chunk_cache[(cx, cy)] = load_chunk(cx, cy)
    return chunk_cache[(cx, cy)]

def unload_old_chunks():
    """Removes old chunks from cache to free memory."""
    if len(chunk_cache) > CACHE_LIMIT:
        chunk_cache.pop(next(iter(chunk_cache)))

# ---- TERRAIN GENERATION ----
def get_biome(cx, cy):
    """Determines the biome for a given chunk."""
    random.seed(cx * 1000 + cy * 2000)
    return random.choice(list(BIOMES.keys()))

def generate_chunk(cx, cy):
    """Creates a chunk with stone, bedrock, and air."""
    chunk = {"blocks": [[STONE for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_HEIGHT)]}
    for x in range(CHUNK_SIZE):
        for y in range(CHUNK_HEIGHT):
            if y <= 2:
                chunk["blocks"][y][x] = BEDROCK
            elif y <= 60 and y >= 3:
                chunk["blocks"][y][x] = random.choices([STONE, AIR], weights=[0.8, 0.2])[0]
            else:
                chunk["blocks"][y][x] = STONE if random.random() < 0.02 else AIR
    save_chunk(cx, cy, chunk)
    return chunk



# ---- MAIN LOOP FOR TESTING ----
def generate_world():
    for x in range(CHUNK_AMT_X + 1):
        for y in range(CHUNK_AMT_Y + 1):
            generate_chunk(x, y)
            print(f"Generated chunk {x}, {y}")

