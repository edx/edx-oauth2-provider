# pylint: disable=missing-docstring
from __future__ import absolute_import, division, print_function, unicode_literals


class DummyHandler(object):
    def scope_profile(self, data):  # pylint: disable=unused-argument
        return ['test']

    def claim_test(self, data):
        """
        Test claim.

        Only has a value if the claim request has essential=True. The
        value is range(10), or the intersection with the values in the
        claims request if any.

        """
        if data.get('essential'):
            values = range(10)
            if data.get('values'):
                values = list(set(values) & set(data.get('values')))
            return values
        return None
