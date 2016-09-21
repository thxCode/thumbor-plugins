#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2015 Thumbor-Community
# Copyright (c) 2011 globo.com timehome@corp.globo.com

from datetime import datetime, timedelta
from cStringIO import StringIO

from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
from gridfs.errors import FileExists,GridFSError
from pymongo.errors import AutoReconnect
from . import on_exception

from thumbor.storages import BaseStorage
from thumbor.utils import logger
from tornado.concurrent import return_future


class Storage(BaseStorage):
    
    client = None

    def __init__(self, context):
        BaseStorage.__init__(self, context)
        
        if not Storage.client:
            Storage.client = self.__conn()
        
    def __conn(self):
        return MongoClient(self.context.config.MONGODB_STORAGE_SERVERS)
    
    def __get_client(self):
        if not Storage.client :
            Storage.client = self.__conn()
        
        # reconnect
        try:
            database = Storage.client[self.context.config.MONGODB_STORAGE_DB]
        except AutoReconnect as exc_value:
            Storage.client = self.__conn()
            database = Storage.client[self.context.config.MONGODB_STORAGE_DB]

        return gridfs.GridFS(database)
    
    def on_mongo_error(self, fname, exc_type, exc_value):
        if self.context.config.MONGODB_STORAGE_IGNORE_ERRORS is True:
            logger.error("[MONGODB_UPLOAD_STORAGE] %s" % exc_value)
            if fname == '_exists':
                return False
            return None
        else:
            raise exc_value

    @on_exception(on_mongo_error, FileExists)
    def put(self, path, bytes):
        database = self.__get_client()

        img_doc = {
            'path': path,
            'create_at': datetime.now()
        }

        img_doc_with_crypto = dict(img_doc)
        if self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            if not self.context.server.security_key:
                raise RuntimeError("STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True if no SECURITY_KEY specified")
            img_doc_with_crypto['crypto'] = self.context.server.security_key

        img_object_id = database.put(StringIO(bytes), **img_doc)
        
        logger.debug("[MONGODB_UPLOAD_STORAGE] put `{path}`".format(path=path))

        return 'scmongo_' + str(img_object_id)
    
    @return_future
    def exists(self, path, callback):
        @on_exception(self.on_mongo_error, GridFSError)
        def _exists(self, path):
            database = self.__get_client()
            
            result = database.exists(ObjectId(path[8:]))
    
            logger.debug("[MONGODB_UPLOAD_STORAGE] exists `{path}`".format(path=path))
        
            return False if not result else True
        
        callback(wrap(self, path))
    
    @return_future
    def get(self, path, callback):
        @on_exception(self.on_mongo_error, GridFSError)
        def wrap(self, path):
            database = self.__get_client()
    
            contents = database.get(ObjectId(path[8:])).read()
            
            logger.debug("[MONGODB_UPLOAD_STORAGE] get `{path}`".format(path=path))
    
            return contents if contents else None
        
        callback(wrap(self, path))
    
    
    @on_exception(on_mongo_error, GridFSError)
    def remove(self, path):
        if not self.exists(path):
            return

        database = self.__get_client()

        database.delete(ObjectId(path[8:]))
        
        logger.debug("[MONGODB_UPLOAD_STORAGE] remove `{path}`".format(path=path))
        