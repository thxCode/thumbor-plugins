# Version
0.0.1

# Plugins
## Loader
`thumbor_thxcode.plugins.smart_loader` use for support smart loader more.
## Storage
`thumbor_thxcode.plugins.mongo_upload_storage` use for support MongoDB access.
`thumbor_thxcode.plugins.redis_image_storage` and `thumbor_thxcode.plugins.redis_result_storage` use for support Redis access.

# Configuration
mongo_upload_storage:
```
MONGODB_STORAGE_SERVERS = 'MongoDB access url, either single server or cluster server'
MONGODB_STORAGE_DB = 'MongoDB database name'
MONGODB_STORAGE_IGNORE_ERRORS = 'ignore error, default false'
```
redis_image_storage and redis_result_storage:
```
REDIS_STORAGE_SERVERS = 'Redis access url, either single server or cluster server'
REDIS_STORAGE_DB = 'Redis database idx, only single server can activity'
REDIS_STORAGE_PASSWORD = 'Redis database password, only single server can activity'
REDIS_STORAGE_IGNORE_ERRORS = 'ignore error, default false'
```