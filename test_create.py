import pytest
import create
import datetime
from unittest.mock import MagicMock

def test_is_on_season_unwrapped():
    start_date = datetime.datetime(year = 2023, month = 4, day = 5)
    end_date = datetime.datetime(year = 2023, month = 3, day = 26)
    song_date = datetime.datetime(year = 2019, month = 3, day = 15)
    
    assert create.is_on_season(song_date, start_date, end_date) == True
    
    song_date = datetime.datetime(year = 2019, month = 9  , day = 15)
    
    assert create.is_on_season(song_date, start_date, end_date) == False
    
def test_is_on_season_wrapped():
    start_date = datetime.datetime(year = 2023, month = 12, day = 12)
    end_date = datetime.datetime(year = 2023, month = 2, day = 10)
    song_date = datetime.datetime(year = 2019, month = 1, day = 15)
    
    assert create.is_on_season(song_date, start_date, end_date) == True
    
    song_date = datetime.datetime(year = 2019, month = 11, day = 15)
    assert create.is_on_season(song_date, start_date, end_date) == False
    
    
def test_all_playlist_songs_are_analyzed():
    sp = MagicMock()
    sp.playlist_items.side_effect = [
        {"items" : [1]*20},
        {"items" : [1]*20},
        {"items" : [1]*10},
    ]
    create.get_all_tracks_gracefully(sp, "id", "name", None, False) #pylint: disable=too-many-function-args
    sp.playlist_items.assert_called_with("id", offset = 40, limit=20)
    assert len(sp.playlist_items.mock_calls) == 3
