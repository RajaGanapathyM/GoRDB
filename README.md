# GoRDB - GraphQL On Relational DB
A lightweight python library for implementing GraphQL on Relational DB Tables in few steps using python dicts. The library is built over strawberry-graphql for creating graphQL schema from dataclasses

```
Example Graph query on Relational DB having User table and Subscriptions table implemented using GoRDB

{
    User(filterStr:" @#ROWNUM#@ <5 ")
    {
        USERID,
        USERNAME,
        Subscriptions{
            PRODUCTID
        }
    }
}
```

<img src="https://user-images.githubusercontent.com/15811701/137274030-0b3b2bc6-f928-4d61-866f-c5dfd7488960.PNG" width="100%" height="300px"/>

<H1> Implementation Steps</H1>

<h2>Step-1:</h2>
Import GoRDB library

```python
from GoRDB import GoRDB
```

<h2>Step-2:</h2>
Initialize connection configs for your DB. Here config is shown for Oracle DB, You can set this for any RDB of your choice

```python
import cx_Oracle as orac
orac.init_oracle_client(lib_dir= "./instantclient_19_12")
import pickle
db=pickle.load(open("G:db_config.pickle","rb"))
username=db['username']
pwd=db['pwd']
db_uri=db['uri']
```

<h2>Step-3:</h2> 
Create function which will receive an connection-id (string) and query (string) as arguments and return query results ( List of tuples) as return

```python

connection_pools_by_connection_id={}
connection_pools_by_connection_id['CUSTOMERDB'] = orac.SessionPool(username, pwd, db_uri,min = 5, max = 20, increment = 5, threaded = True,getmode = orac.SPOOL_ATTRVAL_WAIT)

def query_executor(connection_id,query_str):
    global connection_pools_by_connection_id
    custdb=connection_pools_by_connection_id[connection_id].acquire()
    local_cursor=custdb.cursor()
    local_cursor.execute(query_str)
    query_result=local_cursor.fetchall()   
    return query_result
```

<h2>Step-4:</h2> 

Add node definition for each node in your graph layer as dict in the format given below. 
<br>Nodes define the table in your Relational DB. Node alias is the node name which will be used in your Graph queries
<br>Features define the columns in your RDB table
<br>Edges define the relation between on node to another and corresponding mapping keys. set many_mapping = True if you the edge define one-to-many relationship
<br>Table connection id define the connection identifier which will be passed to query executor function
<br>Query executor define the function which will be called to execute query.

<br>Here for the example shown above we have 2 nodes.

```python
USER_node_dict={
    'node_alias':'User',
    'tbl_name':'CUSTOMERDB.USER_TABLE',
    'tbl_connection_id':'CUSTOMERDB',
    'query_executor':query_executor,
    
    
    'features':[
        {'feature_alias':'USERID','feature_name_in_table':'USERID_SNO'},
        {'feature_alias':'USERNAME','feature_name_in_table':'USERNAME'},
    ],
    
    'edges':[
        {'edge_alias':'Subscriptions','node_feature_alias':'USERID','foreign_node_alias':'Subscriptions','foreignNode_feature_alias':'SUBSCRIBERID','many_mapping':True}
        
    ]
        
}


SUBSCRIPTIONS_node_dict={
    'node_alias':'Subscriptions',
    'tbl_name':'CUSTOMERDB.SUBSCRIBER_PRODUCT_TABLE',
    'tbl_connection_id':'CUSTOMERDB',
    'query_executor':query_executor,
    
    
    'features':[
        {'feature_alias':'SUBSCRIBERID','feature_name_in_table':'SUBSCRIBERID_IDX'},
        {'feature_alias':'PRODUCTID','feature_name_in_table':'PRODUCTID_IDX'},
    ],
    
    'edges':[]
}
```
<h2>Step-5:</h2> 
Build your GraphQL Schema by passing the list of node definitions dict

```python
schema,node_builds_compiled=GoRDB.build_scheme_from_node_dict([USER_node_dict,SUBSCRIPTIONS_node_dict])


```

<h2>Step-6:</h2>

Thats all! Execute your Schema, and await on the response. Now you have succesfully running Graph query engine on you RDB tables

Note: the filterstr corresponds to the "WHERE" part of your nomrmal SQL query. if you want to use some table columns which are not defined in your node definition dict you need to wrap them with ' #@' and '#@ ', but if the column is already defined in the node definition dict this is not need(for example 'USERID' used in the below query)

```python
ding=schema.execute('{User(filterStr:" USERID > 5 and  @#ROWNUM#@ <5 "){USERID,USERNAME,Subscriptions{PRODUCTID}}}')
print(await ding)
```


<H1> Other features </H1>

GoRDB have helper function called show_graph which can be used to see the network diagram of your Schema

```python
GoRDB.show_graph([USER_node_dict,SUBSCRIPTIONS_node_dict])
```

![show_graph_example](https://user-images.githubusercontent.com/15811701/137302776-1654a4eb-eb5b-4df9-b438-73cf1473c528.PNG)

