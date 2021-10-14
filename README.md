# GoRDB
A lightweight python library for implementing GraphQL on Relational DB Tables in few steps using python dicts

```
Example GraphQL on Relational DB having User table and Subscripts table implemented using GoRDB

{
    User(filterStr:" @#ROWNUM#@ <5 ")
    {
        USERID,
        USERNAME,
        SUBSCRIPTIONS{
            PRODUCTID
        }
    }
}
```

<img src="https://user-images.githubusercontent.com/15811701/137274030-0b3b2bc6-f928-4d61-866f-c5dfd7488960.PNG" width="100%" height="300px"/>


<h2>Step-1:</h2>
Import GoRDB library

```python
import GoRDB
```

<h2>Step-2:</h2>
Initialize connection configs of your DB. Here config are shown for Oracle DB

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
