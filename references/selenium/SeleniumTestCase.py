import selenium_config
import unittest
from selenium import selenium
class SeleniumTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(SeleniumTestCase, self).__init__(methodName)
       
    def setUp(self):
        unittest.TestCase
        self.verificationErrors = []
        self.selenium = selenium(selenium_config.server_address, selenium_config.server_port, selenium_config.browser, selenium_config.initial_address)
        self.selenium.start()

    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)