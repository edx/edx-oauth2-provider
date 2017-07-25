"""
Util methods for testing.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os.path
import urlparse


def normpath(url):
    """Get the normalized path of a URL"""
    return os.path.normpath(urlparse.urlparse(url).path)
