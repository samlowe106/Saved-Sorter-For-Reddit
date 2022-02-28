from src.models.parsers import *
from typing import List, Tuple


# https://www.reddit.com/r/wallpaper/comments/obzf75/3840x2160_steam_summer_sale_2021_wallpapers/
# reddit added image albums

single_image_parser = SingleImageParser()
imgur_parser = ImgurParser()

unrecognizable = []

imgur_singles = []
imgur_albums = []
imgur_gallaries = []

reddit_singles = []
artstation_singles = []
deviantart_singles = []
single_image_recognizable = imgur_singles + reddit_singles + artstation_singles + deviantart_singles

flickr_recognizable = []
flickr_unrecognizable = []

gfycat_recognizable = []
gfycat_unrecognizable = []

imgur_recognizable = imgur_singles + imgur_albums + imgur_gallaries
imgur_unrecognizable = flickr_recognizable + gfycat_recognizable

single_image_unrecognizable = imgur_albums + flickr_recognizable + gfycat_recognizable


def test_parser_recognizes(self, parser: IParser, expected_recognizable: List[Response], expected_unrecognizable: List[Response]):
    """
    for url in expected_recognizable:
        self.assertTrue(imgur_parser.recognizes())

    for string in expected_unrecognizable + unrecognizable:
        self.assertFalse(imgur_parser.recognizes(string))
    """


def test_parser_parses(self, parser: IParser, responses_expected: Tuple[Response, Set[str]]):
    # TODO
    for r, expected in responses_expected:
        self.assertEqual(expected, parser.parse(r))



def test_SingleImageParser(self):
    # TODO
    pass


def test_ImgurParser(self):
    test_parser_recognizes(self, imgur_parser, imgur_singles + imgur_albums + imgur_gallaries, imgur_unrecognizable)
    # test_parser_parses(self, imgur_parser, )



def test_FlickrParser(self):
    # TODO
    pass




"""
def test_recognized(self):
    self.assertTrue(urls.recognized(".png"))
    self.assertTrue(urls.recognized(".PnG"))
    self.assertTrue(urls.recognized(".PNG"))
    self.assertTrue(urls.recognized(".jpg"))
    self.assertTrue(urls.recognized(".jpeg"))
    self.assertTrue(urls.recognized(".gif"))

    self.assertFalse(urls.recognized("bar"))
    self.assertFalse(urls.recognized(".foo"))
    self.assertFalse(urls.recognized("arbitrary"))
    self.assertFalse(urls.recognized("gif"))
    self.assertFalse(urls.recognized("png"))
    self.assertFalse(urls.recognized("file.png"))
"""

"""
def test_parse_imgur_album(self):
    self.assertEqual(["https://i.imgur.com/NVQ1nuu.png",
                        "https://i.imgur.com/rDQ6BEA.jpg",
                        "https://i.imgur.com/gIMtb0Z.png",
                        "https://i.imgur.com/GeZmbJA.png",
                        "https://i.imgur.com/AGWHnX0.jpg",
                        "https://i.imgur.com/yt86fMB.jpg",
                        "https://i.imgur.com/cG9eXMk.jpg",
                        "https://i.imgur.com/4gdcscj.jpg",
                        "https://i.imgur.com/uA1NSv3.png"],
                        urls.parse_imgur_album("https://imgur.com/a/rSZlZ"))

    self.assertEqual(["https://i.imgur.com/oPXMrnr.png",
                        "https://i.imgur.com/Au8PAtj.png"],
                        urls.parse_imgur_album("https://imgur.com/gallery/NXBcU"))

    self.assertEqual(["https://i.imgur.com/zkREZI9.jpg",
                        "https://i.imgur.com/Qj7oouc.jpg",
                        "https://i.imgur.com/EthO1mq.jpg",
                        "https://i.imgur.com/xD1f2tb.jpg",
                        "https://i.imgur.com/TGMnQ51.jpg",
                        "https://i.imgur.com/3EXJq2A.jpg",
                        "https://i.imgur.com/KREPkFn.jpg",
                        "https://i.imgur.com/rc0ZVRv.jpg",
                        "https://i.imgur.com/G9pYJ0J.jpg",
                        "https://i.imgur.com/n4YRzTE.jpg",
                        "https://i.imgur.com/MU26NEH.jpg",
                        "https://i.imgur.com/NrmQqQt.jpg",
                        "https://i.imgur.com/iJBMppF.jpg",
                        "https://i.imgur.com/Id2wt99.jpg",
                        "https://i.imgur.com/It96Qrx.jpg"],
                        urls.parse_imgur_album("https://imgur.com/a/uZJHE"))
"""

"""
def test_parse_imgur_single(self):
    self.assertEqual("https://i.imgur.com/jTAD7G1.jpg",
                        urls.parse_imgur_single("https://imgur.com/r/Wallpapers/jTAD7G1"))
    self.assertEqual("https://i.imgur.com/WVntmOE.jpg",
                        urls.parse_imgur_single("https://imgur.com/r/Wallpapers/WVntmOE"))
    self.assertEqual("https://i.imgur.com/rzOOFgI.jpg",
                        urls.parse_imgur_single("https://imgur.com/r/Wallpapers/rzOOFgI"))
    self.assertEqual("https://i.imgur.com/mtjTo2o.jpg",
                        urls.parse_imgur_single("https://imgur.com/r/Wallpapers/mtjTo2o"))
    self.assertEqual("https://i.imgur.com/mgfgDYb.jpg",
                        urls.parse_imgur_single("https://imgur.com/r/Wallpapers/mgfgDYb"))
"""

"""
def test_find_urls(self):
    url_tups = [("https://imgur.com/a/rSZlZ",              ["https://i.imgur.com/NVQ1nuu.png",
                                                            "https://i.imgur.com/rDQ6BEA.jpg",
                                                            "https://i.imgur.com/gIMtb0Z.png",
                                                            "https://i.imgur.com/GeZmbJA.png",
                                                            "https://i.imgur.com/AGWHnX0.jpg",
                                                            "https://i.imgur.com/yt86fMB.jpg",
                                                            "https://i.imgur.com/cG9eXMk.jpg",
                                                            "https://i.imgur.com/4gdcscj.jpg",
                                                            "https://i.imgur.com/uA1NSv3.png"]),
                ("https://imgur.com/gallery/NXBcU",        ["https://i.imgur.com/oPXMrnr.png",
                                                            "https://i.imgur.com/Au8PAtj.png"]),
                ("https://imgur.com/r/Wallpapers/jTAD7G1", ["https://i.imgur.com/jTAD7G1.jpg"]),
                ("https://imgur.com/r/Wallpapers/WVntmOE", ["https://i.imgur.com/WVntmOE.jpg"]),
                ("https://imgur.com/r/Wallpapers/rzOOFgI", ["https://i.imgur.com/rzOOFgI.jpg"]),
                ("https://imgur.com/r/Wallpapers/mtjTo2o", ["https://i.imgur.com/mtjTo2o.jpg"]),
                ("https://imgur.com/r/Wallpapers/mgfgDYb", ["https://i.imgur.com/mgfgDYb.jpg"])
    ]

    for url, expected in url_tups:
        r = requests.get(url)
        if r.status_code == 200:
            self.assertEqual(expected, urls.find_urls(r))
"""