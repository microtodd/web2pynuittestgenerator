import getopt
import sys
import os

### printHelp
def printHelp():
    print "buildUnitTests.py"
    print "  -h            Help"
    print "  -a <appname>  Name of web2py app (assumes http://localhost/<appname>)"
    print "  -u <username> Username to authenticate to"
    print "  -p <password> Password to authenticate with"
    print "  -c <dir>      Directory where controllers are"
    print "  -w <dir>      Directory where web2py installed"
    print "  -o <dir>      Directory where output goes"
    print "  -v            Be verbose"

### A controller ADT
class Controller(object):

    # Constructor
    def __init__(self,fileName=None,dirName=None):
        self._fileName = fileName
        self._dirName = dirName
        self._entryPoints = []

    @property
    def entryPoints(self):
        return self._entryPoints

    @property
    def fileName(self):
        return self._fileName

    def newEntryPoint(self, value):
        self._entryPoints.append(value)

    def gatherEntryPoints(self,controllerFile=None):
        if controllerFile is None:
            controllerFile = self._fileName
        with open(self._dirName+"/"+controllerFile) as file1:
            lines = file1.readlines()
            for line in lines:
                if line.find("def ") != -1:

                    # Some special cases to skip
                    if line.find("#") != -1 or line.find("call(") != -1 or line.find("def _") != -1:
                        continue

                    methodName = line.lstrip()
                    methodName = methodName[4:]
                    methodName = methodName.split('(',1)[0]
                    if methodName == 'GET' or methodName == 'POST':
                        continue
                    self.newEntryPoint(methodName)

    def getUnitTestContent(self,appName="myapp",username="username",password="password",web2py="../web2py"):
        returnString = '''
import sys 
sys.path.append(\'WEB2PYDIR\')
from gluon.contrib.webclient import WebClient
from gluon.storage import Storage

import unittest


class TestDefaultController(unittest.TestCase):

    @classmethod
    def setUpClass(TestDefaultController):
        TestDefaultController.client = WebClient(\'http://127.0.0.1:8000/MYAPP/\')
        TestDefaultController.client.get(\'default/user/login\')
        TestDefaultController.data = dict(email=\'USERNAME\',
                    password=\'PASSWORD\',
                    _formname = \'login\')
        TestDefaultController.client.post(\'default/user/login\',data = TestDefaultController.data)    

    @classmethod
    def tearDownClass(TestDefaultController):
        TestDefaultController.client.post(\'default/user/logout\')

'''
        returnString = returnString.replace("MYAPP",appName)
        returnString = returnString.replace("USERNAME",username)
        returnString = returnString.replace("PASSWORD",password)
        returnString = returnString.replace("WEB2PYDIR",web2py)

        # Iterate the entry points and create the test stub
        for entryPoint in self.entryPoints:
            methodName = self.fileName
            methodName = methodName.replace(".py","")
            returnString = returnString + "    def test" + entryPoint + "(self):\n"
            returnString = returnString + "        self.client.get('" + methodName + '/' + entryPoint + "')\n"
            returnString = returnString + "        self.assertIn('xxx', self.client.text)\n\n"

        returnString = returnString + '''
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDefaultController)
    unittest.TextTestRunner(verbosity=2).run(suite)

'''

        return returnString
    
### Main class
class UnitTestBuilder(object):

    # Constructor
    def __init__(self):
        self._appName = "myapp"
        self._username = "username"
        self._password = "password"
        self._controllerDir = "./"
        self._web2pyDir = "./"
        self._outDir = "./"
        self._files = []

    @property
    def appName(self):
        return self._appName
    @appName.setter
    def appName(self, value):
        self._appName = value

    @property
    def username(self):
        return self._username
    @username.setter
    def username(self, value):
        self._username = value

    @property
    def password(self):
        return self._password
    @password.setter
    def password(self, value):
        self._password = value

    @property
    def controllerDir(self):
        return self._controllerDir
    @controllerDir.setter
    def controllerDir(self, value):
        self._controllerDir = value

    @property
    def web2pyDir(self):
        return self._web2pyDir
    @web2pyDir.setter
    def web2pyDir(self, value):
        self._web2pyDir = value

    @property
    def outDir(self):
        return self._outDir
    @outDir.setter
    def outDir(self, value):
        self._outDir = value

    @property
    def controllers(self):
        return self._files

    def addControllerFile(self,fileName):
        self._files.append(fileName)

    def gatherControllers(self,thisdir=None):
        foundFiles = []
        if thisdir:
            foundFiles = os.listdir(thisdir)
        else:
            foundFiles = os.listdir(self._controllerDir)
        
        # Clean
        for filename in foundFiles:
            if filename.endswith(".py"):
                self.addControllerFile(filename)

# main
if __name__ == '__main__':

    # Create builder
    utb = UnitTestBuilder()

    # Get command line args
    verbose = False
    opts, args = getopt.getopt(sys.argv[1:], "ha:u:p:c:w:v")
    for opt, arg in opts:

        # Help
        if opt == '-h':
            printHelp()
            sys.exit()

        # Appname
        if opt == '-a':
            utb.appName = arg

        # Username
        if opt == '-u':
            utb.username = arg

        # Password
        if opt == '-p':
            utb.password = arg

        # controller
        if opt == '-c':
            utb.controllerDir = arg

        # web2py
        if opt == '-w':
            utb.web2pyDir = arg

        # output
        if opt == '-o':
            utb.outDir = arg

        # verbose
        if opt == '-v':
            verbose = True

    # Gather a list of controllers
    controllers = []
    utb.gatherControllers()

    # Iterate the controllers and gather the entry points
    for controller in utb.controllers:
        if verbose:
            print "Analyzing " + controller
        thisC = Controller(dirName=utb.controllerDir, fileName=controller)
        thisC.gatherEntryPoints()
        if verbose:
            print "Found:" + str(thisC.entryPoints)
        controllers.append(thisC)

    # Iterate the controller ADTs and create unit test files
    for controller in controllers:
        testFileName = "test_" + controller.fileName
        if verbose:
            print "Generating test file: " + testFileName
        newFile = open(testFileName,"w")
        newFile.write(controller.getUnitTestContent(appName=utb.appName,username=utb.username,password=utb.password,web2py=utb.web2pyDir))
        newFile.close()
