import tg, os, shutil, cgi, json, tempfile
import uuid as uuid_m
from tg.decorators import cached_property
from .utils import MarkupString

try:
    from PIL import Image
except ImportError:
    import Image


class AttachedFile(object):
    def __init__(self, file, filename, uuid=None):
        self.uuid = uuid
        if not uuid:
            self.uuid = str(uuid_m.uuid1())

        self._file = file

        self.filename = unicode(filename)
        self.url = '/'.join([self.attachments_url, self.uuid, self.filename])
        self.local_path = os.path.join(self.attachment_dir, self.filename)

    @cached_property
    def file(self):
        if isinstance(self._file, basestring):
            self._file = open(self._file)
        return self._file

    @cached_property
    def attachments_url(self):
        return tg.config.get('attachments_url', '/attachments')

    @cached_property
    def attachment_dir(self):
        attachments_path = tg.config.get('attachments_path')
        if not attachments_path:
            attachments_path = os.path.join(tg.config['here'], tg.config['package'].__name__.lower(),
                                            'public', 'attachments')
        attachment_dir = os.path.join(attachments_path, self.uuid)
        return unicode(attachment_dir)

    def write(self):
        try:
            os.mkdir(self.attachment_dir)
        except Exception, e:
            pass

        if getattr(self.file, 'name', None) != self.local_path:
            shutil.copyfileobj(self.file, open(self.local_path, 'w+'))
            self.file.seek(0)

    def unlink(self):
        shutil.rmtree(self.attachment_dir)

    def encode(self):
        return unicode(json.dumps({'file':self.local_path, 'filename':self.filename, 'uuid':self.uuid}))

    @classmethod
    def decode(cls, value):
        params = {}
        for key, value in json.loads(value).iteritems():
            params[str(key)] = value
        return cls(**params)


class AttachedImage(AttachedFile):
    thumbnail_size = (128, 128)
    thumbnail_format = 'png'

    def __unicode__(self):
         # This is an huge hack, should find a better way to provide HTML for the image
        try:
            url = tg.url(self.thumb_url)
        except:
            url = self.thumb_url

        return MarkupString('<img src="%s"/>' % url)

    def __init__(self, file, filename, uuid=None):
        super(AttachedImage, self).__init__(file, filename, uuid)
        
        thumb_filename = 'thumb.'+self.thumbnail_format.lower()
        self.thumb_local_path = os.path.join(self.attachment_dir, thumb_filename)
        self.thumb_url = '/'.join([self.attachments_url, self.uuid, thumb_filename])

    def write(self):
        super(AttachedImage, self).write()

        if getattr(self.file, 'name', None) != self.local_path:
            self.file.seek(0)
            thumbnail = Image.open(self.file)
            thumbnail.thumbnail(self.thumbnail_size, Image.BILINEAR)
            thumbnail = thumbnail.convert('RGBA')
            thumbnail.format = self.thumbnail_format
            thumbnail.save(self.thumb_local_path)
