from PIL import Image
import argparse
import pathlib
import yaml

def get_layer(layer: str, cfg: dict, args) -> Image:
    image_names = list(args.input.joinpath(layer).glob('*.png'))
    coordinates = [list(map(int, x.stem.split('_'))) for x in image_names]
    image_map = list(zip(image_names, coordinates))
    total_layers = max([x[0] for x in coordinates]) + 1
    
    layers = []
    for i in range(total_layers):
        if i in cfg:
            if cfg[i].get("hidden", False) is True:
                continue
        
        i_coordinates = [x for x in coordinates if x[0] == i]
        if len(i_coordinates) == 0:
            continue

        total_width = (max([x[2] for x in i_coordinates]) * 128) + 128
        total_height = (max([x[1] for x in i_coordinates]) * 128) + 128
    
        layer_im = Image.new('RGBA', (total_width, total_height))
    
        for im in image_map:
            if im[1][0] != i:
                continue
            
            image = Image.open(im[0])
            layer_im.paste(image, (im[1][2] * 128, im[1][1] * 128), image)
            image.close()
        
        if i in cfg:
            if cfg[i].get("mirror", False):
                # Mirror
                mirror_image = Image.new("RGBA", ((total_width * 2) - 128 * cfg[i].get("mirror_hoffset", 0), total_height))
                flip = layer_im.transpose(Image.FLIP_LEFT_RIGHT)

                mirror_image.paste(layer_im, (0,0), layer_im)
                mirror_image.paste(flip, (total_width - 128 * cfg[i].get("mirror_hoffset", 0), 0), flip)

                layers.append(mirror_image)
            else:
                layers.append(layer_im)
        else:
            layers.append(layer_im)

        if args.all:
            pathlib.Path("debug/").joinpath(pathlib.Path(args.input.stem)).mkdir(parents=True, exist_ok=True)
            layer_im.save(pathlib.Path("debug/").joinpath(pathlib.Path(args.input.stem)).joinpath(f"{args.input.stem}_{layer}_{i}.png"))
    
    layer_width = max([x.size[0] for x in layers])
    layer_height = max([x.size[1] for x in layers])
    full_layer = Image.new('RGBA', (layer_width, layer_height))
    for sub_layer in layers:
        full_layer.paste(sub_layer, (0,0), sub_layer)

    if args.all:
        pathlib.Path("debug/").joinpath(pathlib.Path(args.input.stem)).mkdir(parents=True, exist_ok=True)
        full_layer.save(pathlib.Path("debug/").joinpath(pathlib.Path(args.input.stem)).joinpath(f"{args.input.stem}_{layer}.png"))
    return full_layer    

if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser(description="Stitch together Formicide maps")

    cli_parser.add_argument("-i", "--input", type=pathlib.Path, help="path to the map", required=True)
    cli_parser.add_argument("-c", "--config", type=pathlib.Path, help="path to the config file", default=None)
    cli_parser.add_argument("-o", "--output", type=pathlib.Path, help="output file", default=None)
    cli_parser.add_argument("-a", "--all", help="output all layers individually", action="store_true")

    args = cli_parser.parse_args()

    cfg = {}
    if args.config is not None and args.config.exists():
        with open(args.config, "r") as ymlfile:
           cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    layers = [get_layer("BackgroundVisualLayers", cfg.get("background", {}), args), get_layer("TerrainLayers", cfg.get("terrain", {}), args), get_layer("ForegroundVisualLayers", cfg.get("foreground", {}), args)]
    map_width = max([x.size[0] for x in layers])
    map_height = max([x.size[1] for x in layers])
    full_map = Image.new('RGBA', (map_width, map_height))
    for layer in layers:
            full_map.paste(layer, (0,0), layer)
    output_path = f"{args.input.stem}.png" if args.output is None else args.output
    full_map.save(output_path)
