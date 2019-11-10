# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import six

from . import attachment
from . import AttachBase
from . import URLBase
from .AppriseAsset import AppriseAsset
from .logger import logger
from .utils import GET_SCHEMA_RE


class AppriseAttachment(object):
    """
    Our Apprise Attachment File Manager

    """

    def __init__(self, paths=None, asset=None, **kwargs):
        """
        Loads all of the paths/urls specified (if any).

        The path can either be a single string identifying one explicit
        location, otherwise you can pass in a series of locations to scan
        via a list.
        """

        # Initialize our attachment listings
        self.attachments = list()

        # Prepare our Asset Object
        self.asset = \
            asset if isinstance(asset, AppriseAsset) else AppriseAsset()

        # Now parse any paths specified
        if paths is not None:
            # Store our path(s)
            self.add(paths)

    def add(self, attachments, asset=None, db=None):
        """
        Adds one or more attachments into our list.

        """
        # Initialize our return status
        return_status = True

        if isinstance(asset, AppriseAsset):
            # prepare default asset
            asset = self.asset

        if isinstance(attachments, AttachBase):
            # Go ahead and just add our attachments into our list
            self.attachments.append(attachments)
            return True

        elif isinstance(attachments, six.string_types):
            # Save our path
            attachments = (attachments, )

        elif not isinstance(attachments, (tuple, set, list)):
            logger.error(
                'An invalid attachment url (type={}) was '
                'specified.'.format(type(attachments)))
            return False

        # Iterate over our attachments
        for _attachment in attachments:

            if isinstance(_attachment, AttachBase):
                # Go ahead and just add our attachment into our list
                self.attachments.append(_attachment)
                continue

            elif not isinstance(_attachment, six.string_types):
                logger.warning(
                    "An invalid attachment (type={}) was specified.".format(
                        type(_attachment)))
                return_status = False
                continue

            logger.debug("Loading attachment: {}".format(_attachment))

            # Instantiate ourselves an object, this function throws or
            # returns None if it fails
            instance = AppriseAttachment.instantiate(_attachment, asset=asset)
            if not isinstance(instance, AttachBase):
                return_status = False
                continue

            # Add our initialized plugin to our server listings
            self.attachments.append(instance)

        # Return our status
        return return_status

    @staticmethod
    def instantiate(url, asset=None, suppress_exceptions=True):
        """
        Returns the instance of a instantiated attachment plugin based on
        the provided Attachment URL.  If the url fails to be parsed, then None
        is returned.

        """
        # Attempt to acquire the schema at the very least to allow our
        # attachment based urls.
        schema = GET_SCHEMA_RE.match(url)
        if schema is None:
            # Plan B is to assume we're dealing with a file
            schema = attachment.AttachFile.protocol
            url = '{}://{}'.format(schema, URLBase.quote(url))

        else:
            # Ensure our schema is always in lower case
            schema = schema.group('schema').lower()

            # Some basic validation
            if schema not in attachment.SCHEMA_MAP:
                logger.warning('Unsupported schema {}.'.format(schema))
                return None

        # Parse our url details of the server object as dictionary containing
        # all of the information parsed from our URL
        results = attachment.SCHEMA_MAP[schema].parse_url(url)

        if not results:
            # Failed to parse the server URL
            logger.warning('Unparseable URL {}.'.format(url))
            return None

        # Prepare our Asset Object
        results['asset'] = \
            asset if isinstance(asset, AppriseAsset) else AppriseAsset()

        if suppress_exceptions:
            try:
                # Attempt to create an instance of our plugin using the parsed
                # URL information
                attach_plugin = \
                    attachment.SCHEMA_MAP[results['schema']](**results)

            except Exception:
                # the arguments are invalid or can not be used.
                logger.warning('Could not load URL: %s' % url)
                return None

        else:
            # Attempt to create an instance of our plugin using the parsed
            # URL information but don't wrap it in a try catch
            attach_plugin = attachment.SCHEMA_MAP[results['schema']](**results)

        return attach_plugin

    def clear(self):
        """
        Empties our attachment list

        """
        self.attachments[:] = []

    def size(self):
        """
        Returns the total size of accumulated attachments
        """
        return sum([len(a) for a in self.attachments if len(a) > 0])

    def pop(self, index=-1):
        """
        Removes an indexed Apprise Attachment from the stack and returns it.

        by default the last element is poped from the list
        """
        # Remove our entry
        return self.attachments.pop(index)

    def __getitem__(self, index):
        """
        Returns the indexed entry of a loaded apprise attachments
        """
        return self.attachments[index]

    def __bool__(self):
        """
        Allows the Apprise object to be wrapped in an Python 3.x based 'if
        statement'.  True is returned if at least one service has been loaded.
        """
        return True if self.attachments else False

    def __nonzero__(self):
        """
        Allows the Apprise object to be wrapped in an Python 2.x based 'if
        statement'.  True is returned if at least one service has been loaded.
        """
        return True if self.attachments else False

    def __iter__(self):
        """
        Returns an iterator to our attachment list
        """
        return iter(self.attachments)

    def __len__(self):
        """
        Returns the number of attachment entries loaded
        """
        return len(self.attachments)
