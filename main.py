import argparse
from getpass import getpass
from os import chdir
from os import listdir
from os import makedirs
from os import remove
from os.path import exists
from os.path import splitext
from sys import argv
from time import gmtime
from time import strftime
from urllib.parse import urlparse

import praw                         # PRAW
import prawcore.exceptions          # PRAW

from bs4 import BeautifulSoup       # bs4
from PIL import Image               # Pillow
from requests import get            # Requests


# region Globals

# region Constants

# Current date (in Greenwich Mean Time) formatted in month-day-year
DATE = strftime("%m-%d-%y", gmtime())

# Directory where images will be saved
DIRECTORY = DATE + "\\"

# Directory where logs will be stored
LOG_DIRECTORY = DIRECTORY + "Logs\\"

# Log of all urls from which image(s) were downloaded
LOG = LOG_DIRECTORY + "Log.txt"

# List of currently unrecognized links (so compatibility can be added later)
INCOMPATIBLE_DOMAIN_LOG = LOG_DIRECTORY + "Incompatible URL Log.txt"

# Character that Windows won't allow in a filename
INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|"]

# File extensions that this program should recognize
RECOGNIZED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif"]

# True if the user would like all jpg images converted into png images, else false
PNG_PREFERRED = False

USAGE = "Usage: ./ssfr username [args]"

LOGGING = True

SORT = False

ADD_POSTER_NAME = False

TITLE = True

with open("info.txt", 'r') as info_file:
    CLIENT_ID = info_file.readline()
    CLIENT_SECRET = info_file.readline()

# endregion

# Dictionary of domains incompatible with the program in the form domain (str) : number of appearances (int)
incompatible_domains = {}

# endregion

# region Initiation

parser = argparse.ArgumentParser(description="Scrapes images from the user's saved posts on Reddit")
parser.add_argument("limit", metavar='L', type=int, help="max number of images to download")
parser.addargument("sort", metavar="s")

args = parser.parse_args()

# (str) : (str) dictionary of commands (key) and their corresponding descriptions (val)
COMMANDS = {"-png": "Convert all JPG/JPEG images to PNG images",
            "-dir=": "Set the output directory",
            "-nolog": "Disable logging (not recommended!)",
            "-sort": "Place all images into folders named after the subreddits they were downloaded from",
            "-name": "Append the OP's name to the end of file names",
            "-t": "Put file names in title case",
            "-lim=": "Specify how many files should be downloaded (default is limitless)"
            }

# endregion


def attempt_sign_in():
    """
    Prompts the user to sign in

    :return: Reddit object
    """
    while True:
        username = input("Username: ")
        password = getpass("Password: ") # Only works through the command line!

        print("Signing in...", end="")
        reddit = sign_in(username, password)

        # If login was successful, continue with the program
        if reddit is not None:
            print("signed in as " + str(reddit.user.me()) + ".\n")
            break

        print("unrecognized username or password.\n")

    return reddit


