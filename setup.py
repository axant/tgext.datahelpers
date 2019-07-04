from setuptools import setup, find_packages
import os

version = '0.2.1'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

PIL_DEPENDENCY = []
try:
    import PIL
except:
    try:
        import Image
    except ImportError:
        PIL_DEPENDENCY = ['pillow']

testpkgs = [
    'sqlalchemy',
    'ming',
    'nose',
]
        
setup(name='tgext.datahelpers',
      version=version,
      description="Helpers to manage data and attachments on TurboGears",
      long_description=README,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: TurboGears"
        ],
      keywords='turbogears2.extension',
      author='Alessandro Molina',
      author_email='alessandro.molina@axant.it',
      url='https://github.com/axant/tgext.datahelpers',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['tgext'],
      include_package_data=True,
      package_data = {'':['*.html', '*.js', '*.css', '*.png', '*.gif']},
      zip_safe=False,
      install_requires=[
          "TurboGears2 >= 2.1",
          "formencode",
          "beaker",
          "future",
      ] + PIL_DEPENDENCY,
      extras_require={
        'testing': testpkgs,
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
