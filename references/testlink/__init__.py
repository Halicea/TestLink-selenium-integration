#! /usr/bin/python
"""
Testlink API Sample Python 2.x Client implementation
"""
import xmlrpclib
import testlink_config
class TestlinkAPIClient:
    def __init__(self, server=None, devKey=None):
        self.SERVER_URL = server or testlink_config.SERVER_URL
        self.server = xmlrpclib.Server(self.SERVER_URL)
        self.devKey = devKey or testlink_config.DEV_KEY

    def reportTCResult(self, tcid, tpid, buildid, status):
        data = {"devKey":self.devKey, "testcaseid":tcid, "testplanid":tpid, 
        "buildid":buildid, "status":status} 
        return self.server.tl.reportTCResult(data)
    
    def getProjects(self):
        return self.server.tl.getProjects(dict(devKey=self.devKey))
    
    def getInfo(self):
        return self.server.tl.about()

    def about(self):
        """
        Get information about the TestLink API version.
        """
        return self.server.tl.about()
    
    def ping(self):
        """
        Test if the XML-RPC TestLink API is working.
        Returns characters "Hello!"
        """
        return self.server.tl.ping()



    def echo(self, message):
        """
        Ask the server to return a given string
        """
        return self.server.tl.repeat({'str': message})



    def addTestCaseToTestPlan(self, projectID, planID, testCaseVisibleID, version, execOrder, urgency):
        """
        Adds a test case from a project to the test plan.
        Includes the optional parameters for Execution Order,
        and Urgency
        """
        #NOTE: Doesn't seem to need devKey?
        args = {'testprojectid' : str(projectID), 
                'planID' : str(planID),
                'testcaseexternalid' : str(testCaseVisibleID),
                'version' : str(version),
                'executionorder' : str(execOrder),
                'urgency' : str(urgency)}
        return self.server.tl.addTestCaseToTestPlan(args)



    def createBuild(self, planID, buildName, buildNotes):
        """
        Create a new build under the provided test plan identifier.
        """
        args = {'devKey' : self.devKey,
                'testplanid' : str(planID),
                'buildname' : buildName,
                'buildnotes' : buildNotes}
        return self.server.tl.createBuild(args)

    def createTestCase(self, authorLoginName, projectID, suiteID, caseName, summary, steps, order, checkDuplicatedName, actionOnDuplicatedName, executionType, importance):
        """
        Create a new test case using all the variables that are provided by the TestLink API.
        Returns a dict of result info.
        """
        args = {'devKey' : self.devKey,
                'testcasename' : caseName,
                'testsuiteid' : str(suiteID),
                'testprojectid' : str(projectID),
                'authorlogin' : authorLoginName,
                'summary' : summary,
                'steps' : steps,
                'importance' : importance,
                'execution' : executionType,
                'order' : order,
                'checkduplicatedname' : checkDuplicatedName,
                'actiononduplicatedname' : actionOnDuplicatedName}
        return self.server.tl.createTestCase(args)


    def createTestProject(self, projectName, testCasePrefix, description):
        """
        Create a new project in TestLink database.
        """
        args = {'devKey' : self.devKey,
                'testprojectname' : projectName,
                'testcaseprefix' : testCasePrefix,
                'notes' : description}
                #'options' : {'automationEnabled' : '1'}        }
        return self.server.tl.createTestProject(args)


    def createTestSuite(self, projectID, suiteName, description):
        """
        Create top level test suite under a specific project identifier
        """

    def createTestSuite2(self, projectID, suiteName, description, parentID, order, check):
        """
        Create a test suite at any level using the project 
        identifier and the parent suite identifier information.
        """

    def getBuildsForTestPlan(self, planID):
        """
        Get a list of builds for a test plan id
        """

    def getCasesForTestPlan(self, testPlanID):
        """
        Get all the test cases associated with a test plan identifier.
        """



    def getCasesForTestSuite(self, testProjectID, testSuiteID):
        """
        Get all the test cases for a project identifier and test suite identifier.
        """



    def getFirstLevelTestSuitesForTestProject(self, projectID=None, projectName=None ):
        """
        Get all the first level project test suites by project id
        """


    def getLastExecutionResult(self, testPlanID, testCaseID):
        """
        Get the last execution result by plan identifier and test case internal identifier.
        """



    def getLastExecutionResult2(self, projectName, testPlanName, testCaseNameOrVisibleID):
        """
        Get the last execution result by project, plan and test case name/visible id.
        """



    def getLatestBuildForTestPlan(self, planID):
        """
        Get a latest build for a test plan id
        """



    def getLatestBuildForTestPlan2(self, projectName, planName):
        """
        Get the latest build by project and plan name.
        """

    def getProjectIDByName(self, projectName):
        """
        Return the ID for a project, given the project's name.
        -1 if no such project.
        """
        result = -1
        projects = self.server.tl.getProjects({'devKey' : self.devKey})
        for project in projects:
                if (project['name'] == projectName): 
                    result = project['id']
        return result

    def getProjectTestPlans(self, projectID):
        """
        Get the test plans for a project identifier.
        """
        return self.server.tl.getProjectTestPlans({'devKey':self.devKey, 'testprojectid':str(projectID)})



    def getTestCaseIDByName(self, testCaseName):
        """
        Get a test case id by name
        """



    def getTestCaseIDByName2(self, testCaseName, testProjectName, testSuiteName):
        """
        Get test case by name.
        """



    def getTestSuitesForTestPlan(self, testPlanID):
        """
        Get test suites for test test plan by plan identifier.
        """



    def getTestSuitesForTestPlan2(self, projectName, planName):
        """
        Get test suites for a test plan by project and plan name.
        """



    def reportTestCaseResult(self, testPlanID, testCaseID, buildID, bugID, guess, execNotes, testResultStatus):
        """
        This method supports the TestLink API set of parameters that can be 
        used to report a test case result.
        """



    def reportTestCaseResult2(self, testPlanID, testCaseID, buildID, execNotes, testResultStatus):
        """
        Report a test execution result for a test case by test plan identifier 
        and test case identifier for a specific build identifier.
        """



    def reportTestCaseResult3(self, projectName, testPlanName, testCaseNameOrVisibleID, buildName, execNotes, testResultStatus):
        """
        Report a test execution result for a test case by test project name and test plan name for a specific build.
        """


def test():
    # substitute your Dev Key Here
    client = TestlinkAPIClient("1da8171e4663c80844870ecf9e36f4de")
    # get info about the server
    print client.getInfo()
    # Substitute for tcid and tpid that apply to your project
    result = client.reportTCResult(41112, 42294, 245, "f")
    # Typically you'd want to validate the result here and probably do something more useful with it
    print "reportTCResult result was: %s" %(result)
