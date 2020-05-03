import app
from bs4 import BeautifulSoup
import os
import requests
import shutil
from typing import List, Tuple


def find_urls(url: str) -> List[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """

    extension = app.urlhelpers.get_url_extension(url)

    # If the image in the url has a recognized file extension, this is a direct link to an image
    # (Should match artstation, i.imgur.com, i.redd.it, and other direct pages)
    if app.main.is_recognized(extension):
        return [url]

    # Imgur albums
    elif "imgur.com/a/" in url:
        return parse_imgur_album(url)

    # Imgur single-image pages
    elif "imgur.com" in url:
        return [parse_imgur_single(url)]

    # Unrecognized pages
    else:
        return []


def get_url_extension(url: str) -> str:
    """
    Gets the extension from the given url
    :param url: a direct link to an image
    :return: the file extension of the linked page
    """
    # https://stackoverflow.com/a/32651400
    r = requests.get(url, {'Content-type': 'content_type_value'})
    content_type = r.headers["Content-type"]
    return "." + content_type[(content_type.find("/") + 1):]


def parse_imgur_album(album_url: str) -> List[str]:
    """
    Scrapes the specified imgur album for direct links to each image
    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = requests.get(album_url)
    album_soup = BeautifulSoup(album_page.text, "html.parser")
    single_images = ["https://imgur.com/" + div["id"] for div in album_soup.select("div[class=post-images] > div[id]")]
    # Make a list of the direct links to the image hosted on each single-image page; return the list of all those images
    return [parse_imgur_single(link) for link in single_images]


def parse_imgur_single(url: str) -> str:
    """
    Scrapes regular imgur page for a direct link to the image displayed on that page
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def download_img_from(url: str, title: str, dir: str, png: bool = False, temp: str = "temp") -> bool:
    """
    Downloads the linked image, converts it to the specified filetype,
    and saves to the specified directory. Avoids name conflicts.
    :param url: url directly linking to the image to download
    :param title: title that the final file should have
    :param dir: directory that the final file should be saved to
    :return: True if the file was downloaded correctly, else False 
    """

    # Save the image to a temp directory
    try:
        download_image(title, url, temp)
    except ConnectionError:
        return False

    # Convert to png if necessary
    if png:
        app.filehelpers.convert_file(temp, ".png")
        extension = ".png"
        temp_path = os.path.join(temp, title + extension)

    # Move to desired directory
    final_filename = app.filehelpers.prevent_conflicts(title, extension, dir)
    final_filepath = os.path.join(dir, final_filename)
    shutil.move(temp_path, final_filepath)

    return True


def download_image(url: str, directory: str, title: str) -> None:
    """
    Saves the specified image to the specified path with the specified title and file extension
    :param url: a direct link to the image to be saved
    :param directory: the path the image should be saved to
    :param title: the title the image file should have (sans extension)
    :return: None
    """

    image = requests.get(url)

    # The image page couldn't be reached
    if image.status_code != 200:
        return ConnectionError('Request failed with error {0}.'.format(image.status_code))

    # Output path
    app.filehelpers.create_directory(directory)

    filepath = os.path.join(directory, title + get_url_extension(url))

    # Write the file
    with open(filepath, "wb") as f:
        f.write(image.content)

    return