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
        self.example_path=str(Path(__file__).parent.parent)+"/examples"
         
    
    def testProps(self):
        """
        test property query
        """
        debug=self.debug
        debug=True
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        topic=syncCmd.getTopic("Scholar")
        if debug:
            print(json.dumps(topic.properties,indent=2,default=str))
            
    def testUpdateItemCache(self):
        """
        test updating the cache
        """
        debug=False
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        cache_path="/tmp/wikisync"
        json_path,items=syncCmd.updateItemCache("Scholar",cache_path)
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(len(items)>20)
        cached_items=syncCmd.readItemsFromCache("Scholar", cache_path)
        if debug:
            print(json.dumps(cached_items,indent=2,default=str))
        self.assertEqual(items,cached_items)
        
    def testMapping(self):
        """
        test the mapping
        """
        debug=self.debug
        #debug=True
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        mapping=syncCmd.getMapping(self.example_path)
        if debug:
            print(json.dumps(mapping.map_list,indent=2,default=str))
        self.assertEqual(2,len(mapping.map_list))
        self.assertEqual(2,len(mapping.map_by_topic))
        
    def testQuery(self):
        """
        test querying
        """
        debug=self.debug
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        value=syncCmd.getValue("qid","Q110633994","P6634")
        if debug:
            print(value)
        self.assertEqual("haydar-akyuerek",value)
        
    def testQueryByArg(self):
        """
        query by arguments
        """
        debug=True
        syncCmd=SyncCmd("ceur-ws",debug=debug)
        testParams=[("Scholar","Q54303353"),("EventSeries","Q105491257"),("Event","Q48027931")]
        for testParam in testParams:
            with self.subTest(testParam=testParam):
                topic_name,qid=testParam
                mapping=syncCmd.getMapping(self.example_path)
                tm=mapping.map_by_topic[topic_name]
                label=syncCmd.getValue("qid",qid,"label")
                for arg,pm in tm.prop_by_arg.items():
                    value=syncCmd.getValue("qid",qid,pm.pid)
                    if debug:
                        print(f"{label}({qid}):{pm.smw_prop}({arg})={value}")