from strawberry.dataloader import DataLoader
import random
from dataclasses import dataclass,make_dataclass
from datetime import datetime
import typing
import strawberry
from collections import defaultdict,namedtuple
import networkx as nx
from pyvis.network import Network

print_log=False
class Node:
    def __init__(self,tbl_name,node_alias,tbl_connection_id,query_executor):
        self.tbl_name=tbl_name
        self.node_alias=node_alias
        self.tbl_connection_id=tbl_connection_id
        self.features={}
        self.edges={}
        self.query_executor=query_executor
    def add_feature(self,feature_alias,feature_name_in_table,feature_type):
        self.features[feature_alias]=table_column(column_name=feature_name_in_table,column_alias=feature_alias,column_type=feature_type)

    def add_edge(self,edge_alias,foreign_node,local_feature_alias,foreign_feature_alias,many_mapping):
        if isinstance(foreign_node,Node):
            raise "Foreign Nodes should be compiled before adding an edge from it"
        else:
            self.edges[edge_alias]=table_column(column_name=edge_alias,
                                                column_alias=edge_alias,
                                                column_type=typing.List[foreign_node] if many_mapping else foreign_node,
                                                column_parent=foreign_node,
                                                column_localfetchkey=local_feature_alias,
                                                column_foreignfetchkey=foreign_feature_alias,
                                                column_isForeign=True,
                                                column_isList=many_mapping)
    def build_node_1(self):
        tbl_cols=list(self.features.values())+list(self.edges.values())
#         print(tbl_cols)
        tbl_def=table(table_name=self.tbl_name,
                          table_columns=tbl_cols,
                          table_alias=self.node_alias,
                          table_connection_id=self.tbl_connection_id
                          )
        self.graphql_node=get_graphqltype(tbl_def,query_executor=self.query_executor)
        self.graphql_node=build_graphl_type(self.graphql_node)
        return self.graphql_node
    
    def build_node_2(self):
        self.build_node_1()
        self.graphql_node=add_fields(self.graphql_node)
        self.graphql_node=build_graphl_type(self.graphql_node)
        return self.graphql_node
    
    def build_node(self):
        self.build_node_1()
        return self.build_node_2()
def create_graphql_schema(nodes_list):
    Query_node_def=Node(tbl_name=None,node_alias='Query',tbl_connection_id=None,query_executor=None)
    for node_obj in nodes_list:
        Query_node_def.add_edge(edge_alias=node_obj.table_alias,foreign_node=node_obj,local_feature_alias='Query',foreign_feature_alias=node_obj.table_columns_to_alias[0],many_mapping=True)
    Query=Query_node_def.build_node()
    schema = strawberry.Schema(query=Query)
    return schema
class DBloader():
    def __init__(self,prime_key,field_names,alias_name,table_name,table_connection_id,cls,querying_cls,multiple=True,filter_str=None):
        super(DBloader, self).__init__()
        self.prime_key=prime_key
        self.field_names=field_names
        self.table_name=table_name
        self.cls=cls
        self.querying_cls=querying_cls
        self.alias_name=alias_name
        self.table_connection_id=table_connection_id
        self.multiple=multiple
        if print_log:print('DBloader',self,str(self.prime_key),self.table_name,self.cls)
        self.loader = DataLoader(load_fn=self.get_batch_fn())
        self.alias_replace_with_table_name=dict(zip(alias_name,field_names))
        
        self.query_filter_str=filter_str
        if self.query_filter_str!=None:
            for from_ke,repl_ke in zip(alias_name,field_names):
                if from_ke in self.query_filter_str:
                    self.query_filter_str=self.query_filter_str.replace(" "+from_ke+" "," "+repl_ke+" ")
            self.query_filter_str=self.query_filter_str.replace(" @#","").replace("#@ ","")
    def get_batch_fn(self):
        async def batch_load_fn(keys):
            if print_log:print('batch_load_fn',self.querying_cls,keys,self.prime_key,self,self.table_name,self.cls)
            filter_str=str(tuple([ky for ky in keys if ky!=None]))
            if print_log:print('batch_load_fn',filter_str,self.prime_key,self)
            if filter_str[-2:]==",)":
                filter_str=filter_str[:-2]+")"

            fname=",".join(self.field_names)

            filter_ls=[]

            if filter_str!="()" and filter_str!=None:
                filter_ls.append(f"{self.prime_key} in {filter_str}")

            if self.query_filter_str!=None:
                filter_ls.append(self.query_filter_str)

            query_str=f"select {self.prime_key},{fname} from {self.table_name} "
            if filter_ls!=[]:
                query_str+=" where " + " and ".join(filter_ls)
            query_result=[]
            if print_log:print('batch_load_fn',query_str)
            

            if filter_ls!=[] or self.querying_cls==None :
                query_result=self.cls.query_executor(self.table_connection_id,query_str)
