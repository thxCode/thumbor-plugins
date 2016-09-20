# Version
0.0.1

# Plugins
## Loader
`thumbor_thxcode.plugins.smart_loader` use for support smart loader more.
## Storage
`thumbor_thxcode.plugins.mongo_upload_storage` use for support MongoDB Cluster access.

# Configuration
if U use _MongoDB_ (only support MongoDB now), add follow lines:
```
MONGODB_STORAGE_SERVERS 	= 'MongoDB access url, either single server or cluster server'
MONGODB_STORAGE_DB 			= 'MongoDB database name'
```