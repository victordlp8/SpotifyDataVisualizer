import json
import os
from datetime import datetime, timedelta

import attr
import pandas as pd
from tqdm import tqdm


@attr.s
class Paths():
    data = r'data'


@attr.s
class Song():
    date = attr.ib(default=str | datetime)
    duration = attr.ib(default=float)
    artist = attr.ib(default=str)
    name = attr.ib(default=str)


def main():
    DATE_FORMAT = 'Week %W of %Y'
    paths = Paths()

    if os.path.exists(paths.data):
        fileList = [f for f in os.listdir(
            paths.data) if os.path.isfile(os.path.join(paths.data, f))]
        if len(fileList) == 0:
            print('[ERROR] Unable to find StreamingHistory nor endsong files.')
            exit()
    else:
        print('[ERROR] Please make sure the directory \'data\' exists.')
        exit()

    songs: list[dict | Song] = []
    for file in fileList:
        if file.find('StreamingHistory') != -1 or file.find('endsong') != -1:
            with open(os.path.join(paths.data, file), 'r', encoding='utf-8') as file:
                songs += json.load(file)
    del file

    for i, song in enumerate(tqdm(songs, desc='Reading data', unit='song')):
        try:
            song = Song(
                date=datetime.strptime(song['endTime'], '%Y-%m-%d %H:%M'),
                duration=song['msPlayed']/1000/60,
                artist=song['artistName'],
                name=song['artistName'] + ' | ' + song['trackName']
            )
        except KeyError:
            try:
                song = Song(
                    date=datetime.strptime(song['ts'], '%Y-%m-%dT%H:%M:%SZ'),
                    duration=song['ms_played']/1000/60,
                    artist=song['master_metadata_album_artist_name'],
                    name=song['master_metadata_album_artist_name'] +
                    ' | ' + song['master_metadata_track_name']
                )
            except TypeError:
                try:
                    song = Song(
                        date=datetime.strptime(song['ts'], '%Y-%m-%dT%H:%M:%SZ'),
                        duration=song['ms_played']/1000/60,
                        artist=song['episode_show_name'],
                        name=song['episode_show_name'] +
                        ' | ' + song['episode_name']
                    )
                except TypeError:
                    song = Song(
                        date=datetime.strptime(song['ts'], '%Y-%m-%dT%H:%M:%SZ'),
                        duration=song['ms_played']/1000/60,
                        artist=song['episode_name'],
                        name=song['episode_name']
                    )

        songs[i] = song

    songs = sorted(songs, key=lambda song: song.date)

    timeCounter = {}
    dates: list[datetime] = []
    songsData, artistsData = {}, {}
    for song in tqdm(songs, desc='Analyzing data', unit='song'):
        song.date = datetime.strptime(
            song.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
        dates.append(song.date)

        song.date = song.date.strftime(DATE_FORMAT)

        if song.artist in artistsData:
            timeCounter[song.artist] += song.duration
            artistsData[song.artist][song.date] = timeCounter[song.artist]
        else:
            timeCounter[song.artist] = song.duration
            artistsData[song.artist] = {
                song.date: timeCounter[song.artist]}

        if song.name in songsData:
            timeCounter[song.name] += song.duration
            songsData[song.name][song.date] = timeCounter[song.name]
        else:
            timeCounter[song.name] = song.duration
            songsData[song.name] = {
                song.date: timeCounter[song.name]}

    dates = list(set(dates))
    dates = sorted(dates)

    copy_dates = [dates[0]]
    while copy_dates[-1] <= dates[-1]:
        copy_dates.append(copy_dates[-1] + timedelta(days=1))
    dates = copy_dates
    del copy_dates

    dates = [col.strftime(DATE_FORMAT) for col in dates]
    dates = sorted(set(dates), key=dates.index)

    print('\nSaving songs data...')
    dt = pd.DataFrame.from_dict(songsData, orient='index', columns=dates)
    dt.to_csv('songsData.csv')

    print('\nSaving artists data...')
    dt = pd.DataFrame.from_dict(artistsData, orient='index', columns=dates)
    dt.to_csv('artistsData.csv')

    print('\nFINISHED!!!')


if __name__ == '__main__':
    main()
