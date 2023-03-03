'''
Created on 2023-03-03

@author: wf
'''
import json
import os
import sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import traceback
from smwsync.version import Version
from smwsync.mapping import Mapping
import webbrowser
from meta.mw import SMWAccess
from meta.metamodel import Context, Topic
from pathlib import Path
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from lodstorage.sparql import SPARQL
from lodstorage.query import EndpointManager

class SyncCmd:
    """
    Command line for synching
    """
    
    def __init__(self,wikiId:str="ceur-ws",context_name:str="CrSchema",endpoint_name:str="wikidata",debug:bool=False):
        """
        Constructor
        
        Args:
            wikiId(str): my wiki Id
            topic(str): the topic to sync
            context_name(str): the name of the context
            debug(bool): if True switch debugging on
        """
        colorama_init()
        self.wikiId=wikiId
        self.debug=debug
        self.smwAccess=SMWAccess(wikiId)
        self.context_name=context_name
        self.mw_contexts=self.smwAccess.getMwContexts()
        if not context_name in self.mw_contexts:
            raise (f"context {context_name} not available in SMW wiki {wikiId}")
        self.mw_context=self.mw_contexts[context_name]
        self.context,self.error,self.errMsg=Context.fromWikiContext(self.mw_context, debug=self.debug)
        self.endpoints = EndpointManager.getEndpoints(lang="sparql")
        self.endpointConf = self.endpoints.get(endpoint_name)
        self.sparql = SPARQL(self.endpointConf.endpoint)
        
    @classmethod
    def fromArgs(self,args)->'SyncCmd':
        """
        create a sync command for the given command line arguments
        
        Args:
            args(Object): command line arguments
        """
        syncCmd=SyncCmd(wikiId=args.target,context_name=args.context,endpoint_name=args.endpoint,debug=args.debug)
        return syncCmd
    
    @classmethod
    def getArgParser(cls)->ArgumentParser:
        """
        Setup command line argument parser
                   
        Returns:
            ArgumentParser: the argument parser
        """
        parser = ArgumentParser(description=Version.full_description, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-a","--about",help="show about info [default: %(default)s]",action="store_true")
        parser.add_argument('--context', default="CrSchema",help='context to generate from [default: %(default)s]')
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info [default: %(default)s]")
        parser.add_argument("-e","--endpoint",default="wikidata",help="the SPARQL endpoint to be used [default: %(default)s]")
        parser.add_argument("-pk","--primaryKey",help="primary Key [default: %(default)s]",default="qid")
        parser.add_argument("-pkv","--primaryKeyValues",help="primary Key Values",nargs='+')
        parser.add_argument("-t", "--target", default="ceur-ws", help="wikiId of the target wiki [default: %(default)s]")
        parser.add_argument("-u", "--update",action="store_true",help="update the local cache")
        parser.add_argument("--topic",help="the topic to work with [default: %(default)s]",default="Scholar")
        parser.add_argument("--proplist",action="store_true",help="show the properties")
        parser.add_argument("-V", "--version", action='version', version=Version.version_msg)
        parser.add_argument("-p","--props",help="properties to sync")
        parser.add_argument("-pm","--propertyMap",help="the yaml property map")
        return parser
    
    def getTopic(self,topic_name:str):
        """
        get the topic for the given topic name
        
        Args:
            topic_name(str): the name of the topic to get the properties for
        """
        if not topic_name in self.context.topics:
            raise Exception(f"topic {topic_name} is not in context {self.context.name} in wiki {self.wikiId}")
        topic=self.context.topics[topic_name]
        return topic
    
    def getCacheRoot(self,cache_root:str=None)->str:
        """
        get the cache_root for the the given cache_root
        
        Args:
            cache_root(str): root of the cache_path - if None set to $HOME/.smwsync
        Returns:
            str: the cache root
        """
        if cache_root is None:
            home = str(Path.home())
            cache_root = f"{home}/.smwsync"
        return cache_root    
    
    def getCachePath(self,cache_root:str=None)->str:
        """
        get the cache_path for the the given cache_root
        
        Args:
            cache_root(str): root of the cache_path - if None set to $HOME/.smwsync
        Returns:
            str: the cache path for my wikiId and context's name
        """
        cache_root=self.getCacheRoot(cache_root)
        cache_path=f"{cache_root}/{self.wikiId}/{self.context.name}"
        os.makedirs(cache_path,exist_ok=True)
        return cache_path
    
    def getMapping(self,cache_root:str=None)->Mapping:
        """
        get the mapping for the given cache_root
        
        Args:
            cache_root(str): root of the cache_path - if None set to $HOME/.smwsync
        """
        mapping=Mapping()
        cache_root=self.getCacheRoot(cache_root)
        yaml_path=f"{cache_root}/{self.context.name}_wikidata_map.yaml"
        mapping.fromYaml(yaml_path)
        return mapping
    
    def color_msg(self,color,msg):
        print(f"{color}{msg}{Style.RESET_ALL}")
    
    def updateItemCache(self,topic_name:str,cache_path:str=None)->str:
        """
        update the item cache
        
        for the given topic name and cache_path
        
        Args:
            topic_name(str): the name of the topic
            cache_path(str): the path to the cache - if None .smwsync in the home directory is used
            
        Returns:
            str: the path to the json file where the data is cached
        
        """
        topic=self.getTopic(topic_name)
        ask_query=topic.askQuery()
        items=self.smwAccess.smw.query(ask_query)
        cache_path=self.getCachePath(cache_path)
        json_path=(f"{cache_path}/{topic_name}.json")
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(items,json_file,ensure_ascii=False, indent=2)
        return json_path,items
    
    def readItemsFromCache(self,topic_name,cache_path:str=None):
        """
        read the items back from cache
        """
        cache_path=self.getCachePath(cache_path)
        json_path=(f"{cache_path}/{topic_name}.json")
        with open(json_path, 'r') as json_file:
            items = json.load(json_file)
        return items
    
    def showProperties(self,topic:Topic):
        """
        show the properties for the given Topic
        
        Args:
            topic(Topic): the topic to show the properties for
        """
        if not topic.name in self.mapping.map_by_topic:
            raise Exception(f"missing wikidata mapping for {topic.name} - you might want to add it to the yaml file for {self.context.name}")
        tm=self.mapping.map_by_topic[topic.name]
        for prop_name,prop in topic.properties.items():
            if prop_name in tm.prop_by_smw_prop:
                pm=tm.prop_by_smw_prop[prop_name]
                info=f"{pm.arg}: {pm.pid_label} ({pm.pid}) → {prop.name}"
                print(f"{info}")
            #else:
            # info=f"{prop_name}:{prop} ❌ - missing wikidata map entry"
            pass
        
    def getValue(self,pk:str,pkValue:str,pid:str):
        """
        get the value for the given primary key and the given property id
        """
        value=None
        if pk=="qid":
            sparql_query=f"""SELECT ?object WHERE {{
  wd:{pkValue} wdt:{pid} ?object .
}}"""
        records=self.sparql.queryAsListOfDicts(sparql_query)
        if len(records)==1:
            record=records[0]
            value=record["object"]
        return value
    
    def sync(self,pkValues:list,prop_arglist):
        """
        synchronize the given properties 
        """
        for arg in prop_arglist:
            
            pass
                      
    
    def main(self,args):
        """
        command line handling
        """
        if args.about:
            print(Version.description)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
        self.mapping=self.getMapping()
        if args.proplist:
            topic=self.getTopic(topic_name=args.topic)
            self.showProperties(topic=topic)
        if args.update:
            self.color_msg(Fore.BLUE,f"updating cache for {self.context.name}:{args.topic} from wiki {self.wikiId} ...")
            json_path,items=self.updateItemCache(args.topic)
            self.color_msg(Fore.BLUE,f"stored {len(items)} {args.topic} items to {json_path}")
        if args.props:
            self.sync(args.primaryKeyValues,args.props)

def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv=sys.argv[1:]
        
    try:
        parser=SyncCmd.getArgParser()
        args = parser.parse_args(argv)
        if len(argv) < 1:
            parser.print_usage()
            sys.exit(1)
        syncCmd=SyncCmd.fromArgs(args)
        syncCmd.main(args)
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(Version.name) * " "
        sys.stderr.write(Version.name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args.debug:
            print(traceback.format_exc())
        return 2       
        
DEBUG = 1
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
