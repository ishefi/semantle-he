from unittest import TestCase
from mock import patch


class HsTestCase(TestCase):
    def patch(self, target, *args, **kwargs):
        patcher = patch(target, *args, **kwargs)
        mocker = patcher.start()
        self.addCleanup(lambda p: p.stop(), patcher)
        return mocker
