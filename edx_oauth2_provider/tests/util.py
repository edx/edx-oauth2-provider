# pylint: disable=missing-docstring
import os.path
import urlparse


def normpath(url):
    """Get the normalized path of a URL"""
    return os.path.normpath(urlparse.urlparse(url).path)
