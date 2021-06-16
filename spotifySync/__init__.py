#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :  __init__.py
@Date    :  2021/05/08
@Author  :  Yaronzz
@Version :  1.0
@Contact :  yaronhuang@foxmail.com
@Desc    :  
'''
import os
import sys
import json
import aigpy
import prettytable
import webbrowser
import logging

from aigpy.progressHelper import ProgressTool
from aigpy.modelHelper import ModelBase
from aigpy.musicHelp import User, Album, Artist, Track, Playlist, Show
from spotipy import SpotifyOAuth, SpotifyStateError, Spotify

LOG = """
   ____          __  _ ___     ____             
  / __/__  ___  / /_(_) _/_ __/ __/_ _____  ____
 _\ \/ _ \/ _ \/ __/ / _/ // /\ \/ // / _ \/ __/
/___/ .__/\___/\__/_/_/ \_, /___/\_, /_//_/\__/ 
   /_/                 /___/    /___/          
"""

def getSettingsPath():
    if "XDG_CONFIG_HOME" in os.environ:
        return os.environ['XDG_CONFIG_HOME']
    elif "HOME" in os.environ:
        return os.environ['HOME']
    else:
        return os.path._getfullpathname("./")

CACHEFILE = getSettingsPath() + "/.SpotifySync-Auth"
VERSION = "2021.6.16"


def enter(string):
    aigpy.cmd.colorPrint(string, aigpy.cmd.TextColor.Yellow, None)
    ret = input()
    return ret


def err(string):
    print(aigpy.cmd.red("[ERR] ") + string)
    logging.error(string)


def info(string):
    print(aigpy.cmd.blue("[INFO] ") + string)


def success(string):
    print(aigpy.cmd.green("[SUCCESS] ") + string)


def printfMenu(user: str = ""):
    print("====================================================")
    print(aigpy.cmd.yellow("Current authorize user:") + str(user) + '\n')
    tb = prettytable.PrettyTable()
    tb.field_names = ["CHOICE", "FUNCTION"]
    tb.align = 'l'
    tb.set_style(prettytable.PLAIN_COLUMNS)
    tb.add_row([aigpy.cmd.green("Login    " + " '0':"), "login by your spotify account"])
    tb.add_row([aigpy.cmd.green("Authorize" + " '1':"), "Authorize to modify playlist"])
    tb.add_row([aigpy.cmd.green("Save     " + " '2':"), "Save data to local"])
    tb.add_row([aigpy.cmd.green("Upload   " + " '3':"), "Upload local data to your account"])
    print(tb)
    print("====================================================")


class LocalData(ModelBase):
    albums = Album()
    artists = Artist()
    tracks = Track()
    playlists = Playlist()
    shows = Show()

    def save(self, path="./.localData.json"):
        try:
            ret = aigpy.model.modelToDict(self)
            content = json.dumps(ret)
            aigpy.file.write(path, content, 'w+')
        except Exception as e:
            err("Save data failed." + str(e))

    def read(self, path="./.localData.json"):
        try:
            content = aigpy.file.getContent(path)
            if content != '':
                ret = json.loads(content)
                array = aigpy.model.dictToModel(ret, LocalData())
                self.albums = array.albums
                self.tracks = array.tracks
                self.playlists = array.playlists
                self.artists = array.artists
                self.shows = array.shows
        except Exception as e:
            err("Read data failed." + str(e))

        if not isinstance(self.albums, list):
            self.albums = []
        if not isinstance(self.tracks, list):
            self.tracks = []
        if not isinstance(self.playlists, list):
            self.playlists = []
        if not isinstance(self.artists, list):
            self.artists = []
        if not isinstance(self.shows, list):
            self.shows = []

    def __appendBases__(self, selfItems, appendItems):
        array = []
        keys = dict()
        if isinstance(selfItems, list):
            for item in selfItems:
                keys[item.id] = item
        else:
            selfItems = []

        for item in appendItems:
            if item.id in keys:
                continue
            array.append(item)
            keys[item.id] = item
        return array

    def appendTracks(self, appendItems):
        items = self.__appendBases__(self.tracks, appendItems)
        if len(items) > 0:
            self.tracks += items

    def appendAlbums(self, appendItems):
        items = self.__appendBases__(self.albums, appendItems)
        if len(items) > 0:
            self.albums += items

    def appendArtists(self, appendItems):
        items = self.__appendBases__(self.artists, appendItems)
        if len(items) > 0:
            self.artists += items

    def appendShows(self, appendItems):
        items = self.__appendBases__(self.shows, appendItems)
        if len(items) > 0:
            self.shows += items

    def appendPlaylists(self, appendItems):
        keys = dict()
        if isinstance(self.playlists, list):
            for item in self.playlists:
                if not item.isOwn:
                    keys[item.id] = item
                else:
                    keys[item.name] = item
        else:
            self.playlists = []

        for item in appendItems:
            if not item.isOwn:
                if item.id in keys:
                    continue
                else:
                    self.playlists.append(item)
                    keys[item.id] = item
            else:
                if item.name not in keys:
                    self.playlists.append(item)
                    keys[item.name] = item
                else:
                    array = self.__appendBases__(keys[item.name].tracks, item.tracks)
                    keys[item.name].tracks += array


class MySpotify(object):
    def __init__(self, username):
        try:
            auth = SpotifyOAuth(username=username,
                                scope="user-modify-playback-state user-library-modify user-library-read playlist-modify-public playlist-modify-private playlist-read-private user-follow-modify user-follow-read user-read-private",
                                client_id="ddcfe87f7ded4cec843769b882905d89",
                                client_secret="9896b8f8de5e4a26a599def1986749d4",
                                redirect_uri='https://yaronzz.top/',
                                open_browser=True,
                                cache_path=CACHEFILE)
            self.spotify = Spotify(auth_manager=auth)
            self.user = self.__user__()
            self.isLogin = True
        except Exception as e:
            print(aigpy.cmd.red("Err: ") + str(e))
            self.isLogin = False

            

    def __user__(self) -> User:
        result = self.spotify.current_user()
        obj = User()
        obj.id = result['id']
        obj.name = result['display_name']
        return obj

    def __getItems__(self, type: str, id: str = '') -> list:
        offset = 0
        limit = 50
        array = []
        while True:
            if type == "playlist_items":
                result = self.spotify.playlist_items(id, limit=limit, offset=offset)
            elif type == "current_user_playlists":
                result = self.spotify.current_user_playlists(limit, offset)
            elif type == "current_user_saved_tracks":
                result = self.spotify.current_user_saved_tracks(limit, offset)
            elif type == "current_user_saved_albums":
                result = self.spotify.current_user_saved_albums(limit, offset)
            elif type == "current_user_saved_shows":
                result = self.spotify.current_user_saved_shows(limit, offset)

            items = result['items']
            for item in items:
                if type == "playlist_items" or type == "current_user_saved_tracks":
                    obj = Track()
                    obj.id = item['track']['id']
                    obj.name = item['track']['name']
                elif type == "current_user_playlists":
                    obj = Playlist()
                    obj.id = item['id']
                    obj.name = item['name']
                    obj.isOwn = True if item['owner']['id'] == self.user.id else False
                    obj.tracks = []
                elif type == "current_user_saved_albums":
                    obj = Album()
                    obj.id = item['album']['id']
                    obj.name = item['album']['name']
                elif type == "current_user_saved_shows":
                    obj = Show()
                    obj.id = item['show']['id']
                    obj.name = item['show']['name']
                array.append(obj)

            size = len(items)
            if size < limit:
                break
            offset += limit
        return array

    def __getPlaylistTracks__(self, id: str) -> list:
        return self.__getItems__("playlist_items", id)

    def getUserPlaylists(self, includeTracks: bool = True) -> list:
        array = self.__getItems__("current_user_playlists")
        if includeTracks:
            for item in array:
                item.tracks = self.__getPlaylistTracks__(item.id)
        return array

    def getUserSavedTracks(self) -> list:
        return self.__getItems__("current_user_saved_tracks")

    def getUserSavedAlbums(self) -> list:
        return self.__getItems__("current_user_saved_albums")

    def getUserSavedShows(self) -> list:
        return self.__getItems__("current_user_saved_shows")

    def getUserFollowArtists(self) -> list:
        lastId = None
        limit = 10
        array = []
        while True:
            result = self.spotify.current_user_followed_artists(limit, lastId)
            items = result['artists']['items']
            for item in items:
                obj = Artist()
                obj.id = item['id']
                obj.name = item['name']
                array.append(obj)

            size = len(items)
            if size < limit:
                break
            lastId = items[len(items) - 1]['id']
        return array

    def __splitGroups__(self, array):
        idGroup = []
        ids = []
        for item in array:
            ids.append(item)
            if len(ids) >= 10:
                idGroup.append(ids)
                ids = []
        if len(ids) > 0:
            idGroup.append(ids)
        return idGroup

    def __getAppendIDGroups__(self, selfItems, appendItems):
        array = []
        keys = dict()
        if isinstance(selfItems, list):
            for item in selfItems:
                keys[item.id] = item
            else:
                selfItems = []

        for item in appendItems:
            if item.id in keys:
                continue
            array.append(item.id)
            keys[item.id] = item
        
        return self.__splitGroups__(array)

    def SyncFollowArtists(self, artists):
        selfItems = self.getUserFollowArtists()
        idGroup = self.__getAppendIDGroups__(selfItems, artists)
        for item in idGroup:
            self.spotify.user_follow_artists(item)

    def SyncSavedAlbums(self, albums):
        selfItems = self.getUserSavedAlbums()
        idGroup = self.__getAppendIDGroups__(selfItems, albums)
        for item in idGroup:
            self.spotify.current_user_saved_albums_add(item)

    def SyncSaveShows(self, shows):
        selfItems = self.getUserSavedShows()
        idGroup = self.__getAppendIDGroups__(selfItems, shows)
        for item in idGroup:
            self.spotify.current_user_saved_shows_add(item)

    def SyncSaveTracks(self, tracks):
        selfItems = self.getUserSavedTracks()
        idGroup = self.__getAppendIDGroups__(selfItems, tracks)
        for item in idGroup:
            self.spotify.current_user_saved_tracks_add(item)

    def SyncPlaylists(self, plists):
        selfItems = self.getUserPlaylists(True)
        keys = dict()
        for item in selfItems:
            if not item.isOwn:
                continue
            keys[item.name] = item

        for item in plists:
            if not item.isOwn:
                self.spotify.current_user_follow_playlist(item.id)
                continue
            
            plId = None
            tracks = []
            if item.name in keys:
                plId = keys[item.name].id
                tracks = keys[item.name].tracks
            else:
                result = self.spotify.user_playlist_create(self.user.id, item.name)
                plId = result['id']
            
            idGroup = self.__getAppendIDGroups__(tracks, item.tracks)
            for ids in idGroup:
                self.spotify.user_playlist_add_tracks(self.user.id, plId, ids)


def saveLocal(account: MySpotify, data: LocalData):
    if account is None:
        aigpy.cmd.colorPrint("Err: No account authorize\n", aigpy.cmd.TextColor.Red, None)
        return
    progress = ProgressTool(6)
    progress.addCurCount(1)

    tracks = account.getUserSavedTracks()
    data.appendTracks(tracks)
    progress.addCurCount(1)

    shows = account.getUserSavedShows()
    data.appendShows(shows)
    progress.addCurCount(1)

    albums = account.getUserSavedAlbums()
    data.appendAlbums(albums)
    progress.addCurCount(1)

    artists = account.getUserFollowArtists()
    data.appendArtists(artists)
    progress.addCurCount(1)

    plists = account.getUserPlaylists()
    data.appendPlaylists(plists)
    progress.addCurCount(1)

    data.save()


def UploadAccount(account: MySpotify, data: LocalData):
    if account is None:
        aigpy.cmd.colorPrint("Err: No account authorize\n", aigpy.cmd.TextColor.Red, None)
        return
    
    progress = ProgressTool(6, desc="UploadAccount")
    progress.addCurCount(1)

    account.SyncSaveTracks(data.tracks)
    progress.addCurCount(1)

    account.SyncSaveShows(data.shows)
    progress.addCurCount(1)

    account.SyncSavedAlbums(data.albums)
    progress.addCurCount(1)

    account.SyncFollowArtists(data.artists)
    progress.addCurCount(1)

    account.SyncPlaylists(data.playlists)
    progress.addCurCount(1)


def main():
    print(LOG)
    print("                " + VERSION)

    data = LocalData()
    data.read()

    account = None
    newAccount = MySpotify('test')
    if newAccount.isLogin:
        account = newAccount

    while True:
        printfMenu(None if account is None else account.user.name)
        choice = enter("Choice:")
        if choice == '0':
            webbrowser.open("https://accounts.spotify.com/")
        elif choice == '1':
            aigpy.path.remove(CACHEFILE)
            newAccount = MySpotify('test')
            if newAccount.isLogin:
                account = newAccount
        elif choice == '2':
            saveLocal(account, data)
        elif choice == '3':
            UploadAccount(account, data)

if __name__ == "__main__":
    main()
