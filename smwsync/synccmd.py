'''
Created on 2023-03-03

@author: wf
'''
import json
import re
import os
import sys
from tqdm import tqdm
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import traceback
from smwsync.version import Version
from smwsync.mapping import Mapping,  TopicMapping, PropMapping
import webbrowser
from meta.mw import SMWAccess
from meta.metamodel import Context, Topic
from pathlib import Path
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from lodstorage.sparql import SPARQL
from lodstorage.query import EndpointManager
from wikibot3rd.wikipush import WikiPush
from ez_wikidata.wikidata import WikidataItem

class SyncCmd:
    """
    Command line for synching
    """
    
    def __init__(self,wikiId:str="ceur-ws",context_name:str="CrSchema",
                 endpoint_name:str="wikidata",
                 verbose:bool=False,progress:bool=False,
                 dry:bool=True,debug:bool=False):
        """
        Constructor
        
        Args:
            wikiId(str): my wiki Id
            topic(str): the topic to sync
            context_name(str): the name of the context
            dry(bool): if True do not execute commands put display them
            debug(bool): if True switch debugging on
        """
        colorama_init()
        self.lang="en"
        self.wikiId=wikiId
        self.debug=debug
        self.progress=progress
        self.verbose=verbose
        self.dry=dry
        self.smwAccess=SMWAccess(wikiId)
        self.context_name=context_name
        self.mw_contexts=self.smwAccess.getMwContexts()
        if not context_name in self.mw_contexts:
            raise Exception(f"context {context_name} not available in SMW wiki {wikiId}")
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
        syncCmd=SyncCmd(wikiId=args.target,context_name=args.context,endpoint_name=args.endpoint,verbose=args.verbose,progress=args.progress,dry=args.dry,debug=args.debug)
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
        parser.add_argument("-cpm","--createPropertyMap",help="create the yaml property map")
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info [default: %(default)s]")
        parser.add_argument("--dry", action="store_true", help="dry run only - do not execute wikiedit commands but just display them")
        parser.add_argument("-e","--endpoint",default="wikidata",help="the SPARQL endpoint to be used [default: %(default)s]")
        parser.add_argument("--progress",action="store_true",help="show progress bar")
        parser.add_argument("-p","--props",help="properties to sync",nargs="+")
        parser.add_argument("--proplist",action="store_true",help="show the properties")
        parser.add_argument("-pm","--propertyMap",help="the yaml property map")
        parser.add_argument("-pk","--primaryKey",help="primary Key [default: %(default)s]",default="qid")
        parser.add_argument("-pkv","--primaryKeyValues",help="primary Key Values",nargs="+")
        parser.add_argument("-t", "--target", default="ceur-ws", help="wikiId of the target wiki [default: %(default)s]")
        parser.add_argument("-u", "--update",action="store_true",help="update the local cache")
        parser.add_argument("--topic",help="the topic to work with [default: %(default)s]",default="Scholar")
        parser.add_argument("--verbose",action="store_true",help="show verbose edit details")
        parser.add_argument("-V", "--version", action='version', version=Version.version_msg)
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
    
    def createMapping(self)->Mapping:
        """
        create a mapping for my context
        """
        mapping=Mapping()
        for topic_name,topic in self.context.topics.items():
            topic_map=TopicMapping(topic_name)
            for prop_name,_prop in topic.properties.items():
                pm=PropMapping(smw_prop=prop_name,arg=prop_name,pid="P?")
                topic_map.add_mapping(pm)
            mapping.map_by_topic[topic_map.topic_name]=topic_map
        return mapping
    
    def color_msg(self,color,msg:str):
        """
        print a colored message
        
        Args:
            color(Fore): the color to use
            msg(str): the message to print
        """
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
        ask_query=topic.askQuery(listLimit=5000)
        items=self.smwAccess.smw.query(ask_query)
        cache_path=self.getCachePath(cache_path)
        json_path=(f"{cache_path}/{topic_name}.json")
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(items,json_file,ensure_ascii=False, default=str,indent=2)
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
            if pid=="description" or pid=="label":
                value=None
                try:
                    label,description=WikidataItem.getLabelAndDescription(self.sparql, itemId=pkValue,lang=self.lang)
                    if pid=="description":
                        value=description
                    else:
                        value=label
                    pass
                except Exception as ex:
                    # make sure we only ignore "failed"
                    if not "failed" in str(ex):
                        raise ex
            else:
                sparql_query=f"""SELECT * {{ 
  wd:{pkValue} wdt:{pid} ?value . 
}}"""
                # see https://www.wikidata.org/wiki/Help:Ranking
                #sparql_query=f"""SELECT ?value {{ 
