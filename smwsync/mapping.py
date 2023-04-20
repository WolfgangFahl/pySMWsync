'''
Created on 2023-03-03

@author: wf
'''
import dacite
import json
import typing
import yaml
import dataclasses
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
        self.prop_by_pid={}
        
    def __repr__(self):
        """
        return my representation
        """
        tm_dict=self.asdict()
        tm_text=str(tm_dict)
        return tm_text
        
    def asdict(self):
        prop_list=[]
        for pm in self.prop_by_smw_prop.values():
            pm_record=dataclasses.asdict(pm)
            prop_list.append(pm_record)
        tm_dict={
            'topic': self.topic_name,
            'prop_list':prop_list
        }
        return tm_dict
        
    def add_mapping4record(self,propm_record:dict)->PropMapping:
        """
        add a property map record to the mapping
        
        Args:
            propm_record(dict): the record to instantiate the PropMapping from
            
        Returns:
            PropMapping: the property Mapping created and added
        """
        propm=None
        try:
            propm=dacite.from_dict(data_class=PropMapping,data=propm_record)
            self.add_mapping(propm)
        except Exception as ex:
            print(f"Warning property mapping {propm_record} could not be added: {str(ex)}")
            pass
        return propm
        
    
    def add_mapping(self,propm:PropMapping):
        """
        add a property Mapping 
        Args:
            propm:PropMapping
        """
        if propm.arg:
            self.prop_by_arg[propm.arg]=propm
        self.prop_by_smw_prop[propm.smw_prop]=propm
        if propm.pid:
            self.prop_by_pid[propm.pid]=propm
            
    def getPkSMWPropMap(self,pk:str)->PropMapping:
        pm=None
        if pk=="qid":
            if not pk in self.prop_by_pid:
                raise Exception(f"primary key arg {pk} of topic {self.topic_name}  has no mapping")
            pm=self.prop_by_pid[pk]
        return pm
    
    def getPmForArg(self,arg:str)->PropMapping:
        if not arg in self.prop_by_arg:
            raise Exception(f"property arg {arg} of topic {self.topic_name}  has no mapping")
        pm=self.prop_by_arg[arg]
        return pm
        

class Mapping:
    """
    a mapping for properties 
    """
    
    def __init__(self):
        """
        constructor
        """
        self.map_by_topic={}
    
    def fromYaml(self,yaml_path:str):
        """
        initialize me from the given yaml_path
        
        Args:
            yaml_path(str): the path to the yaml file
        """
        # Read YAML file
        with open(yaml_path, 'r') as yaml_file:
            self.map_list = yaml.safe_load(yaml_file)
        for map_record in self.map_list:
            topic_map=TopicMapping(map_record["topic"])
            for propm_record in map_record["prop_list"]:
                topic_map.add_mapping4record(propm_record)
            self.map_by_topic[topic_map.topic_name]=topic_map
        pass
    
    def toYaml(self,yaml_path:str):
        """
        store me to the given yaml_path
        
        Args:
            yaml_path(str): the path to the yaml file
        """
        map_list=[]
        for tm in self.map_by_topic.values():
            map_list.append(tm.asdict())
        with open(yaml_path, 'w') as yaml_file:
            yaml.dump(map_list, yaml_file,sort_keys=False)