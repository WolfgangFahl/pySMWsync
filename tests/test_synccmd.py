'''
Created on 2023-03-03

@author: wf
'''
from smwsync.synccmd import SyncCmd
from tests.basetest import Basetest
import json
import os
class TestSyncCmd(Basetest):
    """
    test the synchronization command line
    """
    
    def testProps(self):
        """
        test property query
        """
        debug=self.debug
        debug=True
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        props=syncCmd.getProperties("Scholar")
        if debug:
            print(json.dumps(props,indent=2,default=str))
            
    def testUpdate(self):
        """
        test updating the cache
        """
        debug=True
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        json_path=syncCmd.update("Scholar","/tmp/wikisync")
        self.assertTrue(os.path.exists(json_path))
