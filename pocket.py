#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Version: Python 3
# License: MIT
# Author: jaduse

import urllib.request
import urllib.response
import urllib.parse
import json
import urllib.error
import sys


class Pocket(object):

    """
    Pocket object

    statics:
        CONSUMER_KEY: consumer key given from http://getpocket.com/developer
        OAUTH_METHODS: authentication methods for OAuth
        API_URL: base url for all api calls
        API_METHODS: api calls

    object:
        Pocket(self,
            config (dict): configuration of access_token and username,
                            both can be stored in file
            redirect_uri (str): path for redirection after authentication

    """
    CONSUMER_KEY = "PUT YOUR KEY HERE"
    OAUTH_METHODS = {"request": "https://getpocket.com/v3/oauth/request",
                     "auth": "https://getpocket.com/v3/oauth/authorize"}
    API_URL = "https://getpocket.com/v3/"
    API_METHODS = ["get", "add", "send"]

    def __init__(
            self,
            config=None,
            redirect_uri="http://getpocket.com"
    ):
        self.config = config
        self.redirect_uri = redirect_uri

    def __repr__(self):
        return "Pocket(config={},redirect_uri={})".format(
            self.config,
            self.redirect_uri
        )

    """
    OAuth
    -----

    get_request: requesting for request token, returns False on fail

    get_access: requesting for access token, returns False on fail
                req_code (str): request code from get_request,
                returns dict on success, include username and 
                access token

    login: whole auth routine, asks for user to approve application
            in browser, return False on fail

    See more: http://getpocket.com/developer/docs/authentication
    """
    def get_request(self):
        req_opener = urllib.request.build_opener()
        req_params = urllib.parse.urlencode(
            {
                "consumer_key": self.CONSUMER_KEY,
                "redirect_uri": self.redirect_uri
            }
        ).encode("ascii")

        request = urllib.request.Request(
            self.OAUTH_METHODS["request"],
            data=req_params
        )
        response = req_opener.open(request)

        if response.code != 200:
            return False

        response_fp = response.fp.readline()
        req_code = urllib.parse.parse_qs(response_fp)[b"code"][0]

        return req_code.decode("utf-8")

    def get_access(self, req_code):
        auth_opener = urllib.request.build_opener()
        auth_params = urllib.parse.urlencode(
            {
                "consumer_key": self.CONSUMER_KEY,
                "code": req_code
            }
        ).encode("ascii")

        request = urllib.request.Request(
            self.OAUTH_METHODS["auth"],
            data=auth_params
        )
        response = auth_opener.open(request)

        if response.code != 200:
            return False

        response_fp = response.fp.readline()
        res_parsed = urllib.parse.parse_qs(response_fp)
        username = res_parsed[b"username"][0].decode("utf-8")
        access_token = res_parsed[b"access_token"][0].decode("utf-8")

        return {
            "access_token": access_token,
            "username": username
        }

    def login(self):
        req_code = self.get_request()
        if not req_code:
            raise PocketException("Failed to obtain request code")

        login_url = ("https://getpocket.com/auth/authorize?"
                     "request_token={}&redirect_uri={}").format(
                        req_code,
                        self.redirect_uri
                    )

        print("{} {}\n".format(
                    ("Please allow application access to your"
                     " acc and then pres enter:"), login_url
            )
        )
        input()

        access_user_code = self.get_access(req_code)

        if not access_user_code:
            raise PocketException("Failed to obtain access code")

        self.config = access_user_code

        return True

    """
    Requesting api
    --------------

    method: makes request for api, returns PocketResponse object,
            return False on fail
            query (dict): representing request
            method_type (str): type of api call, references to API_METHODS

    register_query: makes pre-defined queries callable as function,
                    kind of macros
                    Syntax:
                        {
                            name (str): (
                                method (str), query (dict)
                            )
                        }

                    eg.
                        {
                            "get_two" : (
                                "get", {"count":2}
                            )
                        }

            name (str): name of macro, also callable
            method (str): method of query
            query (dict): query, which will be requested

    """
    def method(self, query, method_type):
        if not isinstance(query, dict):
            return False

        query["consumer_key"] = self.CONSUMER_KEY
        query["access_token"] = self.config["access_token"]
        params = json.dumps(query).encode("ascii")

        req_url = "{}{}".format(self.API_URL, method_type)
        req_query = urllib.request.build_opener()
        req_headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(
            req_url,
            data=params,
            headers=req_headers
        )

        try:
            response = req_query.open(request)

        except urllib.error.HTTPError as err:
            print("{0}\n".format(err), file=sys.stderr)
            return False

        return PocketResponse(response)

    def register_query(self, name, method, query):
        if not isinstance(query, dict):
            return False

        def query_callback(**kwargs):
            if not hasattr(self, method):
                raise PocketException(
                    "Wrong method type. Allowed are get, add, send"
                )

            callback = getattr(self, method)
            query.update(kwargs)
            return callback(query)

        setattr(self, name, query_callback)
        return True

    """
    Endpoints
    ---------

    get: for get api method
    add: for add api method
    send: for send api method

    This is bit messy, hate this 'send' obstructive stuff, but whatever
    also
    See: http://getpocket.com/developer/docs/v3/modify
    """
    def get(self, query):
        return self.method(query, "get")

    def add(self, query):
        return self.method(query, "add")

    def send(self, query):
        actions = {"actions": query}
        return self.method(actions, "send")


class PocketException(Exception):
    """
    Basic Pocket exception
    """
    pass


class PocketResponse(object):
    """
    Represents response of Pocket and make data accesible as dict

    response (HTTPResponse): response from API
    code (int): response HTTP code
    method (str): api method of response
    data (dict): response data
    """

    def __init__(self, response):
        self.code = response.code
        self.method = urllib.parse.urlparse(
            response.url).path.split("/")[-1]
        self.data = json.loads(
            response.read().decode("utf-8")
        )

    def __getitem__(self, key):
        if key not in self.data:
            raise PocketException(KeyError)

        return self.data[key]
