'''
Created on 2023-03-03

@author: wf
'''
from smwsync.synccmd import SyncCmd
from tests.basemwtest import BaseMediawikiTest
import json
import os

class TestSyncCmd(BaseMediawikiTest):
    """
    test the synchronization command line
    """
    
    def setUp(self, debug=False, profile=True):
        """
        setUp
        """
        BaseMediawikiTest.setUp(self, debug=debug, profile=profile)
        for wikiId in ["ceur-ws"]:
            self.getSMWAccess(wikiId, save=True)
    
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
