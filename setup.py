from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='pyarmor-webui',
    version='0.1.0',
    description='A webui for pyarmor to obfuscate python scripts.',
    long_description=long_description,
    license_file='LICENSE',
    url='https://github.com/dashingsoft/pyarmor-webui',
    author='Jondy Zhao',
    author_email='jondy.zhao@gmail.com',

    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Utilities',
        'Topic :: Security',
        'Topic :: System :: Software Distribution',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Support platforms
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],

    packages=['pyarmor.webui'],
    package_dir={'pyarmor.webui': '.'},
    package_data={
        'pyarmor.webui': ['README.rst', 'LICENSE',
                          'static/index.html', 'static/*.js', 'static/*.ico',
                          'static/css/*.css', 'static/js/*.js',
                          'static/fonts/element-*', 'static/img/*.svg'],
    },

    entry_points={
        'console_scripts': [
            'pyarmor-webui=pyarmor.webui.server:main',
        ],
    },

    install_requires=['pyarmor>=5.9'],
)
