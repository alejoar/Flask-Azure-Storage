from azure.storage import CloudStorageAccount
import six
from collections import defaultdict
import logging
import os
import re
from flask import current_app
from flask import url_for as flask_url_for

logger = logging.getLogger('Flask_Azure_Storage')

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def url_for(endpoint, **values):
    app = current_app
    if app.config.get('TESTING', False):
        return flask_url_for(endpoint, **values)
    if 'AZURE_STORAGE_CONTAINER_NAME' not in app.config:
        raise ValueError("AZURE_STORAGE_CONTAINER_NAME not found in app configuration.")

    if endpoint == 'static' or endpoint.endswith('.static'):
        scheme = 'https'
        if not app.config.get("AZURE_STORAGE_USE_HTTPS", True):
            scheme = 'http'
        # allow per url override for scheme
        scheme = values.pop('_scheme', scheme)
        # manage other special values, all have no meaning for static urls
        values.pop('_external', False)  # external has no meaning here
        values.pop('_anchor', None)  # anchor as well
        values.pop('_method', None)  # method too

        url_format = '%(container_domain)s/%(container_name)s/%(virtual_folder)s'

        bucket_path = url_format % {
            'container_domain': app.config['AZURE_STORAGE_DOMAIN'],
            'container_name': app.config['AZURE_STORAGE_CONTAINER_NAME'],
            'virtual_folder': app.config['AZURE_STORAGE_VIRTUAL_FOLDER_NAME']
        }
        urls = app.url_map.bind(bucket_path, url_scheme=scheme)
        return urls.build(endpoint, values=values, force_external=True)
    return flask_url_for(endpoint, **values)


def _path_to_relative_url(path):
    return os.path.splitdrive(path)[1].replace('\\', '/')


def _static_folder_path(static_url, static_folder, static_asset, app):
    # first get the asset path relative to the static folder.
    # static_asset is not simply a filename because it could be
    # sub-directory then file etc.
    if not static_asset.startswith(static_folder):
        raise ValueError("%s static asset must be under %s static folder" %
                         (static_asset, static_folder))
    rel_asset = static_asset[len(static_folder):]
    # Now bolt the static url path and the relative asset location together
    path = '%s/%s' % (static_url.rstrip('/'), rel_asset.lstrip('/'))
    # Skip static folder name
    # return path.split(static_folder.split('/')[-1])[1]
    return path


def _write_files(blob_service, app, static_url_loc, static_folder, files,
                 container_name):
    import mimetypes
    import hashlib
    from azure.storage.blob import ContentSettings
    static_folder_rel = _path_to_relative_url(static_folder)
    for file_path in files:
        asset_loc = _path_to_relative_url(file_path)
        full_key_name = _static_folder_path(static_url_loc, static_folder_rel,
                                            asset_loc, app)

        key_name = full_key_name.lstrip("/")
        virtual_folder_name = app.config.get('AZURE_STORAGE_VIRTUAL_FOLDER_NAME')
        if virtual_folder_name:
            key_name = virtual_folder_name.rstrip('/').lstrip('/') + '/' + key_name

        hasher = hashlib.sha1()
        with open(file_path, 'rb') as file:
            buf = file.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(65536)
        file.close()
        hash = hasher.hexdigest()
        try:
            if blob_service._get_blob(container_name, key_name).\
                    metadata.get('hash') == hash:
                # skip file..
                continue
        except:
            pass
        # upload..
        blob_service.create_blob_from_path(
            container_name,
            key_name,
            file_path,
            content_settings=ContentSettings(
                content_type=mimetypes.MimeTypes().guess_type(key_name)[0]),
            metadata={'hash': hash})


def _bp_static_url(blueprint):
    u = six.u('%s%s' % (blueprint.url_prefix or '', blueprint.static_url_path or ''))
    return u


def _gather_files(app, hidden):
    dirs = [(six.u(app.static_folder), app.static_url_path)]
    if hasattr(app, 'blueprints'):
        blueprints = app.blueprints.values()
        bp_details = lambda x: (x.static_folder, _bp_static_url(x))
        dirs.extend([bp_details(x) for x in blueprints if x.static_folder])

    valid_files = defaultdict(list)
    for static_folder, static_url_loc in dirs:
        if not os.path.isdir(static_folder):
            logger.warning("WARNING - [%s does not exist]" % static_folder)
        else:
            logger.debug("Checking static folder: %s" % static_folder)
        for root, _, files in os.walk(static_folder):
            relative_folder = re.sub(r'^\/',
                                     '',
                                     root.replace(static_folder, ''))

            files = [os.path.join(root, x)
                     for x in files if (hidden or x[0] != '.')]
            if files:
                valid_files[(static_folder, static_url_loc)].extend(files)
    return valid_files


