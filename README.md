# Reddit-Wallpaper

An application for routinely downloading and setting system wallpapers from specified subreddits.

## Features
- Supports Windows and GNOME on Linux
- Auto-downloads wallpapers from specified subreddits

## Installation
1. Clone/download this repository.
2. Install the required packages using `pip install -r requirements.txt`.
3. Copy `config.tmpl.json` to `config.json` and make adjustments accordingly. (See [Configuration](#configuration) section below for more information.)
4. Start the program using `python main.py --start` or configure the script to run on startup with the `--start` flag specified.

## Configuration
- Starting the program using the `--clear-catalog` command clears the current catalog.
- The following configurations can be specified in `config.json`.
  - `catalog_path`: Path _(absolute/relative)_ for storing downloaded images.
  - `catalog_update_interval`: Interval _(in seconds)_ after which to download new images from the subreddits.
  - `wallpaper_change_interval`: Interval _(in seconds)_ after which to change the wallpaper.
  - `downscale`: Boolean value for specifying whether images require downscaling to the screen resolution before setting them as the wallpaper. High-resolution images appear blurred on GNOME but work fine on Windows.
  - `number_of_top_posts`: Number of top posts to download from each subreddit in a single update.
  - `subreddit_list`: List of subreddits to source images from.

## Credits for packages used
- [Pillow](https://github.com/python-pillow/Pillow)
- [screeninfo](https://github.com/rr-/screeninfo)
