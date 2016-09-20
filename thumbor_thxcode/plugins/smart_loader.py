#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2015 Thumbor-Community
# Copyright (c) 2011 globo.com timehome@corp.globo.com

from tornado.concurrent import return_future
from thumbor.loaders import file_loader_http_fallback
from . import mongo_upload_storage


@return_future
def load(context, path, callback):
    
    # MongoDB Upload Storage
    if path.index('scmongo_') == 0:
        mongo_upload_storage.get(context, path, callback)
    else:
        file_loader_http_fallback.load(context, path, callback)

