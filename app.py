#!flask/bin/python
import sys
from flask import Flask, request, redirect, render_template
from app_info import client_id, client_secret, redirect_uri
import requests
from requests.auth import HTTPBasicAuth
import urllib
import string
import random
import base64
import json

app = Flask(__name__)

state_len = 16

def random_string(length):
    return ''.join((random.choice(string.ascii_letters + string.digits)) for i in range(length))

@app.route('/')
def index():
    return "Meow"

@app.route('/help')
def help():
    return "Merp"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-read-recently-played playlist-modify-public playlist-read-private playlist-modify-private user-top-read'
    return redirect('https://accounts.spotify.com/authorize' + '?response_type=code' + '&client_id=' + client_id + 
        '&scope=' +  urllib.parse.quote(scope, safe='~()*!.\'') +
        '&redirect_uri=' +  urllib.parse.quote(redirect_uri, safe='~()*!.\'') +'&state=' + random_string(state_len))


@app.route('/callback')
def callback():
    state = request.args["state"]
    if state is None:
        return "An error occured 1"
    else:
        code_payload = {
            'grant_type': 'authorization_code',
            'code': str(request.args['code']),
            'redirect_uri': redirect_uri
        }

        req = requests.post('https://accounts.spotify.com/api/token', auth=HTTPBasicAuth(client_id, client_secret), data=code_payload)
        if req.status_code == 200:
            json_data = json.loads(req.text)
            access_token = json_data["access_token"]

            auth_header = {"Authorization":"Bearer {}".format(access_token)}

            user_profile_api_endpoint = 'https://api.spotify.com/v1/me'
            profile_response = requests.get(user_profile_api_endpoint, headers=auth_header)
            profile_data = json.loads(profile_response.text)
            user_id = profile_data['id']

            recently_played_url = 'https://api.spotify.com/v1/me/player/recently-played' + '?limit=50'
            rp_response = requests.get(recently_played_url, headers=auth_header)
            display_arr = json.loads(rp_response.text)['items']
            just_names = set()
            uri_list = set()
            for item in display_arr:
                uri_list.add(item['track']['uri'])
                just_names.add(item['track']['name'])

            top_tracks_url = 'https://api.spotify.com/v1/me/top/tracks' + '?limit=30' + '&time_range=short_term'
            tt_response = requests.get(top_tracks_url, headers=auth_header)
            display_array = json.loads(tt_response.text)['items']
            for i in range(len(display_array)):
                just_names.add(display_array[i]['name'])
                uri_list.add(display_array[i]['uri'])

            user_playlists_url = 'https://api.spotify.com/v1/me/playlists'
            playlists_response = requests.get(user_playlists_url, headers=auth_header)
            playlists_array = json.loads(playlists_response.text)['items']
            already_exists = False
            playlist_id = None
            for i in range(len(playlists_array)):
                if playlists_array[i]['name'] == "Recently Played":
                    already_exists = True
                    playlist_id = playlists_array[i]['id']
            r_header = {
                "Authorization":"Bearer {}".format(access_token),
                "Content-Type": "application/json"
            }

            put_payload = {
                "uris": list(uri_list)
            }
            if not already_exists:
                #create new playlist and add tracks to it
                new_playlist_url = 'https://api.spotify.com/v1/users/{}/playlists'.format(user_id)
                create_payload = {
                    "name": "Recently Added"
                }
                new_playlist_response = requests.post(new_playlist_url, data=json.dumps(create_payload), headers=r_header)
                playlist_id = json.loads(new_playlist_response.text)['id']
            replace_tracks_url = 'https://api.spotify.com/v1/users/{}/playlists/{}/tracks'.format(user_id, playlist_id)
            playlist_response = requests.put(replace_tracks_url, data=json.dumps(put_payload), headers=r_header)
            return render_template('index.html', sorted_array=just_names)
        else:
            return "An error occurred 2"



if __name__ == '__main__':
    app.run(debug=True)