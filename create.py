import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import spotipy.util as util
import argparse
import time



def make_parser():
    parser = argparse.ArgumentParser(description='Create playlist of songs from the current season')
    parser.add_argument('--range-in-days', type=int, default=300,
                        help='The day range around the current month and day  (default: 30)')
    return parser
    
    
def inrange_circ(x, l,r):
    """
    Returns true if x belongs in the range [l, r] over a circular domain
    Assume we have points in a circle next(x1) = x2, next(x2) = x3, ..., next(xn) = 1
    
    Then this returns true if x is in the set {l, next(l), next(next(l)), ... , r}
    """
    if (l < r):
        return l <= x <= r
    else:
        return  x >= l or x <= r
    
def is_on_season(date, date_start, date_end):
    """
    Return true if the date was in the same season as date_o
    """
    l = (date_start.month, date_start.day)
    r = (date_end.month, date_end.day)
    x = (date.month, date.day)
    return inrange_circ(x, l, r)

def is_from_this_year(date, date_end):
    """
    :param date_end: The date to check
    """
    return date > date_end
    
    
def process_track(track, track_list, start_date, end_date):
    """
    Evaluates if the track is in season, and then adds it to 
    the track list if it is.
    """
    added_time = datetime.strptime(track["added_at"], "%Y-%m-%dT%H:%M:%SZ")
    # Ignore tracks from this year 
    if is_from_this_year(added_time, end_date):
        return
    
    if is_on_season(added_time, start_date, end_date):
        track_list.append(track)

def get_all_tracks_gracefully(sp : spotipy.Spotify,
                              playlist_id, 
                              playlist_name,
                              max_tracks= None,
                              from_liked_songs=False):
    """
    Iteratively retrieve the names of all tracks in the playlist,
    slowly, to not reach the rate limit
    """
    offset = 0
    limit = 50
    res = []
    print("Retrieving songs from playlist: {}".format(playlist_name))
    while True:
        try:
            print("\r   Progress: {} songs".format(offset), end="")
            if (from_liked_songs):
                new_tracks = sp.current_user_saved_tracks(offset = offset, limit=limit)["items"]
            else:    
                new_tracks = sp.playlist_items(playlist_id, offset = offset, limit=limit)["items"]
            res.extend(new_tracks)
            offset += len(new_tracks)
            if (len(new_tracks) < limit):
                break
            if (max_tracks is not None and offset >= max_tracks):
                break
            
        except:
            break
        
        time.sleep(1.5)
    print("\r   {} songs to be analyzed".format(offset))
    return res
        
      
# def is_valid_uri(sp, uri):
#     try:
#         result = sp.track(uri)
#         return True if result else False
#     except Exception as e:
#         return False
  
def gracefully_add_tracks_to_playlist(sp : spotipy.Spotify,
                                      playlist_id,
                                      track_uris):
    """
    There is a 100 song limit for adding through an api call, so we have to do it in batches
    
    Some uris can be malformed (e.g. if the song was deleted), so we have to filter those out
    """
    print("Adding songs to playlist...")
    for i in range(0, len(track_uris), 100):
        try:
            sp.playlist_add_items(playlist_id, track_uris[i : i + 100], )
            print(f"\r   Progress: {min(i+100, len(track_uris))}/ {len(track_uris)} songs", end="")
        except spotipy.exceptions.SpotifyException:
            pass
        time.sleep(1.5)
    print()
    
def create_date_range(args):
    """
    Creates a date range for the current season
    """
    now = datetime.now()
    last_year = now - timedelta(days=365)
    start_date = last_year - timedelta(days=args.range_in_days // 2)
    end_date = last_year + timedelta(days=args.range_in_days // 2)
    return start_date, end_date

def uri_is_invalid(uri):
    return uri.startswith("spotify:local")

def is_item_valid(item):
    """
    Some items are do not contain neither a uri nor a name
    """
    return "track" in item and item["track"] is not None and "uri" in item["track"]
    
def run():
    
    # Set up the Spotify API client
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
    token = util.prompt_for_user_token(sp.current_user()["display_name"],
                    scope="playlist-read-private user-library-read playlist-modify-private")

    sp = spotipy.Spotify(auth=token, auth_manager=SpotifyOAuth())

    parser = make_parser()
    args = parser.parse_args()
    

    # Determine the date range to look for songs in
    start_date, end_date = create_date_range(args)

    # Retrieve the user's playlists
    playlists = sp.current_user_playlists()

    # Display the playlists and allow the user to choose which ones to include
    # Reformat the following code to be more clean
    print("Select the playlists to include in the final playlist:")
    print("===============================================")
    playlists = playlists['items'] + [{"name": "Liked Songs"}]

    for i, playlist in enumerate(playlists, start=1):
        print(f"{i}. {playlist['name']}")
        
        
    chosen_indices = input("Enter the numbers of the playlists you want to include, separated by commas: ")
    chosen_indices = [int(index.strip()) for index in chosen_indices.split(",")]

    # Retrieve the tracks that were added to the chosen playlists during the specified time frame
    new_playlist_tracks = []
    for i, playlist in enumerate(playlists, start=1):
        if i not in chosen_indices:
            continue
            
        # User selected liked songs
        if (len(playlists) == i):
            tracks = get_all_tracks_gracefully(sp, None, "Liked Songs", from_liked_songs=True, max_tracks=None)
        else:
            tracks = get_all_tracks_gracefully(sp, playlist["id"], playlist["name"], from_liked_songs=False, max_tracks=None)
            
            
        for track in tracks:
            process_track(track , new_playlist_tracks, start_date, end_date)
            

    new_playlist_tracks.sort(key= lambda x: datetime.strptime(x['added_at'], "%Y-%m-%dT%H:%M:%SZ"))
    # Create a new playlist and add the retrieved tracks to it


    # Create a new playlist
    playlist_name = "reminiscence {} - {}".format(
        start_date.strftime("%B %d"), end_date.strftime("%B %d"))
    playlist_description = "Songs between {} and {}, created by reminiscence".format(
        start_date.strftime("%B %d"), end_date.strftime("%B %d"))
    playlist = sp.user_playlist_create(sp.current_user()['id'], playlist_name, public=False, description=playlist_description)

    # Add tracks to the new playlist
    if (len(new_playlist_tracks) > 0):
        # Playlists can have users to so we have to filter them out
        new_playlist_tracks = list(filter(lambda x: is_item_valid(x), new_playlist_tracks))
        for track in new_playlist_tracks:
            uri  = track["track"]["uri"]
            if uri_is_invalid(uri):
                print("Warning: Track {} has Invalid URI, will be skipped.".format(track["track"]["name"]))
                
        gracefully_add_tracks_to_playlist(sp, playlist['id'], list(
                    filter(lambda x: not uri_is_invalid(x),
                    map(lambda x: x["track"]["uri"], new_playlist_tracks))
                    )
        )
        print(f"We found {len(new_playlist_tracks)} in-season songs for you!")
        print(f"A new playlist has been created with name: \"{playlist_name}\"!" +
            " You can find it in your Spotify library.")
            
    else:
        print("No songs were found for the current season, so no playlist was created.")
        
if __name__ == "__main__":
    run()
