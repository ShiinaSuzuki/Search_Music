from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
import os
from google.oauth2.service_account import Credentials

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import json

gc = gspread.oauth(
                   credentials_filename=os.path.join("client_secret.json"), # 認証用のJSONファイル
                   authorized_user_filename=os.path.join("authorized_user.json"), # 証明書の出力ファイル
                   )
wb = gc.open_by_key('1Nd3iBR4vRfEoKNQTmtNb8IhWPN5An95eafURC6Aj1-c') # *****にtest03ファイルのキーを入れる
ws = wb.get_worksheet(0) # 最初のシートを開く(idは0始まりの整数)


# Spotify Developer Dashboardで取得したクライアントIDとクライアントシークレットを設定
client_id = 'dae690eb7fff4646bdc0e8ba7ee3b759'
client_secret = '84b96edadd1b42d4b75585649aa21bbd'

# Spotipyの認証設定
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


########
def get_track_info(artist_name, track_name):
    # アーティスト名と曲名を検索してトラック情報を取得
    results = sp.search(q=f'artist:{artist_name} track:{track_name}', type='track')
    
    # 検索結果から最初のトラックを取得
    if results['tracks']['items']:
        track = results['tracks']['items'][0]

        # トラック情報を取得
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        release_year = track['album']['release_date'][:4]  # リリース年を取得
        popularity = track['popularity']
        url = track['external_urls']['spotify']
        image = track['album']['images'][0]['url']

        # 曲のIDを取得
        track_id = track['id']

        # 曲の音楽情報（キーとテンポ）を取得
        audio_features = sp.audio_features(track_id)[0]
        key = audio_features['key']
        tempo = audio_features['tempo']
        

        
        return {
            'Artist': artist_name,
            'Track Name': track_name,
            'Release Year': release_year,
            'Popularity': popularity,
            'Key': key,
            'Tempo': tempo,
            'URL': url,
            'Image' : image
        }
    else:
        return None


########

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # フォームからアーティスト名と曲名を受け取る
        artist_name = request.form.get('artist_name')
        track_name = request.form.get('track_name')
        # ここでデータを処理したり、他のページに渡すことができます

        


        track_info = get_track_info(artist_name, track_name)
        if track_info:
            track_info = get_track_info(artist_name, track_name)
            key_to_search = track_info['Key']
            tempo_to_search = track_info['Tempo']
            target_url = track_info['URL']
            
            found_tracks = []
            for row in ws.get_all_records():
                if (row['key'] == key_to_search and
                        abs(row['tempo'] - tempo_to_search) <= 15 and
                        row['popularity'] > 60 and
                            row['url'] != target_url):
                    found_tracks.append(row)
            if found_tracks:
                return render_template('output.html', track_info=track_info, found_tracks=found_tracks)
            else:
                print('該当する曲が見つかりませんでした。')
        else:
            print('入力した曲が見つかりませんでした。')
            return render_template('noresult.html')
        # output.htmlにリダイレクト
     
    return render_template('input.html')

@app.route('/output')
def output():
    # テンプレートに渡すデータを設定
    
    found_tracks = request.args.get('found_tracks')
    track_info = request.args.get('track_info')

    # track_infoをJSON文字列に変換
    track_info_dict = json.loads(track_info.replace("'", "\""))
    #found_tracks_dict = json.loads(found_tracks.replace("'", "\""))
    return render_template('output.html', track_info = track_info, found_tracks=found_tracks)

if __name__ == '__main__':
    app.run(debug=True)
