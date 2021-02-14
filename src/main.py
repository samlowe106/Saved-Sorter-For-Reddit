from utils import files, strings
from utils.submission_wrapper import SubmissionWrapper
import argparse
import getpass
import os
from prawcore.exceptions import OAuthException
import praw
from praw import Reddit
from typing import List, Optional, Tuple


# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


temp_dir = "temp"
log_directory = "Logs"
log_path = os.path.join("Logs", "log.txt")
info_path = "info.txt"


def main() -> None:
    """
    Scrapes and downloads any images from posts in the user's saved posts category on Reddit
    """

    if (reddit := sign_in(info_path)) is None:
        print("Unrecognized username or password.")
        return

    files.create_directory(temp_dir)
    files.create_directory(args.directory)    
    files.create_directory(log_directory)

    index = 0
    for post in reddit.user.me().saved():

        post = SubmissionWrapper(post, args.directory, args.png)
        
        if post.url_tuples:

            index += 1

            if not args.nolog:
                post.log(log_path)

            post.print_self(index)

            post.unsave()
            
            # End if the desired number of posts have had their images downloaded
            if index >= args.limit:
                break
    
    cleanup()


def cleanup():
    """ End-of-program cleanup """
    os.rmdir(temp_dir)

    """
    if incompatible_domains:
        print("\nSeveral domains were unrecognized:")
        for domain in sorted(incompatible_domains.items(), key=lambda x: x[1], reverse=True):
            print("\t{0}: {1}".format(domain[0], domain[1]))
    """


def sign_in(filepath: str) -> Optional[Reddit]:
    """
    Attempts to sign into Reddit
    :param filepath: Path to the text file containing the client ID and client secret
    :return: reddit object if successful, else None
    """
    try:
        with open(filepath, 'r') as info_file:
            client_id = info_file.readline()
            client_secret = info_file.readline()
    except FileNotFoundError:
        print(f"The client info file couldn't be found at {filepath}")
        return
    
    # praw returns an invalid reddit instance if the  client id or client secret are ""
    if not client_id:
        print("Client ID is blank!")
        return
    if not client_secret:
        print("Client Secret is blank!")
        return

    # getpass only works through the command line!
    if (username := input("Username: ")) and (password := getpass.getpass("Password: ")):
        print("Signing in...", end="")
        try:
            return praw.Reddit(client_id=client_id,
                            client_secret=client_secret,
                            user_agent='PaperScraper',
                            username=username,
                            password=password)
        except OAuthException:
            return


def read_client_info(filepath: str = "info.txt") -> Tuple[str, str]:
    """
    Reads the client ID and client secret from the specified file
    :param filepath: filepath of the file to read the client id and secret from
    :return: tuple containing the client ID and secret in that order
    :raises: FileNotFoundError, ValueError
    """


if __name__ == "__main__":

    # region Argument Parsing

    parser = argparse.ArgumentParser(
        description="Scrapes images from the user's saved posts on Reddit")
    parser.add_argument("-l",
                        "--limit",
                        type=int,
                        default=1000,
                        help="max number of images to download")
    parser.add_argument("-d",
                        "--directory",
                        type=str,
                        default="Output",
                        help="directory that files should be saved to")
    parser.add_argument("-t",
                        "--titlecase",
                        action='store_true',
                        help="saves filenames in title case")
    parser.add_argument("-p",
                        "--png",
                        action='store_true',
                        help="convert .jpg/.jpeg files to .png files")

    """
    NOT YET IMPLEMENTED
    
    parser.add_argument("-n",
                        "--name",
                        action='store_false',
                        help="append OP's name to the filename")

    parser.add_argument("-s",
                        "--sort",
                        action='store_false',
                        help="sort images into folders by subreddit")

    parser.add_argument("--nolog",
                        action='store_true',
                        help="disable logging")
    """

    args = parser.parse_args()

    # endregion

    main()
