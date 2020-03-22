import requests
import platform
import re
import os
import shutil
import ctypes
import json
import subprocess
import random
import pickle
from threading import Thread
from time import sleep
from screeninfo import get_monitors
from PIL import Image
from argparse import ArgumentParser

def load_config():
    global config
    cfg = 'config.json'
    # use template if config doesn't exist
    if not os.path.exists(cfg):
        cfg = 'config.tmpl.json'
    config = json.load(open(cfg))

def set_wallpaper(path):

    # high-res images look blurred on GNOME, downscale to monitor resolution
    # for best results.
    if config['downscale']:
        # use the variant as wallpaper
        path = downscale_image(path)

    plt = platform.system()
    if plt == 'Linux':
        # run gnome wallpaper set
        subprocess.run(['/usr/bin/gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', f'file://{path}'])
    elif plt == 'Windows':
        SPI_SETDESKTOPWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKTOPWALLPAPER, 0, path, 3)

def get_catalog_path():
    catalog_path = config['catalog_path']

    if not os.path.isabs(catalog_path):
        catalog_path = os.path.join(os.getcwd(), catalog_path)
    
    # create catalog path if it doesnt exist
    if not os.path.exists(catalog_path):
        os.makedirs(catalog_path)

    return catalog_path

def read_catalog():
    cp = get_catalog_path()
    return [img for img in map(lambda x : os.path.join(cp, x), os.listdir(get_catalog_path())) if is_image(img)]
    
def is_image(img_path):
    try:
        Image.open(img_path)
        return True
    except IOError:
        return False

def downscale_image(img_path):
    # get the monitor width
    width = get_monitors()[0].width

    # load a variant image with the required screen dimensions
    new_path, fname = os.path.split(img_path)
    new_path = os.path.join(new_path, str(width))
    variant = os.path.join(new_path, fname)

    # if the variant doensn't already exist, create it
    if not os.path.exists(variant):
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        
        img = Image.open(img_path)
        # find ratio between monitor width and image width
        ratio = width / img.width
        # resize image to new dimensions
        img = img.resize((width, int(img.height * ratio)))
        # save this variant
        img.save(variant)

    return variant

def verify(path):
    img = Image.open(path)
    monitor = get_monitors()[0]

    # must be higher resolution
    if img.width < monitor.width or img.height < monitor.height:
        return False
        
    # if image is portrait, skip
    if img.width < img.height:
        return False

    img.save(path)
    return True


def update_catalog():
    catalog_path = get_catalog_path()

    # generate catalog list
    current_catalog = read_catalog()

    while True:
        print("Updating catalog...")
        
        posts = []

        # fetch top posts from each subreddit
        subreddit_list = config['subreddit_list']
        for subreddit in subreddit_list:
            # fetch the subreddit rss feed
            feed = f'https://reddit.com/r/{subreddit}.json'
            js = requests.get(feed, headers={'user-agent': 'reddit-wallpaper-haroon96'}).json()
            
            # save list of posts
            posts.extend(js['data']['children'][:config['number_of_top_posts']])

        # shuffle posts for source mixing
        random.shuffle(posts)

        # download image from each post
        for post in posts:
            # skip nsfw posts
            if post['data']['over_18']:
                continue

            # extract post image url
            url = post['data']['url']
            
            # check if img not already saved
            _id = os.path.split(url)[1]
            img_path = os.path.join(catalog_path, _id)

            # if image already downloaded, skip
            if img_path in current_catalog:
                continue

            # invalid format
            if os.path.splitext(img_path)[1] not in ['.jpg', '.png', '.bmp']:
                continue

            # download the image
            r = requests.get(url, stream=True)

            # save image to disk
            with open(img_path, 'wb') as f:
                f.write(r.raw.read())

            # check if the image meets requirements and process accordingly
            # if it doesn't, delete it
            if not verify(img_path):
                os.remove(img_path)
                continue
            
            # add image to catalog and save
            current_catalog.append(img_path)

        # sleep for specified interval
        print("Catalog updated!")
        sleep(config['catalog_update_interval'])

def main():
    Thread(target=update_catalog, daemon=True).start()
    
    used = set()

    while True:

        # reload config
        load_config()

        print("Setting wallpaper...")
        
        # read catalog
        catalog = read_catalog()

        # if no wallpapers exist, wait
        if len(catalog) == 0:
            print("Waiting for catalog update...")
            sleep(config['wallpaper_change_interval'])
            continue
            
        # select wallpapers that haven't been used recently
        options = [img for img in catalog if img not in used]
        
        # if all wallpapers consumed, recycle
        if len(options) == 0:
            options = catalog
            used = set()

        # select a random wallpaper
        choice = random.choice(options)

        # mark wallpaper as used
        used.add(choice)
        
        # set as wallpaper
        set_wallpaper(choice)
        print("Wallpaper set!")

        # wait for timeout before setting new wallpaper
        sleep(config['wallpaper_change_interval'])


if __name__ == '__main__':
    # change working directory to this
    if os.path.dirname(__file__) != '':
        os.chdir(os.path.dirname(__file__))

    # load config
    load_config()

    parser = ArgumentParser()
    parser.add_argument('--start', help="Start the wallpaper app", action="store_true")
    parser.add_argument('--clear-catalog', help="Clear the current catalog", action="store_true")

    args = parser.parse_args()
      
    no_arg = True
    
    if args.clear_catalog:
        no_arg = False
        shutil.rmtree(get_catalog_path(), ignore_errors=True)

    if args.start:
        no_arg = False
        main()
        
    if no_arg:
        parser.print_help()
