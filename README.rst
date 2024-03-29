About Data Helpers
-------------------------

.. image:: https://drone.io/bitbucket.org/axant/tgext.datahelpers/status.png
    :target: https://drone.io/bitbucket.org/axant/tgext.datahelpers

tgext.datahelpers is a collection of utilities to help manage stored data
in common web applications.

tgext.datahelpers contains:

- Validators to fetch objects from database by Id (both SQLA and Ming)
- Store Attachments by just declaring a Column in your model
- Store image and thumbnails by just declaring a Column in your model

Installing
-------------------------------

tgext.datahelpers can be installed both from pypi or from bitbucket::

    easy_install tgext.datahelpers

should just work for most of the users

Validators
--------------------------------

``tgext.datahelpers.validators`` provides the ``SQLAEntityConverter`` and
``MingEntityConverter`` that convert the given
parameter (which is expected to be the primary key of an object) to
the actually object itself::

    from tgext.datahelpers.validators import SQLAEntityConverter

    @expose()
    @validate({'doc':SQLAEntityConverter(Document)}, error_handler=index)
    def photo(self, doc):
        return redirect(doc.photo.url)

Validators module provides also the ``validated_handler`` utility which
makes possible to apply validation also to error_handlers.
Normally TurboGears would execute @validate based validation only when
the controller method is called through a request, when you use a controller
method as the error_handler of another method the error_handler @validate
gets skipped and arguments are passed as they are.

Using ``validated_handler`` it is possible to change this behavior and
apply validation even to error_handlers::

    from tgext.datahelpers.validators import SQLAEntityConverter, validated_handler

    @expose()
    @validate({'doc':validators.Int(not_empty=True)},
              error_handler=index)
    def next(self, doc):
        return dict(doc=doc+1)

    @expose()
    @validate({'doc':SQLAEntityConverter(Document)},
              error_handler=validated_handler(next))
    def photo(self, doc):
        return redirect(doc.photo.url)

In the previous example when calling /photo/3 if document 3 is not available
it would be retrieved the successive document by calling next. If validated_handler
gets removed from photo @validate you would get an error as doc wouldn't be an integer.

Utilities
-----------------------------------

``tgext.datahelpers.utils`` provides the ``slugify`` function to
generate slug urls for entities which are meaningful for users.

The generated slugs includes the entity id so that it can identify
unique elements making possible for EntityConverter validators
to support retrieving objects from the generated slug. Add
``slugified=True`` option to the entity converted to load
back an entity by its slug.

Sample usage::

    >>> from tgext.datahelpers.utils import slugify

    >>> entity = DBSession.query(Entity).get(5)
    >>> url = slugify(entity, entity.name)
    >>> print url
    'this-is-a-very-long-phrase-5'

Utility functions also provide a ``fail_with`` object which
can be used with turbogears @validate error_handler to report
a missing element or forbidden access::

    from tgext.datahelpers.validators import SQLAEntityConverter
    from tgext.datahelpers.utils import fail_with

    @expose()
    @validate({'doc':SQLAEntityConverter(Document, slugified=True)},
              error_handler=fail_with(404))
    def photo(self, doc):
        return redirect(doc.photo.url)

Entities Based Caching
-----------------------------------

``tgext.datahelpers.caching`` provides the ``@entitycached`` decorator
which can be used to cache methods (and helpers) based on a parameter
which is a Ming or SQLAlchemy entity.

Whenever the entity gets updated the cache is invalidated and the method
called again, otherwise calling the method will return the value from the cache.

To determine if the entity has changed it will try to retrieve the
``cache_key`` property of the entity, if not available a cache key
will be automatically generated using the primary key and ``updated_at``
property of the entity.

Sample usage::

    from tgext.datahelpers.caching import entitycached

    @entitycached('post')
    def render_post(post):
        return '<div>%s</div>' % post.html

    blog = ''.join(map(render_post, blog_posts))

