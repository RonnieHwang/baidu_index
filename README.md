# **Introduction**
收集百度指数，需python版本2.7以上，数据存入mongo。
改版后的百度指数不需要图像识别，所有指数数据会在一次请求中返回。

**step 1**
需浏览器登录百度指数，获取cookie, 存入mongo

**step 2**
运行程序

# **PROXY**
squid

# **MONGO DATA**

**index col**
{
    "_id" : ObjectId("5ac9db169a0a99fbdc9c9678"),
    "date" : ISODate("2018-03-04T00:00:00.000Z"),
    "index" : 9509,
    "keyword" : "浦发银行",
    "update_time" : ISODate("2018-04-09T11:18:50.372Z")
}

**keyword col**
{
    "_id" : ObjectId("5b5ecb75e8d92d6f7b6bfe11"),
    "create_time" : ISODate("2018-07-30T16:25:25.975Z"),
    "keyword" : "景点"
}

**invalid keyword col**
{
    "_id" : ObjectId("5b320900f0e47cea8a984f43"),
    "keyword" : "陈炎顺"
}

**cookie col**
{
    "_id" : ObjectId("5b3231db81b6c0fe250a40ac"),
    "username" : "xxx",
    "password" : "xxx",
    "cookie" : [ 
        {
            "domain" : ".index.baidu.com",
            "secure" : false,
            "value" : "1540265558",
            "expiry" : 1572921900,
            "path" : "/",
            "httpOnly" : false,
            "name" : "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc"
        }, 
        ...
    ],
    "update_time" : ISODate("2018-11-05T10:45:04.690Z"),
    "last_login_time" : ISODate("2018-10-26T11:09:57.331Z")
}

# **TODO**
1.Replace func print with logger
2.Login system
