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

<img src="https://user-images.githubusercontent.com/15811701/137274030-0b3b2bc6-f928-4d61-866f-c5dfd7488960.PNG" width="100%" height="500px"/>

