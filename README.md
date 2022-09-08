# insectarium

Insectarium is a quick Python script to read the map data files from [Formicide](https://store.steampowered.com/app/434510/Formicide/) (an online videogame released in 2017) and output maps as images. Due to some unknown details in how maps are stored, not all maps are reconstructed correctly; to correct this, there are config options to hide, offset, or mirror some layers in order to correct these errors, but not all configurations are complete or present.

## Usage

```
$ pip install -r requirements
$ python ./insectarium.py --input "/path/to/steamapps/common/Formicide/DataPacks/Full/Textures/Terrains/[terrain]" --config "./config/[terrain].yaml" --output "./output/[terrain].png"
```

Replace `[terrain]` with the map you want to create, like `Frostbite`. To figure out why a map isn't being reconstructed right, try adding `--all` to the options and inspecting the individual layers in `./debug/[terrain]/`.
