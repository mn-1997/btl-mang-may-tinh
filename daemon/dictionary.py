#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

# Python 3.10+ moved MutableMapping from collections to collections.abc
from collections.abc import MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """
    A dictionary where keys aren't case-sensitive. 
    Useful for HTTP headers (e.g., 'Content-Type' vs 'content-type').
    """

    def __init__(self, *args, **kwargs):
        # Store all keys in lowercase so lookups are case-insensitive
        self.store = {k.lower(): v for k, v in dict(*args, **kwargs).items()}

    def __getitem__(self, key):
        return self.store[key.lower()]

    def __setitem__(self, key, value):
        self.store[key.lower()] = value

    def __delitem__(self, key):
        del self.store[key.lower()]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __contains__(self, key):
        # Check if key exists (ignores case)

        return key.lower() in self.store

    def __repr__(self):
        return str(self.store)

    def get(self, key, default=None):
        # Safe lookup with a default value

        try:
            return self[key]
        except KeyError:
            return default