#             local_cursor.execute(query_str)
#             query_result=local_cursor.fetchall()

            response_dict=defaultdict(lambda : [],{}) if self.multiple else defaultdict(lambda : None,{}) 
            record_template=namedtuple('record',self.alias_name)
            if print_log:print("elf.multiple",self.multiple,query_result)
            all_result=[]
            if len(query_result)>0:
                for result in query_result:
                    #dict(zip(self.alias_name,result[1:]))
                    record=record_template(*result[1:])
                    if self.multiple:
                        
                        response_dict[result[0]].append(self.cls(**record._asdict()))
                        all_result.append(response_dict[result[0]][-1])
                    else:
                        response_dict[result[0]]=record
                        all_result.append(record)
            else:
                for k in keys:
                    if self.multiple:response_dict[k]=[]
                    else:response_dict[k]=None
            if print_log:
                print("OUTER")
                print(response_dict)
            
            if self.querying_cls!=None:
                all_result=None
            response=[response_dict[k] if k !=None else all_result for k in keys]
            if print_log:print("\nRESPPPP\n",self.table_name,response)
            return response
        return batch_load_fn
def make_class(class_name,class_vars):
    return type(class_name, (object, ), {i:None for i in class_vars})
@classmethod
def get_data_loader(cls,pkey,isList,calling_cls,filter_str=None):
    if print_log:print('get_data_loader',str(cls),str(pkey),"{",str(filter_str))
    if (pkey,filter_str) not in cls.data_loader:
        pkey_tabl=None
        for col in cls.table_dataclass.table_columns:
            if col.column_alias==pkey:
                pkey_tabl=col.column_name

        cls.data_loader[(pkey,filter_str)]=DBloader(prime_key=pkey_tabl,field_names=cls.table_internal_columns,
                                   alias_name=cls.table_internal_columns_to_alias,
                                   table_name=cls.table_name,
                                   querying_cls=calling_cls,
                                   table_connection_id=cls.table_connection_id,cls=cls,multiple=isList,filter_str=filter_str)   
    return cls.data_loader[(pkey,filter_str)].loader

def function_constructor(self_key,parent_class,self_prime_key,foerign_prime_key,return_type,ext_bool,isList):
    if print_log:print('function_constructor',self_key,return_type)
    async def get_filed(self,info,filter_str:typing.Optional[str]=None)->typing.Optional[return_type]:
        if print_log:print("get_filed",(parent_class,self_prime_key,filter_str))
        dl=parent_class.get_data_loader(pkey=foerign_prime_key,isList=isList,calling_cls=self,filter_str=filter_str)
#         dl=parent_class.get_data_loader(self_prime_key,filter_str)
        if print_log:print("\DLLLLLLLLLLL\n",dl,parent_class)
#         print(getattr(self,self_prime_key))
#         if self==None:
#         random_key
        rec=await dl.load(getattr(self,self_prime_key) if self!=None else None)
        if print_log:print("\nHAIII\n",self_key,rec)
