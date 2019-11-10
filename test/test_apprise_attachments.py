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

import sys
import pytest
from os.path import getsize
from os.path import join
from os.path import dirname
from apprise.AppriseAttachment import AppriseAttachment
from apprise.AppriseAsset import AppriseAsset
from apprise.attachment.AttachBase import AttachBase
from apprise.attachment import SCHEMA_MAP as ATTACH_SCHEMA_MAP
from apprise.attachment import __load_matrix

# Disable logging for a cleaner testing output
import logging
logging.disable(logging.CRITICAL)

TEST_VAR_DIR = join(dirname(__file__), 'var')


def test_apprise_attachment():
    """
    API: AppriseAttachment basic testing

    """

    # Create ourselves an attachment object
    aa = AppriseAttachment()

    # There are no attachents loaded
    assert len(aa) == 0

    # Object can be directly checked as a boolean; response is False
    # when there are no entries loaded
    assert not aa

    # An attachment object using a custom Apprise Asset object
    aa = AppriseAttachment(asset=AppriseAsset())

    # still no attachments added
    assert len(aa) == 0

    # Add a file by it's path
    path = join(TEST_VAR_DIR, 'apprise-test.gif')
    assert aa.add(path)

    # There is now 1 attachment
    assert len(aa) == 1

    # we can test the object as a boolean and get a value of True now
    assert aa

    # Add another entry already in it's AttachBase format
    response = AppriseAttachment.instantiate(path)
    assert isinstance(response, AttachBase)
    assert aa.add(response, asset=AppriseAsset())

    # There is now 2 attachments
    assert len(aa) == 2

    # Reset our object
    aa = AppriseAttachment()

    # We can add by lists as well in a variety of formats
    attachments = (
        path,
        'file://{}?name=newfilename.gif'.format(path),
        AppriseAttachment.instantiate(
            'file://{}?name=anotherfilename.gif'.format(path)),
    )

    # Add them
    assert aa.add(attachments)

    # There is now 3 attachments
    assert len(aa) == 3

    # We can pop the last element off of the list as well
    attachment = aa.pop()
    assert isinstance(attachment, AttachBase)
    # we can test of the attachment is valid using a boolean check:
    assert attachment
    assert len(aa) == 2
    assert attachment.path == path
    assert attachment.name == 'anotherfilename.gif'
    assert attachment.mimetype == 'image/gif'

    # elements can also be directly indexed
    assert isinstance(aa[0], AttachBase)
    assert isinstance(aa[1], AttachBase)

    with pytest.raises(IndexError):
        aa[2]

    # We can iterate over attachments too:
    for count, a in enumerate(aa):
        assert isinstance(a, AttachBase)

        # we'll never iterate more then the number of entries in our object
        assert count < len(aa)

    # Get the file-size of our image
    expected_size = getsize(path) * len(aa)

    # verify that's what we get as a result
    assert aa.size() == expected_size

    # Attachments can also be loaded during the instantiation of the
    # AppriseAttachment object
    aa = AppriseAttachment(attachments)

    # There is now 3 attachments
    assert len(aa) == 3

    # Reset our object
    aa.clear()
    assert len(aa) == 0
    assert not aa

    # Garbage in produces garbage out
    assert aa.add(None) is False
    assert aa.add(object()) is False
    assert aa.add(42) is False

    # length remains unchanged
    assert len(aa) == 0

    # We can add by lists as well in a variety of formats
    attachments = (
        None,
        object(),
        42,
        'garbage://',
    )

    # Add our attachments
    assert aa.add(attachments) is False

    # length remains unchanged
    assert len(aa) == 0

    # test cases when file simply doesn't exist
    aa = AppriseAttachment('file://non-existant-file.png')
    # Our length is still 1
    assert len(aa) == 1
    # Our object will still return a True
    assert aa

    # However our indexed entry will not
    assert not aa[0]

    # length will return 0
    assert len(aa[0]) == 0

    # Total length will also return 0
    assert aa.size() == 0


