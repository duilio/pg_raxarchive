import setuptools
import pg_raxarchive

REQUIRES = [
    'pyrax>=1.4.11'
    ]

setuptools.setup(
    name='pg_raxarchive',
    version=pg_raxarchive.__version__,
    author=pg_raxarchive.__author__,
    author_email='maurizio@skicelab.com',
    description=pg_raxarchive.__doc__.splitlines()[0].strip(),
    long_description='\n'.join(pg_raxarchive.__doc__.splitlines()[1:]).strip(),
    url='https://github.com/duilio/pg_raxarchive',
    license='BSD',

    packages=['pg_raxarchive'],
    install_requires=REQUIRES,

    entry_points={
        'console_scripts': [
            'pg_raxarchive = pg_raxarchive:main'
            ],
        },

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules'],
)
