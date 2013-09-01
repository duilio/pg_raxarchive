import setuptools
import pg_raxarchive

REQUIRES = [
    'pyrax>=1.4.11'
    ]

setuptools.setup(
    name='pg_raxarchive',
    version=pg_raxarchive.__version__,
    author=pg_raxarchive.__author__,
    description=pg_raxarchive.__doc__.splitlines()[0].strip(),
    url='https://github.com/duilio/pg_raxarchive',

    packages=['pg_raxarchive'],
    install_requires=REQUIRES,

    entry_points={
        'console_scripts': [
            'pg_raxarchive = pg_raxarchive:main'
            ],
        }
)
