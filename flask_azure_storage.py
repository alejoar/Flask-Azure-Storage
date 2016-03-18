from azure.storage import CloudStorageAccount

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


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