#         if print_log:
        if rec==None: return None
        if print_log:print("RECCCCCCCC",rec)
        return rec if ext_bool else getattr(rec,self_key) 
    return get_filed

@dataclass
class table_column:
    column_name:str
    column_alias:str
    column_type:str=typing.Optional[str]
    column_parent:str="self"
    column_localfetchkey:str="self"
    column_foreignfetchkey:str="self"
    column_isForeign:bool=False
    column_isList:bool=False
        
@dataclass
class table:
    table_alias:str
    table_name:str
    table_connection_id:str
    table_columns:typing.List[table_column]
        
# graphql_type=None
def get_graphqltype(table_dataclass,query_executor):
#     global graphql_type
#     print(table_dataclass.table_columns)
    graphql_type=make_dataclass(table_dataclass.table_alias,[(col.column_alias,col.column_type) for col in table_dataclass.table_columns if  not col.column_isForeign])
    graphql_type.data_loader={}
    graphql_type.table_connection_id=table_dataclass.table_connection_id
    graphql_type.table_name=table_dataclass.table_name
    graphql_type.table_alias=table_dataclass.table_alias
    graphql_type.table_columns=[col.column_name for col in table_dataclass.table_columns]
    graphql_type.table_columns_to_alias=[col.column_alias for col in table_dataclass.table_columns]
    graphql_type.table_columns_type=[col.column_type for col in table_dataclass.table_columns]
    graphql_type.table_columns_pclass=[col.column_parent for col in table_dataclass.table_columns]
#     graphql_type.table_columns_pkey=[col.column_fetchkey for col in table_dataclass.table_columns] 
    graphql_type.table_internal_columns=[col.column_name for col in table_dataclass.table_columns if not col.column_isForeign]
    graphql_type.table_internal_columns_to_alias=[col.column_alias for col in table_dataclass.table_columns if not col.column_isForeign]

#     print(graphql_type.table_internal_columns,table_dataclass.table_columns )
    graphql_type.get_data_loader=get_data_loader
#     graphql_type.multiple=table_dataclass.table_manyrow_kind
    graphql_type.table_dataclass=table_dataclass
    graphql_type.query_executor=query_executor
    return graphql_type

def add_fields(graphql_type):
    for col in graphql_type.table_dataclass.table_columns:
    
        ext=col.column_isForeign
        if ext:
            k=col.column_alias
            t=col.column_type
            parent_class=col.column_parent
            assert parent_class!='self',"Foreign Node not found"
            localpkey=col.column_localfetchkey
            foerignpkey=col.column_foreignfetchkey
            # print("foerignpkey",foerignpkey)
            assert foerignpkey in parent_class.table_columns_to_alias,"foreignNode_feature_alias is not found in foreign nod"
            pclass=parent_class if parent_class!='self' else graphql_type
            isList=col.column_isList
            if print_log:print(k,pclass,foerignpkey,t,ext)
            setattr(graphql_type,k,strawberry.field(resolver= function_constructor(	self_key=k,parent_class=pclass,self_prime_key=localpkey,foerign_prime_key=foerignpkey,return_type=t,ext_bool=ext,isList=isList)))
    
    return graphql_type

def build_graphl_type(graphql_type):
    graphql_type=strawberry.type(graphql_type)
    return graphql_type
global_nodes_dict={}
def build_node_from_dict(node_def_dict):
    global global_nodes_dict
    
    node_def=Node(tbl_name=node_def_dict['tbl_name'],node_alias=node_def_dict['node_alias'],tbl_connection_id=node_def_dict['tbl_connection_id'],query_executor=node_def_dict['query_executor'])

    for each_f in node_def_dict['features']:
    	if not 'feature_type' in each_f:
    		each_f['feature_type']=typing.Optional[str]
    	else:
    		each_f['feature_type']=typing.Optional[each_f['feature_type']]

    	node_def.add_feature(feature_alias=each_f['feature_alias'],feature_name_in_table=each_f['feature_name_in_table'],feature_type=each_f['feature_type'])
    
    for each_e in node_def_dict['edges']:
        node_def.add_edge(edge_alias=each_e['edge_alias'],foreign_node=global_nodes_dict[each_e['foreign_node_alias']],local_feature_alias=each_e['node_feature_alias'],foreign_feature_alias=each_e['foreignNode_feature_alias'],many_mapping=each_e['many_mapping'])

    node=node_def.build_node()
    global_nodes_dict[node_def_dict['node_alias']]=node
    
    return node

