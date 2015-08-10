# Pocket API
Pocket API for Python 3

##Usage:
At first, you will need and application token. Get your own at http://getpocket.com/developer/apps/new

Simple get method

```python
p_cli = Pocket()
p_cli.login()
result = p_cli.get(
    {
        "state": "unread",
        "count": 10
    }
)

for id, entry in result["list"].items():
    print(entry["resolved_title"])
```

But! You can make your own callable function

```python
p_cli.register_query(
    "get_two_archived",
    "get",
    {
        "state": "archive",
        "count": 2
    }
)
# now you can call it
p_cli.get_two_archived()
```



For more references and information about queries visit http://getpocket.com/developer/docs/overview

##Authentication:

OAuth 2.0, whole process is shown in login() function. Basically, user should be requested by an application to grant permissions in two steps.

```python
request = p_cli.get_request()
# open browser, let user grant access
access_user_code = p_cli.get_access(request)
a_token = access_user_code["access_token"]
username = access_user_code["username"]
```

Access token is necessary to work with API. Access token and username can be passed as argument, request_uri too. Default request_uri is http://getpocket.com.

```python
request_uri = http://yourapplicationwebsite.com
config = {
    "access_token": xxxxxxxx,
    "username": xxxxxxxx
}
p_cli = Pocket(config, request_uri)
```