def create_directory(dirpath: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param dirpath: name of the directory
    :return:
    """
    if not exists(dirpath):
        makedirs(dirpath)
    return


def parse_clas():
    """
    Parses optional CLAs
    :return:
    """
    # TODO: refactor!
    # Parse optional arguments
    if len(argv) > 2:
        for i in range(2, len(argv)):
            # The user prefers png images to jpg images
            if str(argv[i]).lower() == "-png":
                PNG_PREFERRED = True

            # The user has specified the download directory
            elif str(argv[i]).lower().startswith("-dir="):
                working_directory = [i][5:]

            # The user has disabled logging
            elif str(argv[i]).lower() == "-nolog":
                LOGGING = False

            # The user wants images placed into folders by subreddit
            elif str(argv[i]).lower() == "-sort":
                SORT = True

            # The user wants the image poster's name appended to the end of file names
            elif str(argv[i]).lower() == "-name":
                ADD_POSTER_NAME = True

            # The user wants file names in title case
            elif str(argv[i]).lower() == "-t":
                TITLE = True

            # The user wants file names in title case
            elif str(argv[i]).lower() == "-lim=":
                try:
                    download_limit = int(argv[i][5:])
                except ValueError:
                    print("lim must be an int!")

    return


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit

    :return:
    """

    global PNG_PREFERRED, LOGGING, SORT, ADD_POSTER_NAME, TITLE

    # Tentative working directory
    working_directory = "Output\\"
    # Tentative download limit
    download_limit = -1

    reddit = attempt_sign_in()

    parse_clas()

    # Make directories
    create_directory(working_directory)
    chdir(working_directory)
    create_directory(LOG_DIRECTORY)

    # Retrieve saved posts
    saved_posts = reddit.redditor(str(reddit.user.me())).saved()

    # Loop through saved posts
    index = 0
    for post in saved_posts:

        # Sanitize the post
        post = sanitize_post(post)

        # Move on if the post is just a selfpost or link to a reddit thread
        if post.is_self or "https://reddit.com/" in post.url:
            continue

        # Increase the index
        index += 1

        # Parse the image link
        post.images_downloaded = [download_image(post.title, url, DIRECTORY) for url in post.recognized_urls]

        # Log the post
        log_url(post.title, post.url, images_downloaded != [])

        # Unsave the post
        post.unsave()

        # If we've downloaded as many issues as desired, break out
        if index >= download_limit > 0:
            break

    print_unrecognized_domains()

    """ End-of-program cleanup goes here """

    return


def print_post_info(index: int, post) -> None:
    """
    Prints out information about the specified post

    :param index: the index number of the post
    :param post: a post object
    :return: None
    """
    print("\n{0}. {1}".format(index, post.title))
    print("   r/" + str(post.subreddit))
    print("   " + post.url)
    for image in post.downloaded_images:
        print("   Saved as " + image)
    return


def print_unrecognized_domains() -> None:
    """
    Prints unrecognized domains (so compatibility can be added later)
    :return: None
    """
    if len(incompatible_domains) > 0:
        print()
        print("Several domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))
    return


def download_image(title: str, url: str, path: str) -> str:
    """
    Attempts to download an image from the given url to a file with the specified title

    :param title: Desired title of the image file
    :param url: A URL containing a direct link to the image to be downloaded
    :param path: The filepath that the file should be saved to
    :return: filepath that the image was downloaded to, empty string if failed
    :raises: IOError, FileNotFoundError
    """

    # Try to download image data
    image = get(url)

    # If the image page couldn't be reached, return an empty string for failure
    if image.status_code != 200:
        print("\nERROR: Couldn't retrieve image from " + url + " , skipping...")
        return ""

    # Remove any query strings with split, then find the file extension with splitext
    file_extension = splitext(url.split('?')[0])[1]

    # If the file extension is unrecognized, don't try to download the file
    if file_extension not in RECOGNIZED_EXTENSIONS:
        return ""

    # Set up the output path if it doesn't already exist
    if not exists(path):
        makedirs(path)

    # Define a working filename
    file_title = retitle(title, TITLE)

    # Start a loop (prevents this file from overwriting another with the same name by adding (i) before the extension)
    for i in range(len(listdir(path)) + 1):

        # Insert a number in the filename to prevent conflicts
        if i > 0:
            file_title = "{0} ({1})".format(file_title, i)

        # If no files share the same name, write the file
        if (file_title + file_extension) not in listdir(path):

            # Write the file
            with open(path + file_title + file_extension, "wb") as File:
                for chunk in image.iter_content(4096):
                    File.write(chunk)

            # If the user prefers PNG images and the file is a jpg, re-save it as a png
            if PNG_PREFERRED and file_extension == ".jpg":
                im = Image.open(path + file_title + file_extension)
                file_extension = ".png"
                rgb_im = im.convert('RGB')
                rgb_im.save(path + file_title + file_extension)
                # Delete the previous jpg file
                remove(path + file_title + ".jpg")

            # Return the final name of the file (means it was successfully downloaded there)
            return file_title + file_extension


def find_urls(url: str) -> list:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages

    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    # If the URL (without query strings) ends with any recognized file extension, this is a direct link to an image
    # Should match artstation, i.imgur.com, i.redd.it, and other pages
    for extension in RECOGNIZED_EXTENSIONS:
        if url.split('?')[0].endswith(extension):  # .split() removes any query strings from the URL
            return [url]

    # Imgur albums
    if "imgur.com/a/" in url:
        return parse_imgur_album(url)

    # Imgur single-image pages
    elif "imgur.com" in url:
        return [parse_imgur_single(url)]

    return []


def parse_imgur_album(album_url: str) -> list:
    """
    Scrapes the specified imgur album for direct links to each image

    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = get(album_url)
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
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]


def retitle(current_string: str, title_case: bool) -> str:
    """
    Capitalizes the first letter in each word, strips non-ASCII characters and characters Windows doesn't support in
    file names, and removes any preceding or trailing periods and spaces. Optionally enforces title case

    :param current_string: the current string
    :param title_case: True if the returned string should be in title case, else False
    :return: valid file name with no leading or trailing spaces, periods, or commas
    """
    # Recapitalize the title and remove any incompatible characters
    new_string = ""
    # Replace non-ASCII characters with a space
    for i, char in enumerate(current_string):
        if char not in INVALID_CHARS:
            # Replace " with '
            if char == '"':
                new_string += "'"
            # If desired, enforce title case
            elif title_case and (i == 0 or current_string[i - 1] == ' '):
                new_string += (char.upper())
            # Prevent consecutive spaces
            elif char == ' ' and current_string[i - 1] == ' ':
                pass
            else:
                new_string += char

    # If the string is too long, limit it to the first sentence
    if len(new_string) > 250:
        new_string = new_string.split('.', 1)[0]
        # If the string is still too long, truncate it
        if len(new_string) > 250:
            new_string = new_string[:250]

    # Remove any trailing periods or spaces
    while new_string.endswith('.') or new_string.endswith(',') or new_string.endswith(' '):
        new_string = new_string[:-1]

    # Remove any preceding periods, spaces, or commas
    while new_string.startswith('.') or new_string.startswith(',') or new_string.startswith(' '):
        new_string = new_string[1:]

    return new_string


def sanitize_post(post):
    """
    Adds is_comment properties to posts and is_self property to comments, and finds valid urls in non-self posts

    :param post: a post object
    :return: the same post with edited data to prevent errors
    """

    # If the post links somewhere, find scrape-able images
    if hasattr(post, 'title'):
        post.is_comment = False
        post.recognized_urls = find_urls(post.url)

    # If the post is a comment, mark it as a selfpost
    else:
        post.is_self = True
        post.is_comment = True

    return post


def sign_in(username: str, password: str):
    """
    Attempts to sign into Reddit taking the first two CLAs

    :param username: The user's username
    :param password: The user's password
    :return: reddit object if successful, else None
    """

    # Don't bother trying to sign in if username or password are blank
    #  (praw has a stack overflow without this check!)
    if username == "" or password == "":
        return None

    # Try to sign in
    try:
        reddit = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent='Saved Sorter',
                             username=username,
                             password=password)
        return reddit
    except prawcore.exceptions.OAuthException:
        return None


def log_url(title: str, url: str, compatible: bool) -> None:
    """
    Writes the given title and url to the specified file, and  adds the url's domain to
    the dictionary of incompatible domains

    :param title: title of the post to be logged
    :param url: the post's URL
    :param compatible: whether the post was compatible with this program or not
    :return: nothing
    """

    with open(LOG, "a", encoding="utf-8") as log_file:
        log_file.write(title + " : " + url + " : " + str(compatible) + '\n')

    # If the url was incompatible, update the log of incompatible domains
    if not compatible:

        # Establish the post's domain
        uri = urlparse(url)
        domain = '{0}://{1}'.format(uri.scheme, uri.netloc)

        # Save that domain to a dictionary
        if domain in incompatible_domains.keys():
            incompatible_domains[domain] += 1
        else:
            incompatible_domains[domain] = 1

        # Update the log file
        with open(INCOMPATIBLE_DOMAIN_LOG, "a") as incompatible_domain_log_file:
            for domain in incompatible_domains.keys():
                incompatible_domain_log_file.write(domain + " : " + str(incompatible_domains[domain]) + "\n")

    return


if __name__ == "__main__":
    main()
