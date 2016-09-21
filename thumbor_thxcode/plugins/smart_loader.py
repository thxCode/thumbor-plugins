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
from thumbor.utils import logger
from thumbor.loaders import file_loader, http_loader, LoaderResult
from pymongo import MongoClient
from pymongo.errors import AutoReconnect
from bson.objectid import ObjectId
import gridfs

def __get_client(context):
    client = MongoClient(context.config.MONGODB_STORAGE_SERVERS)
    database = client[context.config.MONGODB_STORAGE_DB]
    
    return gridfs.GridFS(database)

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
        result = LoaderResult()
        try:
            database = __get_client(context)
            img = database.get(ObjectId(path[9:]))
            
            logger.debug("[SMART_LOADER_MONGO] get `{path}`".format(path=path))
            result.successful = True
            result.buffer = img.read()
            result.metadata.update(
                size=img.length
            )
            
            print img.metadata
            
        except Exception as exc_value:
            logger.error("[SMART_LOADER_MONGO] %s" % exc_value)
            result.successful = False
            result.error = "%s" % exc_value
        
        callback(result)
    else:
        http_loader.load(context, path, __callback_wrapper, __normalize_url)

