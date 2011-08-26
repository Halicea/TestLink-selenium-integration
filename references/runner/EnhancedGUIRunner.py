#!/usr/bin/env python
"""
Copyright (c) 2011 Costa Halicea Mihajlov
An enhaced GUI runner with tight integration with testlink via testlinkrpc API, derived from 
Jonella Michaylov's enhanced GUI test runner.
Copyright (c) 2011 Costa Halicea Mihajlov
This module is free software, and you may redistribute it and/or modify
it under the same terms as Python itself, so long as these copyright messages
and disclaimers are retained in their original form.
============ Original Copyright Notice and Disclaimer below =================
An enhanced GUI test runner for the PyUnit unit testing framework, derived from
Steve Purcell's original GUI framework and application shipped with PyUnit.

For further information, see http://www.path-not-tested.com

Copyright (c) 2010 Jonella Michaylov
This module is free software, and you may redistribute it and/or modify
it under the same terms as Python itself, so long as these copyright messages
and disclaimers are retained in their original form.

============ Original Copyright Notice and Disclaimer below =================

GUI framework and application for use with Python unit testing framework.
Execute tests written using the framework provided by the 'unittest' module.

Further information is available in the bundled documentation, and from

  http://pyunit.sourceforge.net/

Copyright (c) 1999, 2000, 2001 Steve Purcell
This module is free software, and you may redistribute it and/or modify
it under the same terms as Python itself, so long as this copyright message
and disclaimer are retained in their original form.

IN NO EVENT SHALL THE AUTHOR BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,
SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF
THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.

THE AUTHOR SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS,
AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
"""

__author__ = "Costa Halicea Michaylov (costa@halicea.com)"
__version__ = "$Revision: 1.0 $"

import unittest
import sys
import os
import Tkinter
import tkMessageBox
import traceback
import threading
import Queue
import time
import runner
import string
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configuration')))
import runner_config
tk = Tkinter # Alternative to the messy 'from Tkinter import *' often seen


##############################################################################
# GUI framework classes
##############################################################################


class GUITestResult(unittest.TestResult):
    """A TestResult that makes callbacks to its associated GUI TestRunner.
    Used by EnhancedGUIRunner. Need not be created directly.
    """
    def __init__(self, callback):
        unittest.TestResult.__init__(self)
        self.callback = callback

    def addError(self, test, err):
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


class RollbackImporter:
    """This tricky little class is used to make sure that modules under test
    will be reloaded the next time they are imported.
    """
    def __init__(self):
        self.previousModules = sys.modules.copy()
        
    def rollbackImports(self):
        for modname in sys.modules.keys():
            if not self.previousModules.has_key(modname):
                # Force reload when modname next imported
                del(sys.modules[modname])


##############################################################################
# Tkinter GUI
##############################################################################

_ABOUT_TEXT="""\
An enhanced automation GUI test runner for the PyUnit unit testing framework based on testlink testplans.
(Integration with testlink enabled).
Copyright (c) 2011 Costa Halicea Mihaylov
<costa@halicea.com>
based on the enhaced test gui runner from Jonella Michaylov: 
Copyright (c) 2010 Jonella Michaylov
<admin@path-not-tested.com>
based on the original GUI Test Runner from PyUnit:
Copyright (c) 2000 Steve Purcell
<stephen_purcell@yahoo.com>
"""
_HELP_TEXT="""\
Enter the path of the  exported testplan from testlink.
Click 'start', and the test thus produced will be run.
Check the Update testlink checkbox if you like the results to be updated.

Double click on an error in the listbox to see more information about it,\
including the stack trace. Unlike the original GUI test runner in PyUnit, \
the listbox is populated before the tests run, and the test-by-test progress \
and results are indicated in real time. 

Notes: Configuration files are located in the configuration directory.
    -runner_config.py 
    -selenium_config.py #for setting the selenium server paths e.t.c
    -testlink_config.py #for seting the testlink server paths e.t.c
"""