#  wd:{pkValue} p:{pid} ?st . 
#  ?st ps:P569 ?value . 
# ?st wikibase:rank wikibase:PreferredRank  
#}}"""
                
                records=self.sparql.queryAsListOfDicts(sparql_query)
                if len(records)>=1:
                    record=records[0]
                    value=record["value"]
                    if isinstance(value,str):
                        value=re.sub(r"http://www.wikidata.org/entity/(.*)",r"\1",value)
                    else:
                        value=str(value)
        return value
    
    def filterItems(self,items:list,pk_prop:str,pk_values:list)->list:
        """
        filter the given list of items by SMW records having primary key property values
        in the given pk_values list
        
        Args:
            items(list): the list of records to filter
            pk_prop(str): the primary key property
            pk_values(list): the list of primary key values
        """
        if pk_values is None:
            return items
        sync_items=[]
        for item_record in items:
            if pk_prop in item_record:
                item_pk_value=item_record[pk_prop]
                if item_pk_value in pk_values:
                    sync_items.append(item_record)
        return sync_items
    
    def sync(self,topic:Topic,pk:str,pk_values:list,prop_arglist:list):
        """
        synchronize the items for the given topic, the properties as specified by the prop_arglist
        the given primary key pk and the filter values pkValues
        
        Args:
            topic(Topic): the topic / class /entityType
            pk(str): the primary key to use
            pk_values(list): a list of primaryKeyValues to filter for
            prop_arglist(list): the argument names for properties to be handled
            
        """
        tm=self.mapping.map_by_topic[topic.name]
        items_dict=self.readItemsFromCache(topic.name)
        pk_map=tm.getPkSMWPropMap(pk)
        sync_items=self.filterItems(items=items_dict.values(),pk_prop=pk_map.smw_prop,pk_values=pk_values)
        self.color_msg(Fore.BLUE, f"{len(sync_items)} {tm.topic_name} items to sync ...")
        wikipush=WikiPush(None,self.wikiId,debug=self.debug,verbose=self.verbose)
        if self.progress:
            t=tqdm(total=len(prop_arglist)*len(sync_items))
        else:
            t=None    
        for arg in prop_arglist:
            pm=tm.getPmForArg(arg)
            for sync_item in sync_items:
                pk_value=sync_item[pk_map.smw_prop]
                wd_value=self.getValue(pk, pk_value, pm.pid)
                if wd_value is None:
                    wd_value=""
                page_title=sync_item[tm.topic_name]
                msg=f"updating {page_title} {pm.smw_prop} to {wd_value} from wikidata {pk_value}"
                if self.verbose:
                    self.color_msg(Fore.BLUE,msg)
                cmd=f"""wikiedit -t {self.wikiId} -p "{page_title}" --template {tm.topic_name} --property {pm.smw_prop} --value "{wd_value}" -f"""
                if self.dry:
                    print(cmd)
                if t is not None:
                    t.set_description(f"{page_title}→{pm.smw_prop}")
                wikipush.edit_wikison(
                    page_titles=[page_title],
                    entity_type_name=tm.topic_name,
                    property_name=pm.smw_prop,
                    value=wd_value,
                    force=not self.dry
                )
                if t is not None:
                    t.update()
            pass
                      
    def main(self,args):
        """
        command line handling
        """
        if args.about:
            print(Version.description)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
        elif args.createPropertyMap:
            mapping=self.createMapping()
            mapping.toYaml(args.createPropertyMap)
        else:  
            self.mapping=self.getMapping()
            topic=self.getTopic(topic_name=args.topic)
            if args.proplist:
                self.showProperties(topic=topic)
            if args.update:
                self.color_msg(Fore.BLUE,f"updating cache for {self.context.name}:{topic.name} from wiki {self.wikiId} ...")
                json_path,items=self.updateItemCache(topic.name)
                self.color_msg(Fore.BLUE,f"stored {len(items)} {topic.name} items to {json_path}")
            if args.props:
                self.sync(topic=topic,pk=args.primaryKey,pk_values=args.primaryKeyValues,prop_arglist=args.props)
      
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
