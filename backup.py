import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import spotipy.util as util
import argparse
import time
import traceback
import os

def make_parser():
    parser = argparse.ArgumentParser(description='Create playlist of songs from the current season')
    parser.add_argument('--range-in-days', type=int, default=30,
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
    print("Select the playlists to backup to files:")
    print("===============================================")
    playlists = playlists['items'] + [{"name": "Liked Songs"}]

    for i, playlist in enumerate(playlists, start=1):
        print(f"{i}. {playlist['name']}")
        
        
    chosen_indices = input("Enter the numbers of the playlists you want to backup, separated by commas: ")
    chosen_indices = [int(index.strip()) for index in chosen_indices.split(",")]

    # Retrieve the tracks that were added to the chosen playlists during the specified time frame
    playlists_tracks = []
    chosen_playlists = []
    for i, playlist in enumerate(playlists, start=1):
        if i not in chosen_indices:
            continue
            
        # User selected liked songs
        if (len(playlists) == i):
            tracks = get_all_tracks_gracefully(sp, None, "Liked Songs", from_liked_songs=True, max_tracks=None)
        else:
            tracks = get_all_tracks_gracefully(sp, playlist["id"], playlist["name"], from_liked_songs=False, max_tracks=None)
            
        tracks.sort(key= lambda x: datetime.strptime(x['added_at'], "%Y-%m-%dT%H:%M:%SZ"))
        playlists_tracks.append(tracks)
        chosen_playlists.append(playlist)
    

    bckup_folder = "spotipy_backed_up_playlists"
    if not os.path.exists(bckup_folder):
        os.mkdir(bckup_folder)
    
    print("Backing up the playlists.. I hope no artists has a comma in their name right?")
    for i in range(len(chosen_playlists)):
        playlist_name = chosen_playlists[i]["name"]
        output_fname = os.path.join(bckup_folder, playlist_name)
        csv_lines=[]
        csv_lines.append(",".join(["track_uri", "added_at_time", "name", "artist", "album"]))
        for track in playlists_tracks[i]:
            # Local tracks I think are like this
            if (track["track"] is None):
                continue
            try:
                artists = "-".join([artist["name"] for artist in track["track"]["artists"]])
                attributes = [track["track"]["uri"], track['added_at'],track["track"]["name"],
                               artists, track["track"]["album"]["name"]]
            except KeyError:
                print("A track has not been backed up because it is malformed.. maybe you can" +\
                       "add it to the backed up files  manually:")
                print(track)

            line = ",".join(attributes)
            csv_lines.append(line)
        csv_contents = "\n".join(csv_lines)
        

        print(f"Saving playlist {playlist_name} at {output_fname}")
        with open(output_fname, "w") as f:
            f.write(csv_contents)

        
if __name__ == "__main__":
    run()
