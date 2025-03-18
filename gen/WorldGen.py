import os
import json
import random
import threading
import biomeMap
import msgpack  # Efficient binary storage

def make_world_folder(name):
    return f"./saves/{name}"

# ---- CONFIG ----
WORLD_NAME = input("World name: ")
WORLD_FOLDER = make_world_folder(WORLD_NAME)
WORLD_FOLDER_CHUNKS = f"{WORLD_FOLDER}/chunks"
WORLD_FOLDER_NBTS = f"{WORLD_FOLDER}/nbts"
WORLD_FOLDER_BIOME_MAP = f"{WORLD_FOLDER}/biome_map"
CHUNK_SIZE = 16
CHUNK_HEIGHT = 256
CACHE_LIMIT = 15
CHUNK_AMT = int(input("Enter chunk amount (accounts for x and y): "))
CHUNK_AMT_X = CHUNK_AMT
CHUNK_AMT_Y = CHUNK_AMT

print(f"Generating {CHUNK_AMT_X * CHUNK_AMT_Y} chunks ({CHUNK_AMT_X}x{CHUNK_AMT_Y})")

# ---- BLOCKS ----
AIR, STONE, GRASS, DIRT, OAKWOOD, LEAVES, BEDROCK, WATER = "mnclc:air", "mnclc:stone", "mnclc:grass", "mnclc:OAKWOOD", "mnclc:tree", "mnclc:leaves", "mnclc:bedrock", "mnclc:water"

# ---- BIOMES ----
BIOMES = {
    "plains": {"height": 4, "blocks": [GRASS, DIRT]},
    "forest": {"height": 6, "blocks": [GRASS, DIRT, OAKWOOD]},
    "mountain": {"height": 10, "blocks": [STONE, DIRT]},
}

# Ensure world folder exists
os.makedirs(WORLD_FOLDER, exist_ok=True)
os.makedirs(WORLD_FOLDER_CHUNKS, exist_ok=True)
os.makedirs(WORLD_FOLDER_NBTS, exist_ok=True)
os.makedirs(WORLD_FOLDER_BIOME_MAP, exist_ok=True)

# ---- CHUNK HANDLING ----
chunk_cache = {}
all_chunks = {}

def save_all_chunks():
    filepath = f"{WORLD_FOLDER_CHUNKS}/chunk_data.msgpack"
    with open(filepath, "wb") as f:
        packed_data = msgpack.packb(all_chunks, use_bin_type=True)
        f.write(packed_data)
    print(f"Saved all chunks to {filepath}")

def load_all_chunks():
    filepath = f"{WORLD_FOLDER_CHUNKS}/chunk_data.msgpack"
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            print(f"Loaded chunks from {filepath}")
            return msgpack.unpackb(f.read(), raw=False)
    print(f"No existing chunk data found at {filepath}")
    return {}

def save_chunk(cx, cy, chunk_data):
    all_chunks[(cx, cy)] = chunk_data

def load_chunk(cx, cy):
    return all_chunks.get((cx, cy), generate_chunk(cx, cy))

def get_chunk(cx, cy):
    if (cx, cy) not in chunk_cache:
        chunk_cache[(cx, cy)] = load_chunk(cx, cy)
    return chunk_cache[(cx, cy)]

def unload_old_chunks():
    if len(chunk_cache) > CACHE_LIMIT:
        chunk_cache.pop(next(iter(chunk_cache)))

def generate_chunk(cx, cy):
    biome_map = biomeMap.load_biome_map(WORLD_NAME)
    biome = biomeMap.get_biome_at(cx, cy, biome_map)
    biome_info = BIOMES.get(biome, BIOMES["plains"])  # Default to plains if biome not found
    height = biome_info["height"]
    block_types = biome_info["blocks"]

    chunk = {"blocks": [[STONE for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_HEIGHT)]}
    for x in range(CHUNK_SIZE):
        for y in range(CHUNK_HEIGHT):
            if y <= 2:
                chunk["blocks"][y][x] = BEDROCK
            elif y < height:
                chunk["blocks"][y][x] = random.choice(block_types)
            elif y < 60:
                chunk["blocks"][y][x] = random.choices([STONE, AIR], weights=[0.8, 0.2])[0]
            else:
                chunk["blocks"][y][x] = STONE if random.random() < 0.02 else AIR
            
            if chunk["blocks"][y][x] == AIR and y < 62:
                chunk["blocks"][y][x] = WATER
    save_chunk(cx, cy, chunk)
    return chunk

def generate_world():
    biomeMap.make_biome_map(WORLD_NAME)
    def worker(x, y):
        generate_chunk(x, y)
        print(f"Generated chunk {x}, {y}")
    
    threads = []
    for x in range(CHUNK_AMT_X + 1):
        for y in range(CHUNK_AMT_Y + 1):
            t = threading.Thread(target=worker, args=(x, y))
            t.start()
            threads.append(t)
    
    for t in threads:
        t.join()
    
    save_all_chunks()

if __name__ == "__main__":
    all_chunks = load_all_chunks()
    generate_world()