class TestStartedMessage():
    
    def __init__(self, test):
        self.test = test
        pass
    
    def __call__(self, receiver):
        receiver.executeTestStarted(self.test)
        pass
    
class TestFailedMessage():
    
    def __init__(self, test, err):
        self.test = test
        self.err = err
        pass
    
    def __call__(self, receiver):
        receiver.executeTestFailed(self.test, self.err)
        pass

class TestErroredMessage():
    
    def __init__(self, test, err):
        self.test = test
        self.err = err
        pass
    
    def __call__(self, receiver):
        receiver.executeTestErrored(self.test, self.err)
        pass

class TestFinishedMessage():
    
    def __init__(self, test):
        self.test = test
        pass
    
    def __call__(self, receiver):
        receiver.executeTestFinished(self.test)
        pass

class StoppedMessage():
    
    def __init__(self):
        pass
    
    def __call__(self, receiver):
        receiver.executeStopped()
        pass

class EnhancedGUIRunner():
    """A test runner GUI using Tkinter.
    """
    
    def __init__(self, *args, **kwargs):
        self.currentResult = None
        self.running = 0
        self.rollbackImporter = None
        self.runner = None
        apply(self.initGUI, args, kwargs)
        
    def initGUI(self, root, initialTestName):
        """Set up the GUI inside the given root window. The test name entry
        field will be pre-filled with the given initialTestName.
        """
        self.root = root
        # Set up values that will be tied to widgets
        self.suiteNameVar = tk.StringVar()
        self.suiteNameVar.set(initialTestName)
        if not initialTestName:
            self.suiteNameVar.set(os.path.abspath(runner_config.DEFAULT_PLAN))
        self.statusVar = tk.StringVar()
        self.statusVar.set("Idle")
        self.runCountVar = tk.IntVar()
        self.failCountVar = tk.IntVar()
        self.errorCountVar = tk.IntVar()
        self.remainingCountVar = tk.IntVar()
        self.stopOnErrorVar = tk.IntVar()
        self.updateTestLinkVar=tk.IntVar()
        self.autoGenerateVar = tk.IntVar()
        self.skipMissingVar = tk.IntVar()
        self.elapsedVar = tk.StringVar()
        self.elapsedVar.set("0:00")
        self.averageVar = tk.StringVar()
        self.averageVar.set("0:00")
        self.top = tk.Frame()
        self.top.pack(fill=tk.BOTH, expand=1)
        self.createWidgets()
        self.queue = Queue.Queue()
        self.currentTestIndex = 0
        

    def runClicked(self):
        "To be called in response to user choosing to run a test"
        if self.running: return
        self.running = 1 
        self.currentTestIndex = 0
        while self.errorListbox.size():
            self.errorListbox.delete(0)
        testName = self.getSelectedTestName()
        if not testName:
            self.errorDialog("Test name entry", "You must enter a test plan file path")
            return
        if self.rollbackImporter:
            self.rollbackImporter.rollbackImports()
        self.rollbackImporter = RollbackImporter()
        try:
            self.runner = runner.TestLinkBuild(
                               testName, 
                               testlinkUpdate=(self.updateTestLinkVar.get() and [True, ] or [False, ])[0], 
                               autoGenerate=(self.autoGenerateVar.get() and [True, ] or [False, ])[0],
                               skipMissing = (self.skipMissingVar.get() and [True, ] or [False, ])[0],
                               stream=None,
                               testResultClass= GUITestResult
                               )
            self.runner.testresult = GUITestResult(self)
            self.currentResult = self.runner.testresult
            self.test = self.runner.suite #unittest.defaultTestLoader.loadTestsFromName(testName)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            apply(traceback.print_exception,sys.exc_info())
            self.errorDialog("Unable to run test '%s'" % testName,
                             "Error loading specified test: %s, %s" % \
                             (exc_type, exc_value))
            return
        self.showtests(self.runner.suite)
        self.currentResult = GUITestResult(self)
        self.totalTests = self.runner.suite.countTestCases()
        self.notifyRunning()
        self.thread1 = threading.Thread(target=self.bgRunner)
        self.thread1.start()
        self.theLoop()
            
    def showtests(self, x):
        if isinstance(x, unittest.TestCase):
            print x.id()
            self.errorListbox.insert(Tkinter.END, x.id())
            #tk.Label(self.testFrame, text=x.id()).pack() 
        elif isinstance(x, unittest.TestSuite):
            for thing in x._tests:
                self.showtests(thing)  
    
    def bgRunner(self):   
        print "start thread"
        print "actually running"
        self.runner.run()
        print "done running"
        self.notifyStopped()
        pass

    def stopClicked(self):
        "To be called in response to user stopping the running of a test"
        if self.currentResult:
            self.currentResult.stop()
            print "processed a user stop"
            self.stopGoButton.config(state=tk.DISABLED)

    def theLoop(self):
        if self.running:
            soFar = time.clock() - self.runStartTime
            self.elapsedVar.set(time.strftime("%M:%S", 
                                              time.localtime(soFar)))
            while self.queue.qsize():
                try:
                    print "getting message"
                    msg = self.queue.get(0)
                    # Check contents of message and do what it says
                    # As a test, we simply print it
                    msg(self)
                    self.top.update()
                except Queue.Empty:
                    pass
            self.top.after(100, self.theLoop) 

    def createWidgets(self):
        """Creates and packs the various widgets.
        
        Why is it that GUI code always ends up looking a mess, despite all the
        best intentions to keep it tidy? Answers on a postcard, please.
        """
        # Status bar
        statusFrame = tk.Frame(self.top, relief=tk.SUNKEN, borderwidth=2)
        statusFrame.pack(anchor=tk.SW, fill=tk.X, side=tk.BOTTOM)
        tk.Label(statusFrame, textvariable=self.statusVar).pack(side=tk.LEFT)

        rightFrame = tk.Frame(self.top, borderwidth=3)
        rightFrame.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, expand=1)

        # Area to enter name of test to run
        suiteNameFrame = tk.Frame(rightFrame, borderwidth=3)
        suiteNameFrame.pack(fill=tk.X)
        tk.Label(suiteNameFrame, text="Enter the test plan file path:").pack(side=tk.LEFT)
        e = tk.Entry(suiteNameFrame, textvariable=self.suiteNameVar, width=25)
        e.pack(side=tk.LEFT, fill=tk.X, expand=1)
        e.focus_set()
        #e.bind('<Key-Return>', lambda e, self=self: self.runClicked())
        #e.bind('', lambda e, self = self:self.run)
        # stop on error checkbox
        stopOnErrorFrame = tk.Frame(rightFrame, borderwidth=0)
        stopOnErrorFrame.pack(side=tk.TOP, anchor=tk.W)
        stopOnErrorButton = tk.Checkbutton(stopOnErrorFrame, text="Stop on first error", 
                                           variable=self.stopOnErrorVar)
        stopOnErrorButton.pack(side=tk.LEFT, expand=0, anchor=tk.W)
        
        updateTestLinkFrame = tk.Frame(rightFrame, borderwidth=0)
        updateTestLinkFrame.pack(side=tk.TOP, anchor=tk.W)
        updateTestLinkButton = tk.Checkbutton(stopOnErrorFrame, text="Update TestLink", 
                                           variable=self.updateTestLinkVar)
        updateTestLinkButton.pack(side=tk.LEFT, expand=0, anchor=tk.W)

        autogenerateFrame = tk.Frame(rightFrame, borderwidth=0)
        autogenerateFrame.pack(side=tk.TOP, anchor=tk.W)
        autogenerateButton = tk.Checkbutton(stopOnErrorFrame, text="Autogenerate Tests", 
                                           variable=self.autoGenerateVar)
        autogenerateButton.pack(side=tk.LEFT, expand=0, anchor=tk.W)
        self.autoGenerateVar.set(1)
        skipMissingFrame = tk.Frame(rightFrame, borderwidth=0)
        skipMissingFrame.pack(side=tk.TOP, anchor=tk.W)
        skipMissingButton = tk.Checkbutton(stopOnErrorFrame, text="Skip Missing Tests", 
                                           variable=self.skipMissingVar)
        skipMissingButton.pack(side=tk.LEFT, expand=0, anchor=tk.W)
        self.skipMissingVar.set(1)
        
        # Progress bar
        progressFrame = tk.Frame(rightFrame, relief=tk.GROOVE, borderwidth=2)
        progressFrame.pack(fill=tk.X, expand=0, anchor=tk.NW)
        tk.Label(progressFrame, text="Progress:").pack(anchor=tk.W)
        self.progressBar = ProgressBar(progressFrame, relief=tk.SUNKEN,
                                       borderwidth=2)
        self.progressBar.pack(fill=tk.X, expand=1)

        # Area with buttons to start/stop tests and quit
        buttonFrame = tk.Frame(self.top, borderwidth=3)
        buttonFrame.pack(side=tk.LEFT, anchor=tk.NW, fill=tk.Y)
        self.stopGoButton = tk.Button(buttonFrame, text="Start",
                                      command=self.runClicked)
        self.stopGoButton.pack(fill=tk.X)
        tk.Button(buttonFrame, text="Close",
                  command=self.top.quit).pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(buttonFrame, text="About",
                  command=self.showAboutDialog).pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(buttonFrame, text="Help",
                  command=self.showHelpDialog).pack(side=tk.BOTTOM, fill=tk.X)

        # Area with labels reporting results
        countFrame = tk.Frame(progressFrame, borderwidth=2)
        countFrame.pack(fill=tk.X, expand=1)  
        for label, var in (('Run:', self.runCountVar),
                           ('Failures:', self.failCountVar),
                           ('Errors:', self.errorCountVar),
                           ('Remaining:', self.remainingCountVar)
                           ):
            tk.Label(countFrame, text=label).pack(side=tk.LEFT)
            tk.Label(countFrame, textvariable=var,
                     foreground="blue").pack(side=tk.LEFT, fill=tk.X,
                                             expand=1, anchor=tk.W)
                     
        timeFrame = tk.Frame(progressFrame, borderwidth=2)
        timeFrame.pack(fill=tk.X, expand=1)           
        for label, var in (('Elapsed time:', self.elapsedVar),
                           ('Average time:', self.averageVar)
                           ):
            tk.Label(timeFrame, text=label).pack(side=tk.LEFT)
            tk.Label(timeFrame, textvariable=var,
                     foreground="blue").pack(side=tk.LEFT, fill=tk.X,
                                             expand=1, anchor=tk.W)


        # List box showing errors and failures
        tk.Label(rightFrame, text="Detailed progress:").pack(anchor=tk.W)
        listFrame = tk.Frame(rightFrame, relief=tk.SUNKEN, borderwidth=2)
        listFrame.grid_rowconfigure(0, weight=1)
        listFrame.grid_columnconfigure(0, weight=1)

        
        self.errorListbox = tk.Listbox(listFrame, foreground='black',
                                       selectmode=tk.SINGLE,
                                       selectborderwidth=0,
                                       width='50')
        self.errorListbox.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        #self.errorListbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1,
        #                       anchor=tk.NW)
        listVScroll = tk.Scrollbar(listFrame, command=self.errorListbox.yview)
        listVScroll.grid(row=0, column=1, sticky=tk.N+tk.S)

        #listVScroll.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.N)
        listHScroll = tk.Scrollbar(listFrame, command=self.errorListbox.xview,
                                   orient=Tkinter.HORIZONTAL)
        listHScroll.grid(row=1, column=0, sticky=tk.E+tk.W)

        #listHScroll.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.N)
        self.errorListbox.bind("<Double-1>",
                               lambda e, self=self: self.showSelectedError())
        self.errorListbox.configure(yscrollcommand=listVScroll.set)
        self.errorListbox.configure(xscrollcommand=listHScroll.set)
        listFrame.pack(fill=tk.BOTH, expand=1)

    def getSelectedTestName(self):
        return self.suiteNameVar.get()

    def errorDialog(self, title, message):
        tkMessageBox.showerror(parent=self.root, title=title,
                               message=message)

    def notifyRunning(self):
        self.runStartTime = time.clock()
        self.runCountVar.set(0)
        self.failCountVar.set(0)
        self.errorCountVar.set(0)
        self.elapsedVar.set("0:00")
        self.averageVar.set("0:00")
        self.remainingCountVar.set(self.totalTests)
        self.errorInfo = []
        #while self.errorListbox.size():
        #    self.errorListbox.delete(0)
        #Stopping seems not to work, so simply disable the start button
        self.stopGoButton.config(command=self.stopClicked, text="Stop")
        #self.stopGoButton.config(state=tk.DISABLED)
        self.progressBar.setProgressFraction(0.0)
        self.top.update_idletasks()

    def notifyStopped(self):
        self.queue.put(StoppedMessage())
        pass
        
    def executeStopped(self):
        print "got a stop"
        self.stopGoButton.config(state=tk.ACTIVE)
        self.stopGoButton.config(command=self.runClicked, text="Start")
        self.statusVar.set("Idle")
        self.top.update_idletasks()
        self.running = 0
        pass

    def notifyTestStarted(self, test):
        self.queue.put(TestStartedMessage(test))
        pass
    
    def setDisplayStatus(self, position, status):
        str = self.errorListbox.get(position)
        parts = str.split(': ', 1)
        if len(parts) == 2:
            if parts[0] == 'FAILED' or parts[0] == 'ERROR':
                return
            else:
                str = parts[1]
        str = status + ': ' + str
        self.errorListbox.insert(position, str)
        self.errorListbox.delete(position + 1)
        if status == 'RUNNING':
            self.errorListbox.itemconfig(position, fg='blue')
        elif status == 'FAILED':
            self.errorListbox.itemconfig(position, fg='red')
        elif status == 'ERROR':
            self.errorListbox.itemconfig(position, fg='red')
        elif status == 'SUCCESS':
            self.errorListbox.itemconfig(position, fg='darkgreen')
        if position > 0:
            self.errorListbox.select_clear(position-1)
        self.errorListbox.select_set(position)
        self.errorListbox.see(min(position+4, self.errorListbox.size()))
        pass
    
    def executeTestStarted(self, test):
        self.statusVar.set(str(test))
        self.setDisplayStatus(self.currentTestIndex, 'RUNNING')
        self.top.update_idletasks()
        pass

    def notifyTestFailed(self, test, err):
        if self.stopOnErrorVar.get() == 1:
            self.currentResult.stop()
        if self.updateTestLinkVar.get()==1:
            self.runner.notifyTestFailed(test, err)
        self.queue.put(TestFailedMessage(test, err))
        pass
    
    def executeTestFailed(self, test, err):
        self.failCountVar.set(1 + self.failCountVar.get())
        #self.errorListbox.insert(tk.END, "Failure: %s" % test)
        self.errorInfo.append((test,err))
        self.setDisplayStatus(self.currentTestIndex, 'FAILED')
        pass

    def notifyTestErrored(self, test, err):
        if self.stopOnErrorVar.get() == 1:
            self.currentResult.stop()
        if self.updateTestLinkVar.get()==1:
            self.runner.notifyTestErrored(test, err)
        self.queue.put(TestErroredMessage(test, err))
        pass
    
    def executeTestErrored(self, test, err):
        self.errorCountVar.set(1 + self.errorCountVar.get())
        #self.errorListbox.insert(tk.END, "Error: %s" % test)
        self.errorInfo.append((test,err))
        self.setDisplayStatus(self.currentTestIndex, 'ERROR')
        pass

    def notifyTestFinished(self, test):
        self.queue.put(TestFinishedMessage(test))
        pass
    
    def executeTestFinished(self, test):
        self.remainingCountVar.set(self.remainingCountVar.get() - 1)
        self.runCountVar.set(1 + self.runCountVar.get())
        fractionDone = float(self.runCountVar.get())/float(self.totalTests)
        fillColor = (self.errorCountVar.get() > 0 or self.failCountVar.get() > 0) \
                        and "red" or "darkgreen"
        self.progressBar.setProgressFraction(fractionDone, fillColor)
        soFar = time.clock() - self.runStartTime
        self.averageVar.set(time.strftime("%M:%S", 
                                          time.localtime(soFar / self.runCountVar.get())))
        self.setDisplayStatus(self.currentTestIndex, 'SUCCESS')
        if self.currentTestIndex >= len(self.errorInfo):
            # no error, so pad the error list for this test
            self.errorInfo.append((test,None))
        self.currentTestIndex = self.currentTestIndex + 1
        pass

    def showAboutDialog(self):
        tkMessageBox.showinfo(parent=self.root, title="About PyUnit Enhanced Runner",
                              message=_ABOUT_TEXT)

    def showHelpDialog(self):
        tkMessageBox.showinfo(parent=self.root, title="PyUnit Enhanced Runner help",
                              message=_HELP_TEXT)

    def showSelectedError(self):
        selection = self.errorListbox.curselection()
        if not selection: return
        selected = int(selection[0])
        txt = self.errorListbox.get(selected)
        window = tk.Toplevel(self.root)
        window.title(txt)
        window.protocol('WM_DELETE_WINDOW', window.quit)
        if selected < len(self.errorInfo):
            test, error = self.errorInfo[selected]
            tk.Label(window, text=str(test),
                             foreground=(error is None) and "darkgreen" or "red", 
                             justify=tk.LEFT).pack(anchor=tk.W)
            if error is None:
                tk.Label(window, text='Test succeeded!', justify=tk.LEFT).pack()
            else:
                tracebackLines = apply(traceback.format_exception, error + (10,))
                tracebackText = string.join(tracebackLines,'')
                tk.Label(window, text=tracebackText, justify=tk.LEFT).pack()
        else:
            tk.Label(window, text='Test has not been executed!', justify=tk.LEFT).pack()
        tk.Button(window, text="Close",
                  command=window.quit).pack(side=tk.BOTTOM)
        window.bind('<Key-Return>', lambda e, w=window: w.quit())
        window.mainloop()
        window.destroy()


