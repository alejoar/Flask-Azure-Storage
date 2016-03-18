from azure.storage import CloudStorageAccount
import six
from collections import defaultdict
import logging
import os
import re

logger = logging.getLogger('flask_s3')

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def _bp_static_url(blueprint):
    """ builds the absolute url path for a blueprint's static folder """
    u = six.u('%s%s' % (blueprint.url_prefix or '', blueprint.static_url_path or ''))
    return u


def _gather_files(app, hidden, filepath_filter_regex=None):
    """ Gets all files in static folders and returns in dict."""
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

            files = [os.path.join(root, x) \
                     for x in files if (
                         (hidden or x[0] != '.') and
                         # Skip this file if the filter regex is
                         # defined, and this file's path is a
                         # negative match.
                         (filepath_filter_regex == None or re.search(
                             filepath_filter_regex,
                             os.path.join(relative_folder, x))))]
            if files:
                valid_files[(static_folder, static_url_loc)].extend(files)
    return valid_files


class FlaskAzureStorage(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        app.config.setdefault('AZURE_STORAGE_ACCOUNT_NAME', None)
        app.config.setdefault('AZURE_STORAGE_ACCOUNT_KEY', None)
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

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
