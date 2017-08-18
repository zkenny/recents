#!flask/bin/python
from flask import Flask, request, redirect, render_template
import requests
from requests.auth import HTTPBasicAuth
import urllib
import string
import random
import base64
import json
import sys

app = Flask(__name__)

client_id = '71dd46c4bb6641e6a438804d26021836'
client_secret = 'b44780508cc34e5f92e97d25a1cf87ed'
redirect_uri = 'http://127.0.0.1:5000/callback'

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
    scope = 'user-read-private user-read-email user-read-recently-played playlist-modify-public playlist-modify-private'
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

            recently_played_url = 'https://api.spotify.com/v1/me/player/recently-played' + '?limit=50'
            rp_response = requests.get(recently_played_url, headers=auth_header)
            display_arr = json.loads(rp_response.text)['items']
            just_names = []
            for item in display_arr:
                just_names.append(item['track']['name'])

            # playlist_api_endpoint = '{}/playlists'.format(str(profile_data['href']))
            # playlists_response = requests.get(playlist_api_endpoint, headers=auth_header)
            # playlist_data = json.loads(playlists_response.text)

            # display_arr = [profile_data] + playlist_data["items"]
            return render_template('index.html', sorted_array=just_names)
            # redirect('/#' + {access_token: access_token, refresh_token, refresh_token})
        else:
            return "An error occurred 2"
            # redirect()



if __name__ == '__main__':
    app.run(debug=True)