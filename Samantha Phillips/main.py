
import os
from flask import Flask, redirect, request, session, url_for, jsonify
from spotifyMethods import cache_handler, sp_oauth, sp_client
import spotipy
import csv


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)



@app.route('/')
def home():
    token = cache_handler.get_cached_token()
    if not token or not token.get('access_token'):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        sp_oauth.get_access_token(code)
    return redirect(url_for('get_playlists'))

@app.route('/get_playlists')
def get_playlists():
    token = cache_handler.get_cached_token()
    if not token or not token.get('access_token'):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp_client.current_user_playlists() 
    if not playlists or 'items' not in playlists: 
        return "No playlists found" 
    
    playlists_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlists['items']] 

    playlists_dict = {'track_info': {}}
    track_info_list = []

    for name, url in playlists_info: 
        playlist_id = url.split('/', 4)[4]
        info = sp_client.playlist_items(playlist_id, fields='items(track(id,name,artists(name)))')
        items = info.get('items', []) # type: ignore

        for item in items:
            track = item.get('track', {})
            if not track:
                continue
            song_id = track.get('id', '')
            song_title = track.get('name', '')
            song_artist_name = track.get('artists', [{}])[0].get('name', '')

            track_info_list.append({
                'id': song_id,
                'title': song_title,
                'artist': song_artist_name
            })

        playlists_dict['track_info'][playlist_id] = track_info_list
    
    with open('user_info.csv', 'w', newline='') as csvfile:
        fieldnames = ['artist', 'id', 'title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in track_info_list: # type: ignore
            writer.writerow(row) 

    return playlists_dict 
    


@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('home')) 


if __name__ == '__main__': 
    app.run(debug=True)