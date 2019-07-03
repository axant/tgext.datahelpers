import os, cgi, tempfile
import sqlalchemy.types as types
from tgext.datahelpers.attachments import AttachedFile, AttachedImage


class Attachment(types.TypeDecorator):
    impl = types.Unicode

    def __init__(self, attachment_type=AttachedFile, *args, **kw):
        super(Attachment, self).__init__(*args, **kw)
        self.attachment_type = attachment_type

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(4096))

    def _create_attached_file(self, value):
        if isinstance(value, cgi.FieldStorage):
            filename = value.filename
            file = value.file
        elif isinstance(value, str):
            filename = 'attachment'
            file = tempfile.TemporaryFile()
            file.write(value)
            file.seek(0)
        else:
            filename = os.path.basename(value.name)
            file = value

        return self.attachment_type(file, filename)

    def process_bind_param(self, value, dialect):
        if isinstance(value, cgi.FieldStorage):
            if not bool(getattr(value, 'filename', None)):
                return None
        elif not value:
            return None

        if not isinstance(value, AttachedFile):
            value = self._create_attached_file(value)

        value.write()
        return value.encode()

    def process_result_value(self, value, dialect):
        if not value:
            return None

        return self.attachment_type.decode(value)


try:
    from sprox.sa.widgetselector import SAWidgetSelector
    from tw2.forms import FileField
    SAWidgetSelector.default_widgets.setdefault(Attachment, FileField)

    from sprox.sa.validatorselector import SAValidatorSelector
    from tw2.forms import FileValidator
    SAValidatorSelector.default_validators.setdefault(Attachment, FileValidator)
except ImportError:
    pass


