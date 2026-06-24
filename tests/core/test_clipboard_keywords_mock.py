
import base64
import unittest
import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock

from AppiumLibrary.keywords._applicationmanagement import _ApplicationManagementKeywords


# A few bytes that are NOT valid UTF-8 (PNG signature) so the image path
# would crash if it were treated as text.
PNG_BYTES = b'\x89PNG\r\n\x1a\n' + b'fakeimagedata'
PNG_B64 = base64.b64encode(PNG_BYTES).decode('utf-8')


class TestClipboardKeywordsMock(unittest.TestCase):

    def setUp(self):
        self.am = _ApplicationManagementKeywords()
        self.am._log_level = 'DEBUG'
        self.am._info = MagicMock()
        self.driver = MagicMock()
        self.am._current_application = MagicMock(return_value=self.driver)

    def _sent_b64(self):
        """Return the b64Content sent to the driver on the last setClipboard call."""
        name, kwargs = self.driver.execute_script.call_args
        return name[1]['b64Content']

    # ---- set: plaintext ----

    def test_set_plaintext_encodes_utf8(self):
        self.am.appium_set_clipboard("Hello World")
        self.assertEqual(self._sent_b64(),
                         base64.b64encode("Hello World".encode('utf-8')).decode('utf-8'))

    def test_set_plaintext_no_encode_passes_through(self):
        self.am.appium_set_clipboard("already-b64", encode_base64=False)
        self.assertEqual(self._sent_b64(), "already-b64")

    # ---- set: image ----

    def test_set_image_bytes_are_b64_encoded_once(self):
        self.am.appium_set_clipboard(PNG_BYTES, content_type='image')
        # Driver must receive base64-of-PNG-bytes; one decode -> PNG bytes.
        self.assertEqual(self._sent_b64(), PNG_B64)
        self.assertEqual(base64.b64decode(self._sent_b64()), PNG_BYTES)

    def test_set_image_b64_string_passes_through(self):
        # Already-base64 PNG string must NOT be double-encoded.
        self.am.appium_set_clipboard(PNG_B64, content_type='image')
        self.assertEqual(self._sent_b64(), PNG_B64)
        self.assertEqual(base64.b64decode(self._sent_b64()), PNG_BYTES)

    def test_set_image_png_alias(self):
        self.am.appium_set_clipboard(PNG_BYTES, content_type='image/png')
        name, kwargs = self.driver.execute_script.call_args
        self.assertEqual(name[1]['contentType'], 'image')

    # ---- get: plaintext ----

    def test_get_plaintext_decodes(self):
        self.driver.execute_script.return_value = \
            base64.b64encode("Hi".encode('utf-8')).decode('utf-8')
        self.assertEqual(self.am.appium_get_clipboard(), "Hi")

    # ---- get: image ----

    def test_get_image_returns_png_bytes(self):
        self.driver.execute_script.return_value = PNG_B64
        result = self.am.appium_get_clipboard(content_type='image')
        # Must NOT crash on .decode('utf-8'); returns raw PNG bytes.
        self.assertEqual(result, PNG_BYTES)

    def test_get_image_no_decode_returns_b64_string(self):
        self.driver.execute_script.return_value = PNG_B64
        result = self.am.appium_get_clipboard(content_type='image', decode_base64=False)
        self.assertEqual(result, PNG_B64)


if __name__ == '__main__':
    unittest.main()
