#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import http.cookiejar as cookielib
import urllib.request
import urllib.parse
import json
from html.parser import HTMLParser

class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise RuntimeError("Second form on page")
            if self.in_form:
                raise RuntimeError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True


def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    # Authorization form
    def auth_user(email, password, client_id, scope, opener):
        response = opener.open(
            "http://oauth.vk.com/oauth/authorize?" + \
            "redirect_uri=http://oauth.vk.com/blank.html&response_type=token&" + \
            "client_id=%s&scope=%s&display=mobile" % (client_id, ",".join(scope))
            )
        doc = response.read()
        parser = FormParser()
        parser.feed(doc.decode())
        parser.close()
        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or \
          "email" not in parser.params:
              raise RuntimeError("Something wrong")
        parser.params["email"] = email
        parser.params["pass"] = password
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode('utf8'))
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.read(), response.geturl()

    # Permission request form
    def give_access(doc, opener):
        parser = FormParser()
        parser.feed(doc.decode())
        parser.close()
        if not parser.form_parsed or parser.url is None:
              raise RuntimeError("Something wrong")
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode('utf8'))
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.geturl()


    if not isinstance(scope, list):
        scope = [scope]
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib.request.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urllib.parse.urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)

    if urllib.parse.urlparse(url).path != "/blank.html":
        raise RuntimeError("Expected success here")
    answer = dict(split_key_value(kv_pair) for kv_pair in urllib.parse.urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise RuntimeError("Missing some values in answer")
    return answer["access_token"], answer["user_id"]


def call_method(name, params):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib.request.HTTPRedirectHandler())
    result = opener.open("https://api.vk.com/method/%s?%s" % (name, params))
    response = result.read()
    return json.loads(response.decode())


def searchGroups(**params):
    string = form_string(**params)
    result = call_method("groups.search", string)
    groups = []
    for item in result['response']['items']:
        if (item.get('is_closed') == 0):
            name = "%s %s" % (item.get('name'), item.get('id'))
            groups.append({"id":item.get('id'), "name":name})

    return groups


def get_countries(**params):
    string = form_string(**params)
    result = call_method("database.getCountries", string)

    countries = []
    for d in result['response']:
        countries.append({d['title']:d['cid']})

    return countries


def get_user_count(**params):
    string = form_string(**params)
    result = call_method("groups.getMembers", string)
    return result['response']['count']


def spam(**params):
    string = form_string(**params)
    result = call_method("wall.post", string)
    return result


def form_string(**params):
    string = ""
    for param in params:
        string = string + "%s=%s&" % (param, params[param])

    return string
