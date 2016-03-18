# Flask-Azure-Storage [![PyPI version](https://badge.fury.io/py/Flask-Azure-Storage.png)](https://badge.fury.io/py/Flask-Azure-Storage)

A Flask extension that provides integration with Azure Storage

## Install

```
pip install Flask-Azure-Storage
```

## Usage

Set the account credentials in your [app.config](http://flask.pocoo.org/docs/0.10/config/):
```
AZURE_STORAGE_ACCOUNT_NAME = "your-account-name"
AZURE_STORAGE_ACCOUNT_KEY = "your-account-key"
```

Initialize the extension:
```
from flask import Flask
from flask.ext.azure_storage import FlaskAzureStorage

app = Flask(__name__)
azure_storage = FlaskAzureStorage(app)
```

Or, if you follow the [Flask application factory pattern](http://flask.pocoo.org/docs/0.10/patterns/appfactories/):
```
from flask import Flask
from flask.ext.azure_storage import FlaskAzureStorage

azure_storage = FlaskAzureStorage()

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    # initialize azure storage on the app within create_app()
    azure_storage.init_app(app)
```

From the `azure_storage` object you can now access any of the following classes:

| Attribute 						| Class 													|
| --------------------------------- | --------------------------------------------------------- |
| azure_storage.account 			| azure.storage.cloudstorageaccount.CloudStorageAccount 	|
| azure_storage.block_blob_service 	| azure.storage.blob.blockblobservice.BlockBlobService 		|
| azure_storage.page_blob_service 	| azure.storage.blob.pageblobservice.PageBlobService 		|
| azure_storage.append_blob_service | azure.storage.blob.appendblobservice.AppendBlobService 	|
| azure_storage.queue_service 		| azure.storage.queue.queueservice.QueueService 			|
| azure_storage.table_service 		| azure.storage.table.tableservice.TableService 			|
| azure_storage.file_service 		| azure.storage.file.fileservice.FileService 				|


## Examples

#### Create container
`azure_storage.block_blob_service.create_container('container-name')`

#### Delete container
`azure_storage.block_blob_service.delete_container('container-name'`

#### Upload a file
```
from azure.storage.blob import ContentSettings
azure_storage.block_blob_service.create_blob_from_path(container_name='container-name', blob_name='uploaded-file-name', file_path='/path/to/your/file.png', content_settings=ContentSettings(content_type='image'))
```

#### Delete a file
```
azure_storage.block_blob_service.delete_blob('container-name', 'uploaded-file-name')
```

#### Check if file exists
```
azure_storage.block_blob_service.exists('container-name', 'uploaded-file-name')
```

## Read more
There are plenty more things you can do. For more examples, [check out the Azure Storage SDK for Python samples](https://github.com/Azure/azure-storage-python/tree/cb51c567c5bdc1192482c7fc96cc89dad4879a29/samples)
