# reminiscence

What were you listening to this part of the year, last year? 2 years ago? This tool will create a playlist of songs that you listened to in the same part of the year in the past.


## How it works

Select some of your playlists where you have accumulated songs over the years and reminiscence creates a playlist containing the songs that you added to those playlists around the same period as now, but in previous years.


This is the way I like to listen to music. If it is spring I like to listen to songs that I listened to in spring in past years. This brings back a lot of memories and i enjoy listening to music more. Sometimes even listening to music that I listened to last winter while being spring makes me uncomfortable.

## Set up instructions

First clone the repository and cd into it

```sh
git clone https://github.com/NickSmyr/spotify-reminiscence
cd spotify-reminiscence
```

Then you need to have a developer account for spotify. You can create one without extra costs [here](https://developer.spotify.com). 

Then you need to fetch some secrets, specifically the **spotify client id** and **spotify client secret**. For this you need to create a placeholder app, with any name. Instructions [here](https://support.heateor.com/get-spotify-client-id-client-secret/). 

Finally set the **redirect url** of your application as the following: http://localhost:5000/callback

Then set the following necessary environment variables. For Linux/MacOS you can do the following 

```sh
export SPOTIPY_CLIENT_ID=<your client id>
export SPOTIPY_CLIENT_SECRET=<your client secret key>
export SPOTIPY_REDIRECT_URI=http://localhost:5000/callback
```

Then install the only requirement
```sh
pip install spotipy
```

And finally execute the script. 

```sh
python create.py
```

When the script starts you will be prompted to authenticate using your spotify account in a webpage.

The script will ask you to include some playlists for your reminiscence playlist and when its finished you will see a new playlist in your library.