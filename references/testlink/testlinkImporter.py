import sys
import getopt
import testlink_config
from testlink import TestlinkAPIClient
def main(*argv):
    if(argv):
        client = TestlinkAPIClient()
        projects = client.getProjects()
        opts, args =  getopt.getopt(argv, None, ["project"])
        p = [x for x in projects if x['name'].lower()==args[0].lower()]
        print dir(p)
        pass
def createEmptyTC(tcName, tcDescription):
    template = """
        
    """
    return template.replace("{{name}}", tcName).replace("{{description}}", tcDescription)
    
if __name__=='__main__':
    main('LifeWatch Connect')
    #main(*sys.argv[1:])