def pre_build_node_from_dict(node_def_dict):
    global global_nodes_dict
    
    node_def=Node(tbl_name=node_def_dict['tbl_name'],node_alias=node_def_dict['node_alias'],tbl_connection_id=node_def_dict['tbl_connection_id'],query_executor=node_def_dict['query_executor'])

    for each_f in node_def_dict['features']:
    	if not 'feature_type' in each_f:
    		each_f['feature_type']=typing.Optional[str]
    	else:
    		each_f['feature_type']=typing.Optional[each_f['feature_type']]
    	node_def.add_feature(feature_alias=each_f['feature_alias'],feature_name_in_table=each_f['feature_name_in_table'],feature_type=each_f['feature_type'])
    
#     node_def=node_def.build_node_1()
    global_nodes_dict[node_def_dict['node_alias']]=node_def.build_node_1()
    
    return node_def_dict,node_def

def post_build_node_from_dict(node_def_dict,node_def):
    
    global global_nodes_dict
    for each_e in node_def_dict['edges']:
        node_def.add_edge(edge_alias=each_e['edge_alias'],foreign_node=global_nodes_dict[each_e['foreign_node_alias']],local_feature_alias=each_e['node_feature_alias'],foreign_feature_alias=each_e['foreignNode_feature_alias'],many_mapping=each_e['many_mapping'])

    global_nodes_dict[node_def.node_alias]=node_def.build_node_2()
    return global_nodes_dict[node_def.node_alias]

def build_scheme_from_node_dict(node_dicts):
    global global_nodes_dict
    nodes_build=[]

    for each_n in node_dicts:
        nodes_build.append(pre_build_node_from_dict(each_n))
    node_final_build=[]
    for each_n in  nodes_build:
        node_final_build.append(post_build_node_from_dict(*each_n))
    schema=create_graphql_schema(node_final_build)  
    return schema,node_final_build

def show_graph(node_dicts):
    G = nx.DiGraph()
    for each_no in node_dicts:
        G.add_node(each_no['node_alias'])
        G.nodes[each_no['node_alias']]['tbl_name']=each_no['tbl_name']
        G.nodes[each_no['node_alias']]['label']=each_no['node_alias']
        G.nodes[each_no['node_alias']]['title']=each_no['tbl_name']
        G.nodes[each_no['node_alias']]['tbl_connection_id']=each_no['tbl_connection_id']
        G.nodes[each_no['node_alias']]['tbl_name']=each_no['tbl_name']
        # G.nodes[each_no['node_alias']]['features']=each_no['features']

        for each_ed in each_no['edges']:
            G.add_edge(each_no['node_alias'],each_ed['foreign_node_alias'])
            G[each_no['node_alias']][each_ed['foreign_node_alias']]['node_feature_alias']=each_ed['node_feature_alias']
            G[each_no['node_alias']][each_ed['foreign_node_alias']]['foreignNode_feature_alias']=each_ed['foreignNode_feature_alias']
            G[each_no['node_alias']][each_ed['foreign_node_alias']]['many_mapping']=each_ed['many_mapping']
            G[each_no['node_alias']][each_ed['foreign_node_alias']]['title']='{} to {}'.format(each_ed['node_feature_alias'],each_ed['foreignNode_feature_alias'])
    # print(G)
    nt = Network('100%', '100%', directed=True)
    nt.from_nx(G)
    nt.set_edge_smooth('dynamic')
    nt.show('nx.html')