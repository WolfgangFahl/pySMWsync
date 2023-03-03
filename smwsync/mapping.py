'''
Created on 2023-03-03

@author: wf
'''
import dacite
import typing
import yaml
from dataclasses import dataclass

@dataclass
class PropMapping:
    smw_prop: str
    pid: str
    arg: typing.Optional[str]=None
    pid_label: typing.Optional[str]=None
    
class TopicMapping:
    """
    a property mapping for a given topic
    """    
    def __init__(self,topic_name:str):
        """
        initialize this topic mapping
        """
        self.topic_name=topic_name
        self.prop_by_arg={}
        self.prop_by_smw_prop={}
        
    def add_mapping(self,propm_record:dict):
        """
        add a property map record to the mapping
        """
        propm=dacite.from_dict(data_class=PropMapping,data=propm_record)
        self.prop_by_arg[propm.arg]=propm
        self.prop_by_smw_prop[propm.smw_prop]=propm
        

class Mapping:
    """
    a mapping for properties 
    """
    
    def fromYaml(self,yaml_path:str):
        """
        initialize me from the given yaml_path
        """
        # Read YAML file
        with open(yaml_path, 'r') as yaml_file:
            self.map_list = yaml.safe_load(yaml_file)
        self.map_by_topic={}
        for map_record in self.map_list:
            topic_map=TopicMapping(map_record["topic"])
            for propm_record in map_record["prop_list"]:
                topic_map.add_mapping(propm_record)
            self.map_by_topic[topic_map.topic_name]=topic_map
        pass
        
