
"""
Copyright 2011 Costa Halicea Mihajlov.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import getopt
import os
from os.path import dirname
import sys
import unittest
sys.path.append(os.path.join(dirname(dirname(dirname(__file__))), 'tests'))
sys.path.append(os.path.join(dirname(dirname(dirname(__file__))), 'references'))
sys.path.append(os.path.join(dirname(dirname(dirname(__file__))), 'configuration'))
import xml.dom.minidom as md
import runner_config
from testlink import TestlinkAPIClient
class TestLinkTestResult(unittest.TestResult):
    """A TestResult that makes callbacks to its associated GUI TestRunner.
    Used by EnhancedGUIRunner. Need not be created directly.
    """
    def __init__(self, callback, active=False):
        self.active = active
        unittest.TestResult.__init__(self)
        self.callback = callback

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        self.callback.notifyTestErrored(test, err)
    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        self.callback.notifyTestPassed(test)
    def addFailiure(self, test, err):
        unittest.TestResult.addError(self, test, err)
        self.callback.notifyTestErrored(test, err)
    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        self.callback.notifyTestFailed(test, err)
    def stopTest(self, test):
        unittest.TestResult.stopTest(self, test)
        self.callback.notifyTestFinished(test)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        self.callback.notifyTestStarted(test)

class TestLinkBuild(object):
    statuses = {'b':'ERROR', 'f':'FAIL', 'p':'PASS'}
    def __init__(self, xml=None, testlinkUpdate=False, autoGenerate=False, skipMissing=False, stream = None, testResultClass = TestLinkTestResult,):
        self.testcases = []
        if not xml:
            self.xml = open(runner_config.DEFAULT_PLAN, 'r').read()
        else:
            self.xml = open(xml, 'r').read()
            
        self.tlupdate = testlinkUpdate
        self.stream = stream
        self.dom = md.parseString(self.xml)
        self.autoGen = autoGenerate
        self.client = TestlinkAPIClient()
        self.loadTestParams()
        self.loadTCs()
        if self.autoGen: self.createTCs()
        if skipMissing: self.removeMissingTCs()
        self.suite = unittest.TestLoader().loadTestsFromNames([x['fullname'] for x in self.testcases])
        self.tcdict = dict([(x['fullname'], x) for x in self.testcases])
        self.testresult = testResultClass(self)
    def loadTestParams(self):
        #plan id
        try:
            self.planid=int(self.dom.childNodes[0].attributes['id'].value)
        except Exception, ex:
            raise Exception("Id of the plan was not found in the XML. \r\n You need to add it by hand as an attribute\r\nExample:<testplan id=\"12345\">")
        #buildid
        buildidtag = self.dom.getElementsByTagName('build')[0].getElementsByTagName('internal_id')[0]
        for n in buildidtag.childNodes:
            try:
                self.buildid = int(n.nodeValue)
                break
            except:
                pass
        print "BuildID", self.buildid
    def loadTCs(self):
        tcs = self.dom.getElementsByTagName('testcase')
        for tc in tcs:
            stepsTag= tc.getElementsByTagName('step')
            keywordsTag= tc.getElementsByTagName('keyword')
            name = runner_config.name_correction(tc.attributes['name'].value)
            fullname = name
            print tc.attributes
            id = int(tc.attributes['internalid'].value)
            steps = []
            keywords = []
            repl = lambda k:   k.replace('<![CDATA[<p>','')\
                                .replace('<expectedresults>','')\
                                .replace('</expectedresults>','')\
                                .replace('</p>]]>','')\
                                .replace('<actions>','')\
                                .replace('</actions>','')\
                                .replace('\n', '')\
                                .replace('\t', '')\
                                .strip()
            for s in stepsTag:
                steps.append({'step': repl(s.getElementsByTagName('actions')[0].toxml()),
                              'result':repl(s.getElementsByTagName('expectedresults')[0].toxml())})
            for k in keywordsTag:
                keywords.append(repl(k.attributes['name'].value))
#            summary =   tc.getElementsByTagName('summary').value
#            automatic = tc.getElementsByTagName('execution_type').value
            
            summary =   ""
            automatic = "" 
            #setup the fullname
            nd=tc
            while nd.parentNode.tagName=='testsuite':
                nd = nd.parentNode
                suite = runner_config.name_correction(nd.attributes['name'].value)
                fullname = suite+'.'+fullname
            #end setup the fullname
            self.testcases.append({'name':name, 'fullname':fullname,'id':id, 'summary':summary, 'automatic':automatic, 'steps':steps, 'keywords':keywords})
    
    def removeMissingTCs(self):
        missing = []
        testsDir = os.path.join(runner_config.PROJECT_PATH, 'tests')
        for tc in self.testcases:
            tcPath = tc['fullname'].replace('.', os.path.sep)+'.py'
            if not os.path.exists(os.path.join(testsDir, tcPath)):
                missing.append(tc)
        for m in missing:
            self.testcases.remove(m)
    def createTCs(self):
        testsDir = os.path.join(runner_config.PROJECT_PATH, 'tests')
        errCnt = 0
        for tc in self.testcases:
            relPath = tc['fullname'].replace('.', os.path.sep)+'.py'
            relDir = os.path.dirname(relPath)
            if not os.path.exists(os.path.join(testsDir, relPath)):
                if not os.path.exists(os.path.join(testsDir, relDir)):
                    os.makedirs(os.path.join(testsDir, relDir))
                try:
                    f = open(os.path.join(testsDir, relPath), 'w')
                    f.write(self.createEmptyTC(tc))
                    f.close()
                except Exception, ex:
                    errCnt+=1
                    print errCnt, '-', ex
                    print os.path.join(testsDir, relPath)
            #recheck if __init__.py are created
            while relDir:
                initfile = os.path.join(testsDir, relDir, '__init__.py')
                if not os.path.exists(initfile):
                    f = open(initfile, 'w')
                    f.write("""#import os
