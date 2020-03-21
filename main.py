import requests
import platform
import re
import os
import ctypes
import json
import subprocess
import random
import pickle
from threading import Thread
from time import sleep
from screeninfo import get_monitors
from PIL import Image

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
    if os.path.exists('catalog.pickle'):
        return pickle.load(open('catalog.pickle', 'rb'))
    return []

def downscale_image(path):
    # get the monitor width
    width = get_monitors()[0].width

    # load a variant image with the required screen dimensions
    fn, ext = os.path.splitext(path)
    variant = f'{fn}-{width}{ext}'

    # if the variant doensn't already exist, create it
    if not os.path.exists(variant):
        img = Image.open(path)
        ratio = width / img.width
        img.resize((width, int(img.height * ratio)))
        img.save(variant)

    return variant

def verify(path):
    img = Image.open(path)
    monitor = get_monitors()[0]

    # must be better resolution
    if img.width < monitor.width or img.height < monitor.height:
        return False

    img.save(path)
    return True


def update_catalog():
    catalog_path = get_catalog_path()

    # generate catalog list
    current_catalog = read_catalog()

    while True:
        print("Updating catalog...")

        for subreddit in config['subreddit_list']:
            # fetch the subreddit rss feed
            feed = f'https://reddit.com/r/{subreddit}.json'
            js = requests.get(feed, headers={'user-agent': 'reddit-wallpaper-haroon96'}).json()

            # get the list of posts
            posts = js['data']['children'][:config['number_of_top_posts']]

            for post in posts:
                url = post['data']['url']
                
                # check if img not already saved
                _id = os.path.split(url)[1]
                img_path = os.path.join(catalog_path, _id)

                if img_path in current_catalog:
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
                pickle.dump(current_catalog, open('catalog.pickle', 'wb'))

            
        print("Catalog updated!")
        sleep(config['catalog_update_timeout'])

def main():
    global config
    config = json.load(open('config.json'))
    Thread(target=update_catalog, daemon=True).start()
    
    used = set()

    while True:
        # wait for timeout before setting new wallpaper
        sleep(config['wallpaper_change_timeout'])

        print("Setting wallpaper...")
        # fetch catalog
        catalog = read_catalog()

        # check if catalog exists
        if len(catalog) == 0:
            print("Waiting for catalog update...")
            continue

        # pick a random wallpaper
        choice = random.choice(catalog)

        # prevent reselections
        while choice in used or not os.path.exists(choice):
            choice = random.choice(catalog)

        used.add(choice)

        # prevent over-consumption
        if len(used) == len(used):
            used = set()
        
        # set as wallpaper
        set_wallpaper(choice)
        print("Wallpaper set!")



if __name__ == '__main__':
    main()
