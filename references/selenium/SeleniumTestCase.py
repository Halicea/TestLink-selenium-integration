import selenium_config
import unittest
from selenium import selenium
class SeleniumTestCase(unittest.TestCase):
    server_address = selenium_config.server_address
    server_port = selenium_config.server_port
    browser = selenium_config.browser
    initial_address = selenium_config.initial_address
    def __init__(self, methodName='runTest'):
        super(SeleniumTestCase, self).__init__(methodName)
    def setUp(self):
        unittest.TestCase
        self.verificationErrors = []
        self.selenium = selenium(self.server_address, self.server_port, self.browser, self.initial_address)
        self.selenium.start()

    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)