"""
Util methods for testing.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

import six.moves.urllib.parse  # pylint: disable=import-error


def normpath(url):
    """Get the normalized path of a URL"""
    return os.path.normpath(six.moves.urllib.parse.urlparse(url).path)
