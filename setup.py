from spotifySync import VERSION
from setuptools import setup, find_packages
setup(
    name = 'spotifySync',
    version=VERSION,
    license = "Apache2",
    description = "Sync Spotify Account.",

    author = 'YaronH',
    author_email = "yaronhuang@foxmail.com",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires=["aigpy", "spotipy"],
    entry_points={'console_scripts': ['spotifySync = spotifySync:main', ]}
)
