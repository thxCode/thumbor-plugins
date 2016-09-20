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

from thumbor.storages import BaseStorage
from tornado.concurrent import return_future


class Storage(BaseStorage):

    def __conn__(self):
        client = MongoClient(self.context.config.MONGODB_STORAGE_SERVERS)

        database = client[self.context.config.MONGODB_STORAGE_DB]

        return gridfs.GridFS(database)

    def put(self, path, bytes):
        database = self.__conn__()

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

        return 'scmongo_' + str(img_object_id)
    
    @return_future
    def exists(self, path, callback):
        database = self.__conn__()
        
        result = database.exists(ObjectId(path[8:]))

        if not result :
            callback(False)
        else:
            callback(True)

    @return_future
    def get(self, path, callback):
        database = self.__conn__()

        contents = database.get(ObjectId(path[8:])).read()

        callback(contents)
        
    def remove(self, path):
        if not self.exists(path):
            return

        database = self.__conn__()

        img_fs.database(ObjectId(path[8:]))
        