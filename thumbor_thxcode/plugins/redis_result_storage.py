#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2014 PopKey martin@popkey.co

import time
from datetime import datetime, timedelta
from rediscluster import RedisCluster
from redis import ConnectionPool,Redis,RedisError
from . import on_exception
from thumbor.result_storages import BaseStorage
from thumbor.utils import logger


class Storage(BaseStorage):

    client = None
    start_time = None

    def __init__(self, context):
        BaseStorage.__init__(self, context)
        
        if not Storage.client:
            Storage.client = self.__conn()
        
        if not Storage.start_time:
            Storage.start_time = time.time()
        
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
                temp_servers.append({host: temp_server[0], port: temp_server[1]})
                
            return StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
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
        if self.context.config.REDIS_RESULT_STORAGE_IGNORE_ERRORS is True:
            logger.error("[REDIS_RESULT_STORAGE] %s" % exc_value)

            return None
        else:
            raise exc_value

    def __accept_webp(self):
        return (self.context.config.AUTO_WEBP and self.context.request.accepts_webp)

    def __key_for(path):
        if self.__accept_webp():
            path = "thumbor-result-webp-%s" % path
        else:
            path = "thumbor-result-%s" % path
            
        return path

    def __get_max_age(self):
        default_ttl = self.context.config.RESULT_STORAGE_EXPIRATION_SECONDS
        if self.context.request.max_age == 0:
            return self.context.request.max_age

        return default_ttl

    @on_exception(on_redis_error, RedisError)
    def put(self, path, bytes):
        key = self.__key_for(path)
        result_ttl = self.__get_max_age()

        logger.debug("[REDIS_RESULT_STORAGE] put `{path}`".format(path=path))

        client = self.__get_client()
        client.set(key, bytes)

        if result_ttl > 0:
            client.expireat(
                key,
                datetime.now() + timedelta(
                    seconds=result_ttl
                )
            )

        return key
    
    @return_future
    def get(self, path, callback):
        @on_exception(self.on_redis_error, RedisError)
        def wrap(self, path):
            key = self.__key_for(path)
            result = self.__get_client().get(key)
        
            logger.debug("[REDIS_IMAGE_STORAGE] get `{path}`".format(path=path))
            return result if result else None

        callback(wrap(self, path))

    @on_exception(on_redis_error, RedisError)
    def last_updated(self, path):
        key = self.__key_for(path)
        max_age = self.__get_max_age()

        if max_age == 0:
            return datetime.fromtimestamp(Storage.start_time)

        ttl = self.__get_client().ttl(key)

        if ttl >= 0:
            return datetime.now() - timedelta(
                seconds=(
                    max_age - ttl
                )
            )

        if ttl == -1:
            # Per Redis docs: -1 is no expiry, -2 is does not exists.
            return datetime.fromtimestamp(Storage.start_time)

        # Should never reach here. It means the storage put failed or the item
        # somehow does not exists anymore.
        return datetime.now()