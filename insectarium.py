from PIL import Image
from PIL.Image import Image as ImageType
from pathlib import Path
from typing import List, Optional
import argparse
import yaml

def get_coords(path: Path) -> List[int]:
    """
    From a file of name layer_y_x.png, gets a list [layer, y, x]. 
    """
    return [int(x) for x in path.stem.split("_")]

def get_layer(layer_path: str, cfg: dict, args) -> Optional[ImageType]:
    # Get all images
    tile_paths = list(args.input.joinpath(layer_path).glob('*.png'))

    if len(tile_paths) == 0: # Aw, shucks. Nothing here.
        return None

    # Count the layers by looking through all the files for the biggest x in the pattern x_*_*.png
    sublayer_keys = list(set([get_coords(x)[0] for x in tile_paths])) # get all layers
    sublayer_keys = [x for x in sublayer_keys if not cfg.get(x, {}).get("hidden", False)] # filter out hidden layers
    sublayer_keys.sort()
    # initialize a blank sublayer list
    sublayer_images: List[ImageType] = []

    # Filter out all images for hidden layers
    tile_paths = [x for x in tile_paths if get_coords(x)[0] in sublayer_keys]

    if len(sublayer_keys) == 0: # If there are no visible layers...
        return None # ...return nothing.

    for sublayer in sublayer_keys:
        # Only get images for this layer
        sublayer_tiles = [x for x in tile_paths if get_coords(x)[0] == sublayer]

        # Calculate width
        sublayer_width = (max([get_coords(x)[2] for x in sublayer_tiles]) + 1) * 128
        sublayer_height = (max([get_coords(x)[1] for x in sublayer_tiles]) + 1) * 128
        # Initialize image
        sublayer_images.append(Image.new('RGBA', (sublayer_width, sublayer_height)))

    for tile_path in tile_paths:
        tile_coords = get_coords(tile_path)
        tile = Image.open(tile_path)

        # remap file layer to "data layer" index; we have to do this because hidden layers change the list length
        sublayer = sublayer_keys.index(tile_coords[0])  
        sublayer_images[sublayer].paste(tile, (tile_coords[2] * 128, tile_coords[1] * 128), tile)

    for sublayer_id, sublayer in enumerate(sublayer_images):
        true_layer = sublayer_keys[sublayer_id]
        if cfg.get(true_layer, {}).get("mirror", False):
            # Mirror
            mirror_width = (sublayer.size[0] * 2) - 128 * cfg.get(true_layer, {}).get("mirror_hoffset", 0)
            flip_pos = sublayer.size[0] - 128 * cfg.get(true_layer, {}).get("mirror_hoffset", 0)
            mirror_image = Image.new('RGBA', (mirror_width, sublayer.size[1]))
            flip = sublayer.transpose(Image.FLIP_LEFT_RIGHT)

            mirror_image.paste(sublayer, (0,0), sublayer)
            mirror_image.paste(flip, (flip_pos, 0), flip)
            sublayer_images[sublayer_id] = mirror_image

    layer_width = max(sublayer_images, key=lambda x: x.size[0]).size[0]
    layer_height = max(sublayer_images, key=lambda x: x.size[1]).size[1]

    layer = Image.new('RGBA', (layer_width, layer_height))
    for sublayer_id, sublayer in enumerate(sublayer_images):
        if sublayer is None:
            continue
        if args.all:
            Path(f"debug/{args.input.stem}/").mkdir(parents=True, exist_ok=True)
            sublayer.save(Path(f"debug/{args.input.stem}/{args.input.stem}_{layer_path}{sublayer_keys[sublayer_id]}.png"))
        layer.paste(sublayer, (0,0), sublayer)

    return layer

if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser(description="Stitch together Formicide maps")

    cli_parser.add_argument("-i", "--input", type=Path, help="path to the map", required=True)
    cli_parser.add_argument("-c", "--config", type=Path, help="path to the config file", default=None)
    cli_parser.add_argument("-o", "--output", type=Path, help="output file", default=None)
    cli_parser.add_argument("-a", "--all", help="output all layers individually", action="store_true")

    args = cli_parser.parse_args()

    cfg = {}
    if args.config is not None and args.config.exists():
        with open(args.config, "r") as ymlfile:
           cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    layer_key = {
        0: "background",
        1: "terrain",
        2: "foreground"
    }

    layers = [get_layer("BackgroundVisualLayers", cfg.get("background", {}), args), get_layer("TerrainLayers", cfg.get("terrain", {}), args), get_layer("ForegroundVisualLayers", cfg.get("foreground", {}), args)]
    
    map_width = max([x.size[0] for x in layers if x is not None])
    map_height = max([x.size[1] for x in layers if x is not None])
    full_map = Image.new('RGBA', (map_width, map_height))
    for layer_id, layer in enumerate(layers):
        if layer is None:
            continue
        pos_x = 0
        pos_y = 0
        if cfg.get(layer_key[layer_id], {}).get("vcenter", False):
            pos_y = (map_height-layer.size[1])//2 + 256
        full_map.paste(layer, (0,pos_y), layer)
    output_path = f"{args.input.stem}.png" if args.output is None else args.output
    full_map.save(output_path)