def test_apprise_attachment_instantiate():
    """
    API: AppriseAttachment.instantiate()

    """
    assert AppriseAttachment.instantiate(
        'file://?', suppress_exceptions=True) is None

    assert AppriseAttachment.instantiate(
        'invalid://?', suppress_exceptions=True) is None

    class BadAttachType(AttachBase):
        def __init__(self, **kwargs):
            super(BadAttachType, self).__init__(**kwargs)

            # We fail whenever we're initialized
            raise TypeError()

    # Store our bad attachment type in our schema map
    ATTACH_SCHEMA_MAP['bad'] = BadAttachType

    with pytest.raises(TypeError):
        AppriseAttachment.instantiate(
            'bad://path', suppress_exceptions=False)

    # Same call but exceptions suppressed
    assert AppriseAttachment.instantiate(
        'bad://path', suppress_exceptions=True) is None


def test_apprise_attachment_matrix_load():
    """
    API: AppriseAttachment() matrix initialization

    """

    import apprise

    class AttachmentDummy(AttachBase):
        """
        A dummy wrapper for testing the different options in the load_matrix
        function
        """

        # The default descriptive name associated with the Notification
        service_name = 'dummy'

        # protocol as tuple
        protocol = ('uh', 'oh')

        # secure protocol as tuple
        secure_protocol = ('no', 'yes')

    class AttachmentDummy2(AttachBase):
        """
        A dummy wrapper for testing the different options in the load_matrix
        function
        """

        # The default descriptive name associated with the Notification
        service_name = 'dummy2'

        # secure protocol as tuple
        secure_protocol = ('true', 'false')

    class AttachmentDummy3(AttachBase):
        """
        A dummy wrapper for testing the different options in the load_matrix
        function
        """

        # The default descriptive name associated with the Notification
        service_name = 'dummy3'

        # secure protocol as string
        secure_protocol = 'true'

    class AttachmentDummy4(AttachBase):
        """
        A dummy wrapper for testing the different options in the load_matrix
        function
        """

        # The default descriptive name associated with the Notification
        service_name = 'dummy4'

        # protocol as string
        protocol = 'true'

    # Generate ourselves a fake entry
    apprise.attachment.AttachmentDummy = AttachmentDummy
    apprise.attachment.AttachmentDummy2 = AttachmentDummy2
    apprise.attachment.AttachmentDummy3 = AttachmentDummy3
    apprise.attachment.AttachmentDummy4 = AttachmentDummy4

    __load_matrix()

    # Call it again so we detect our entries already loaded
    __load_matrix()


def test_attachment_matrix_dynamic_importing(tmpdir):
    """
    API: Apprise() Attachment Matrix Importing

    """

    # Make our new path valid
    suite = tmpdir.mkdir("apprise_attach_test_suite")
    suite.join("__init__.py").write('')

    module_name = 'badattach'

    # Update our path to point to our new test suite
    sys.path.insert(0, str(suite))

    # Create a base area to work within
    base = suite.mkdir(module_name)
    base.join("__init__.py").write('')

    # Test no app_id
    base.join('AttachBadFile1.py').write(
        """
class AttachBadFile1(object):
    pass""")

    # No class of the same name
    base.join('AttachBadFile2.py').write(
        """
class BadClassName(object):
    pass""")

    # Exception thrown
    base.join('AttachBadFile3.py').write("""raise ImportError()""")

    # Utilizes a schema:// already occupied (as string)
    base.join('AttachGoober.py').write(
        """
from apprise import AttachBase
class AttachGoober(AttachBase):
    # This class tests the fact we have a new class name, but we're
    # trying to over-ride items previously used

    # The default simple (insecure) protocol
    protocol = 'http'

    # The default secure protocol
    secure_protocol = 'https'""")

    # Utilizes a schema:// already occupied (as tuple)
    base.join('AttachBugger.py').write("""
from apprise import AttachBase
class AttachBugger(AttachBase):
    # This class tests the fact we have a new class name, but we're
    # trying to over-ride items previously used

    # The default simple (insecure) protocol
    protocol = ('http', 'bugger-test' )

    # The default secure protocol
    secure_protocol = ('https', 'bugger-tests')""")

    __load_matrix(path=str(base), name=module_name)