class ProgressBar(tk.Frame):
    """A simple progress bar that shows a percentage progress in
    the given colour."""

    def __init__(self, *args, **kwargs):
        apply(tk.Frame.__init__, (self,) + args, kwargs)
        self.canvas = tk.Canvas(self, height='20', width='60',
                                background='white', borderwidth=3)
        self.canvas.pack(fill=tk.X, expand=1)
        self.rect = self.text = None
        self.canvas.bind('<Configure>', self.paint)
        self.setProgressFraction(0.0)

    def setProgressFraction(self, fraction, color='blue'):
        self.fraction = fraction
        self.color = color
        self.paint()
        self.canvas.update_idletasks()
        
    def paint(self, *args):
        totalWidth = self.canvas.winfo_width()
        width = int(self.fraction * float(totalWidth))
        height = self.canvas.winfo_height()
        if self.rect is not None: self.canvas.delete(self.rect)
        if self.text is not None: self.canvas.delete(self.text)
        self.rect = self.canvas.create_rectangle(0, 0, width, height,
                                                 fill=self.color)
        percentString = "%3.0f%%" % (100.0 * self.fraction)
        self.text = self.canvas.create_text(totalWidth/2, height/2,
                                            anchor=tk.CENTER,
                                            text=percentString)

def main(initialTestName=""):
    root = tk.Tk()
    root.title("PyUnit TestLink TestPlan Runner")
    runner = EnhancedGUIRunner(root, initialTestName)
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main()