``@entitycached`` decorator can also be used to cache any function by using
the ``tgext.datahelpers.caching.CacheKey`` object as a function argument instead
of a Ming/SQLAlchemy entity.

If you want to cache an SQLAlchemy query give a look at the ``sqla_merge`` option.

``@entitycached`` decorator supports also various options:

- ``expire`` - How long the cached value will be kept around, by default 3 days
- ``cache_type`` - Which type of cache to use, by default memory will be used
- ``namespace`` - The cache namespace, by default this is autogenerated by the cached class and method names
- ``sqla_merge`` - Whenever the cached function return value is a SQLAlchemy query.
    When this option is True you will always get the results instead of the query itself and the resulting
    objects will be merged back in to the currently existing TurboGears DBSession to avoid
    ``DetachedInstanceError`` exceptions.

Attachments
-----------------------------------

``tgext.datahelpers.fields`` provides the ``Attachment`` field for SQLAlchemy
to provide an easy and convenient way to store attachments.

The ``Attachment`` field will permit to assign files to the attribute
declared with ``Attachment`` type and will store a copy of the file on disk
as soon as the object is committed to the database.

The document field will provide a bunch of attributes you can use to
access the file:

- ``file`` - A file object pointing to the saved file
- ``filename`` - The name of the saved file
- ``url`` - Url from which the file is fetchable
- ``local_path`` - Local path of the file on disk

Files will be saved in ``tg.config['attachments_path']`` and url will be
generated using ``tg.config['attachments_url']``. By default those are set
at */public/attachments* and */attachments*.

The ``Attachment`` field accepts a *attachment_type* parameter which specifies
the kind of attachment that it is going to be saved. The default is
``tgext.datahelpers.fields.AttachedFile`` which just stores the file itself::

    from tgext.datahelpers.fields import Attachment
    class Document(DeclarativeBase):
        __tablename__ = 'document'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        file = Column(Attachment)

    d = Document(file=open('/myfile.txt'))
    DBSession.add(d)
    DBSession.flush()
    DBSession.commit()

    d = DBSession.query(Document).first()
    print d.file.url

    '/attachments/747722ca-1a07-11e1-83fc-001ff3d72e6b/myfile.txt'

Apart from file objects also instances of ``cgi.FieldStorage`` can be assigned
to permit to quickly store uploaded files.

Image Attachments with Thumbnail
--------------------------------------

Using the ``tgext.datahelpers.fields.AttachedImage`` as the argument of the
``Attachment`` field it is possible to quickly store images with their thumbnail.

The resulting object will provide the same attributes as the generic Attachment one
adding two more thumbnail related properties:

- ``thumb_local_path`` - The local path of the image thumbnail
- ``thumb_url`` - The url of the thumbnail

Storing image with thumbnails is as easy as storing the file itself::

    from tgext.datahelpers.fields import Attachment, AttachedImage
    class Document(DeclarativeBase):
        __tablename__ = 'document'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        image = Column(Attachment(AttachedImage))

    d = Document(image=open('/photo.jpg'))
    DBSession.add(d)
    DBSession.flush()
    DBSession.commit()

    d = DBSession.query(Document).first()
    print d.image.url
    '/attachments/d977144a-1a08-11e1-8131-001ff3d72e6b/aperto.tiff'
    print d.image.thumb_url
    'attachments/d977144a-1a08-11e1-8131-001ff3d72e6b/thumb.png'


Thumbnail Options
=======================================

By default thumbnails will be generated with size 128, 128 and in PNG format.
This can be changed by sublcassing the ``AttachedImage`` class and specifying
the ``thumbnail_size`` and ``thumbnail_format`` attributes::

    class BigThumbnailAttachedImage(AttachedImage):
        thumbnail_size = (320, 320)
        thumbnail_format = 'jpg'

    class Document(DeclarativeBase):
        __tablename__ = 'document'

        uid = Column(Integer, autoincrement=True, primary_key=True)
        image = Column(Attachment(BigThumbnailAttachedImage))
