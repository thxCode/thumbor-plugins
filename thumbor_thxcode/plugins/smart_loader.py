#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2015 Thumbor-Community
# Copyright (c) 2011 globo.com timehome@corp.globo.com

from urllib2 import unquote
from tornado.concurrent import return_future
from thumbor.loaders import file_loader, http_loader
from . import mongo_upload_storage


@return_future
def load(context, path, callback):

    def __unquote_url(url) :
        return unquote(str(url)).decode('utf-8').encode('utf-8')

    def __normalize_url(url):
        rurl = __unquote_url(url)
        if rurl.find('http') == 0 :
            if rurl.find('://') < 0 :
                url = rurl.replace(':', ':/')
        else:
            url = 'http://%s' % rurl
        return url
    
    def __callback_wrapper(result):
        if result.successful:
            callback(result)
        else:
            file_loader.load(context, path, callback)
    
    # MongoDB Upload Storage
    if path.find('sc_mongo_') == 0:
        mongo_upload_storage.get(context, path, callback)
    else:
        http_loader.load(context, path, __callback_wrapper, __normalize_url)

