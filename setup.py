from setuptools import setup, find_packages
setup(
    name = 'tidal-dl',
    version = "2021.6.9",
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