#import sys
#from os.path import dirname
#cmd_folder = os.path.dirname(os.path.abspath(__file__))
#if cmd_folder not in sys.path:
#    sys.path.insert(0, cmd_folder)""")
                    f.close()
                relDir = os.path.dirname(relDir)
    def createEmptyTC(self,tc):
        template = """from selenium import selenium, SeleniumTestCase
class {{name}}(SeleniumTestCase):
    '''
{{description}}
    '''
    def test(self):
        self.fail("TC is not implemented")
"""
        description = ''
        if tc['keywords']:
            description += '\n'.join(tc['keywords'])
        if tc['steps']:
            description += '\n'.join(['\t\t'+x['step']+'\n\t\t\t-'+x['result'] for x in tc['steps']])
        return template.replace("{{name}}", tc['name']).replace("{{description}}", description and description or 'Add description here')            
    def run(self):
        self.testresult = self.suite.run(self.testresult)
        #print res
    def sendStatus(self, test, status, message=None):
        tc = None
        if self.tcdict.has_key(test.__class__.__module__+'.'+test.__class__.__name__):
            tc = self.tcdict[test.__class__.__module__+'.'+test.__class__.__name__]
        elif self.tcdict.has_key(test.__class__.__module__):
            tc = self.tcdict[test.__class__.__module__]
        if tc:
            if self.tlupdate:
                if (status=='p' and not tc['result']) or status in ['b', 'f']:
                    self.client.reportTCResult(tc['id'], self.planid, self.buildid, status)
            if self.stream:
                self.stream.write(self.statuses[status])
                if message:self.stream.write('\n'+message)
        else:
            if self.stream:
                self.stream.write("cannot find this testcase in the dictionary")
    def notifyTestErrored(self, test, err):
        self.sendStatus(test, 'b', str(err))
    def notifyTestFailed(self, test, err):
        self.sendStatus(test, 'f', str(err))
    def notifyTestPassed(self, test):
        self.sendStatus(test, 'p')
    def notifyTestFinished(self, test):
        if self.stream:
            self.stream.write('\n')
    def notifyTestStarted(self, test):
        if self.stream:
            self.stream.write(str(test)+':')

def main(*argv):
    xml=None
    if(argv):
        opts, args =  getopt.getopt(argv, None, ["planbased", "tcbased", "testlink", "autogenerate", "skip_missing"])
        xml = args[0]
    testlinkUpdate = False
    autogenerate = False
    skip_missing = False
    if '--testlink' in [x[0] for x in opts ]:
        testlinkUpdate = True
    if '--autogenerate' in [x[0] for x in opts ]:
        autogenerate = True
    if '--skip_missing' in [x[0] for x in opts ]:
        skip_missing = True
    bld = TestLinkBuild(xml, testlinkUpdate=testlinkUpdate, autoGenerate=autogenerate, stream=sys.stderr, skipMissing=skip_missing)
    bld.run()
    bld.stream.close()
if __name__=='__main__':
    main("--testlink", "--autogenerate", "--skip_missing", runner_config.DEFAULT_PLAN)
    #main(*sys.argv[1:])