def create_all(app, account_name=None, account_key=None, container_name=None,
               include_hidden=False):
    account_name = account_name or app.config.get('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = account_key or app.config.get('AZURE_STORAGE_ACCOUNT_KEY')
    container_name = container_name or app.config.get('AZURE_STORAGE_CONTAINER_NAME')
    if not container_name:
        raise ValueError("No container name provided.")

    # build list of static files
    all_files = _gather_files(app, include_hidden)
    logger.debug("All valid files: %s" % all_files)

    # connect to azure
    azure = CloudStorageAccount(
            account_name=account_name,
            account_key=account_key
            )

    # create blob service
    blob_service = azure.create_block_blob_service()

    # get_or_create container
    if not blob_service.exists(container_name):
        blob_service.create_container(container_name)

    prefix = app.config.get('AZURE_STORAGE_PREFIX', '').lstrip('/').rstrip('/')
    for (static_folder, static_url), names in six.iteritems(all_files):
        static_upload_url = '%s/%s' % (prefix.rstrip('/'), static_url.lstrip('/'))
        _write_files(blob_service, app, static_upload_url, static_folder,
                     names, container_name)


class FlaskAzureStorage(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        app.config.setdefault('AZURE_STORAGE_ACCOUNT_NAME', None)
        app.config.setdefault('AZURE_STORAGE_ACCOUNT_KEY', None)
        app.config.setdefault('AZURE_STORAGE_CONTAINER_NAME', '')
        app.config.setdefault('AZURE_STORAGE_DOMAIN', '')
        app.config.setdefault('AZURE_STORAGE_VIRTUAL_FOLDER_NAME', '')

        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        if app.debug:
            app.config['AZURE_STORAGE_ACTIVE'] = False
        else:
            app.config['AZURE_STORAGE_ACTIVE'] = True

        if app.config['AZURE_STORAGE_ACTIVE']:
            app.jinja_env.globals['url_for'] = url_for

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'azure_storage_account'):
            ctx.azure_storage_account = None
        if hasattr(ctx, 'azure_block_blob_service'):
            ctx.azure_block_blob_service = None
        if hasattr(ctx, 'azure_page_blob_service'):
            ctx.azure_page_blob_service = None
        if hasattr(ctx, 'azure_append_blob_service'):
            ctx.azure_append_blob_service = None
        if hasattr(ctx, 'azure_queue_service'):
            ctx.azure_queue_service = None
        if hasattr(ctx, 'azure_table_service'):
            ctx.azure_table_service = None
        if hasattr(ctx, 'azure_file_service'):
            ctx.azure_file_service = None

    @property
    def account(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_storage_account'):
                ctx.azure_storage_account = CloudStorageAccount(
                    account_name=ctx.app.config.get('AZURE_STORAGE_ACCOUNT_NAME'),
                    account_key=ctx.app.config.get('AZURE_STORAGE_ACCOUNT_KEY')
                    )
            return ctx.azure_storage_account

    @property
    def block_blob_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_block_blob_service'):
                ctx.azure_block_blob_service = self.account.create_block_blob_service()
            return ctx.azure_block_blob_service

    @property
    def page_blob_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_page_blob_service'):
                ctx.azure_page_blob_service = self.account.create_page_blob_service()
            return ctx.azure_page_blob_service

    @property
    def append_blob_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_append_blob_service'):
                ctx.azure_append_blob_service = self.account.create_append_blob_service()
            return ctx.azure_append_blob_service

    @property
    def queue_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_queue_service'):
                ctx.azure_queue_service = self.account.create_queue_service()
            return ctx.azure_queue_service

    @property
    def table_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_table_service'):
                ctx.azure_table_service = self.account.create_table_service()
            return ctx.azure_table_service

    @property
    def file_service(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'azure_file_service'):
                ctx.azure_file_service = self.account.create_file_service()
            return ctx.azure_file_service
