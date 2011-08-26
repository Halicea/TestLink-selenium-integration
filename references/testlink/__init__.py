#! /usr/bin/python
"""
Testlink API Sample Python 2.x Client implementation
"""
import xmlrpclib
import testlink_config
class TestlinkAPIClient:        
    # substitute your server URL Here
    SERVER_URL = testlink_config.SERVER_URL
    
    def __init__(self):
        self.server = xmlrpclib.Server(self.SERVER_URL)
        self.devKey = testlink_config.DEV_KEY

    def reportTCResult(self, tcid, tpid, buildid, status):
        data = {"devKey":self.devKey, "testcaseid":tcid, "testplanid":tpid, 
        "buildid":buildid, "status":status} 
        return self.server.tl.reportTCResult(data)
    def getProjects(self):
        return self.server.tl.getProjects(dict(devKey=self.devKey))
    def getInfo(self):
        return self.server.tl.about()
    

def test():
    # substitute your Dev Key Here
    client = TestlinkAPIClient("1da8171e4663c80844870ecf9e36f4de")
    # get info about the server
    print client.getInfo()
    # Substitute for tcid and tpid that apply to your project
    result = client.reportTCResult(41112, 42294, 245, "f")
    # Typically you'd want to validate the result here and probably do something more useful with it
    print "reportTCResult result was: %s" %(result)
