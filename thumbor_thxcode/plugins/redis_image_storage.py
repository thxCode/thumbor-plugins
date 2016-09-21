#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2014 PopKey martin@popkey.co

import hashlib
import json
from urllib2 import unquote
from datetime import datetime, timedelta
from rediscluster import StrictRedisCluster
from redis import ConnectionPool,Redis,RedisError
from . import on_exception
from tornado.concurrent import return_future
from thumbor.storages import BaseStorage
from thumbor.utils import logger


class Storage(BaseStorage):

    client = None

    def __unquote_url(url):
        return unquote(str(url)).decode('utf-8').encode('utf-8')

    def __init__(self, context):
        BaseStorage.__init__(self, context)
        
        if not Storage.client:
            Storage.client = self.__conn()
        
    def __conn(self):
        servers = self.context.config.REDIS_STORAGE_SERVERS
        
        size = len(servers)
        
        if size == 1:
            servers = servers[0].split(':')
            
            return ConnectionPool(
                        host=servers[0],
                        port=servers[1],
                        db=self.context.config.REDIS_STORAGE_DB,
                        password=self.context.config.REDIS_STORAGE_PASSWORD
                    )
        elif size > 0:
            temp_server = None
            temp_servers = []
            for server in servers:
                temp_server = servers[0].split(':')
                temp_servers.append({'host': temp_server[0], 'port': temp_server[1]})
                
            return StrictRedisCluster(startup_nodes=temp_servers, decode_responses=True)
        else:
            raise RuntimeError(
                "REDIS_STORAGE_SERVERS can't empty "
            )
    
    def __get_client(self):
        if not Storage.client:
            Storage.client = self.__conn()
        
        if type(Storage.client) == ConnectionPool:
            return Redis(connection_pool=Storage.client)
        else:
            return Storage.client

    def on_redis_error(self, fname, exc_type, exc_value):
        if self.context.config.REDIS_STORAGE_IGNORE_ERRORS is True:
            logger.error("[REDIS_IMAGE_STORAGE] %s" % exc_value)
            if fname == '_exists':
                return False
            return None
        else:
            raise exc_value

    def __key_for(self, url, unquote_url=__unquote_url):
        return 'thumbor-%s' % hashlib.md5(unquote_url(url)).hexdigest()

    def __crypto_key_for(self, url, unquote_url=__unquote_url):
        return 'thumbor-crypto-%s' % hashlib.md5(unquote_url(url)).hexdigest()

    def __detector_key_for(self, url, unquote_url=__unquote_url):
        return 'thumbor-detector-%s' % hashlib.md5(unquote_url(url)).hexdigest()

    @on_exception(on_redis_error, RedisError)
    def put(self, path, bytes):
        client = self.__get_client()
        path = self.__key_for(path)
        client.set(path, bytes)
        client.expireat(
            path, datetime.now() + timedelta(
                seconds=self.context.config.STORAGE_EXPIRATION_SECONDS
            )
        )
        
        logger.debug("[REDIS_IMAGE_STORAGE] put `{path}`".format(path=path))

    @on_exception(on_redis_error, RedisError)
    def put_crypto(self, path):
        if not self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            return

        if not self.context.server.security_key:
            raise RuntimeError(
                "STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True if no "
                "SECURITY_KEY specified"
            )
        
        path = self.__crypto_key_for(path)
        self.__get_client().set(path, self.context.server.security_key)
        
        logger.debug("[REDIS_IMAGE_STORAGE] put_crypto `{path}`".format(path=path))

    @on_exception(on_redis_error, RedisError)
    def put_detector_data(self, path, data):
        path = self.__detector_key_for(path)
        self.__get_client().set(path, json.dumps(data))
        
        logger.debug("[REDIS_IMAGE_STORAGE] put_detector_data `{path}`".format(path=path))

    @return_future
    def get_crypto(self, path, callback):
        @on_exception(self.on_redis_error, RedisError)
        def wrap(self, path):
            if not self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
                return None
            
            path = self.__crypto_key_for(path)
            crypto = self.__get_client().get(path)
            
            logger.debug("[REDIS_IMAGE_STORAGE] get_crypto `{path}`".format(path=path))
    
            return crypto if crypto else None
        
        callback(wrap(self, path))

    @return_future
    def get_detector_data(self, path, callback):
        @on_exception(self.on_redis_error, RedisError)
        def wrap(self, path):
            path = self.__detector_key_for(path)
            data = self.__get_client().get(path)
        
            logger.debug("[REDIS_IMAGE_STORAGE] get_detector_data `{path}`".format(path=path))
            
            return json.loads(data) if data else None
        
        callback(wrap(self, path))

    @return_future
    def exists(self, path, callback):
        @on_exception(self.on_redis_error, RedisError)
        def _exists(self, path):
            path = self.__key_for(path)
            result = self.__get_client().exists(path)
            
            if result :
                logger.debug("[REDIS_IMAGE_STORAGE] exists `{path}`".format(path=path))
            
            return result
        
        callback(_exists(self, path))


    @on_exception(on_redis_error, RedisError)
    def remove(self, path):
        path = self.__key_for(path)
        self.__get_client().delete(path)
        
        logger.debug("[REDIS_IMAGE_STORAGE] remove `{path}`".format(path=path))
        

    @return_future
    def get(self, path, callback):
        @on_exception(self.on_redis_error, RedisError)
        def wrap(self, path):
            path = self.__key_for(path)
            result = self.__get_client().get(path)
            
            logger.debug("[REDIS_IMAGE_STORAGE] get `{path}`".format(path=path))
            
            return result if result else None

        callback(wrap(self, path))