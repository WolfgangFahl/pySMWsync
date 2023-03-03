'''
Created on 2023-03-03

@author: wf
'''
from smwsync.synccmd import SyncCmd
from tests.basemwtest import BaseMediawikiTest
import json
import os
from pathlib import Path

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
        json_path,items=syncCmd.update("Scholar","/tmp/wikisync")
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(len(items)>20)
        
    def testMapping(self):
        """
        test the mapping
        """
        debug=self.debug
        debug=True
        example_path=str(Path(__file__).parent.parent)+"/examples"
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        mapping=syncCmd.getMapping(example_path)
        if debug:
            print(json.dumps(mapping.map_list,indent=2,default=str))
        self.assertEqual(2,len(mapping.map_list))
        self.assertEqual(2,len(mapping.map_by_topic))