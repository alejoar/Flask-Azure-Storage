# Flask-Azure-Storage [![PyPI version](https://badge.fury.io/py/Flask-Azure-Storage.png)](https://badge.fury.io/py/Flask-Azure-Storage)

A Flask extension that provides integration with Azure Storage

**Table of Contents**

- [Flask-Azure-Storage ](#flask-azure-storage-)
	- [Install](#install)
	- [Usage](#usage)
	- [Examples](#examples)
			- [Create container](#create-container)
			- [Delete container](#delete-container)
			- [Upload a file](#upload-a-file)
			- [Delete a file](#delete-a-file)
			- [Check if file exists](#check-if-file-exists)
	- [More examples](#more-examples)
	- [Seamless integration with Flask's static assets ('static' folder)](#seamless-integration-with-flasks-static-assets-static-folder)

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
`azure_storage.block_blob_service.delete_container('container-name')`

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

## More examples
There are plenty more things you can do. For more examples, [check out the Azure Storage SDK for Python samples](https://github.com/Azure/azure-storage-python/tree/cb51c567c5bdc1192482c7fc96cc89dad4879a29/samples)

## Seamless integration with Flask's static assets ('static' folder)
Automatically upload the static assets associated with a Flask application to Azure Storage.

You don't need to manually change your `url_for` calls, Flask-Azure-Storage will automatically target Azure where you call `url_for('static', ...)` in your Jinja themes.

This feature is based on [flask-s3](https://github.com/e-dard/flask-s3), intending to implement similar functionality based on the Azure Storage service. It is still under development so please report any issues.

To upload all your static files first set the following parameters in the app.config:
```
AZURE_STORAGE_ACCOUNT_NAME = "your-account-name"
AZURE_STORAGE_ACCOUNT_KEY = "your-account-key"
AZURE_STORAGE_CONTAINER_NAME = "your-container-name"  # make sure the container is created. Refer to the previous examples or to the Azure admin panel
AZURE_STORAGE_DOMAIN = 'your-account-base-domain'
```

Then you can call the method `create_all` from the python interpreter:
```
>>> from flask import current_app
>>> from flask.ext.azure_storage import create_all
>>> create_all(current_app)
```

Or, a better choice (if you use something like FLask-Script):
```
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

@manager.command
def deploy_azure():
    from flask.ext.azure_storage import create_all
    create_all(app)
```

So now it is possible to simply call `python manage.py deploy_azure` to upload your assets.
