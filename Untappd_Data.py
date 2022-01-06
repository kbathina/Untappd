import json
import requests
import urllib.request as url
import os.path
import os
import sys
from datetime import datetime,timedelta

if not os.path.exists('data/'):
    os.mkdir('data/')
    os.mkdir('data/badge_images/')

with open('user_information.txt','r') as f:
    data = [x.strip() for x in f.readlines()]
    
username = data[0].split('= ')[1]
client_id  = data[1].split('= ')[1]
client_secret = data[2].split('= ')[1]
access_token = data[3].split('= ')[1]



def get_main_data():
    '''
    download full data
    '''
    with open('data/untappd_checkins.json') as json_file: # read in data from untappd api
        current_data = json.load(json_file)

    current_time = datetime.strptime(current_data[0]['created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)\

    checkins = requests.get("https://api.untappd.com/v4/user/checkins/?access_token="+access_token)

    append_data = []
    checkins_data = checkins.json()
    for checkin in checkins_data["response"]["checkins"]["items"]:
        new_time = datetime.strptime(checkin['created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
        if new_time > current_time:
            append_data.append(checkin)

    
    count = 0
    while new_time > current_time:
        count += 1
        if count % 10 == 0: print(str(count) + ' checkins')
        max_id   = checkins_data["response"]["pagination"]["max_id"]
        next_url = "https://api.untappd.com/v4/user/checkins/?max_id=" + str(max_id) + "&access_token="+access_token
        checkins = requests.get(next_url)
        checkins_data = checkins.json()
        for checkin in checkins_data["response"]["checkins"]["items"]:
            new_time = datetime.strptime(checkin['created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
            if new_time > current_time:
                append_data.append(checkin)
            else:
                break

    append_data.extend(current_data)
    with open("data/untappd_checkins.json", "w") as f:
        json.dump(append_data, f)

    return current_data

def get_unique_data():
    '''
    get unique data
    '''
    with open('data/untappd_unique_beer.json') as json_file: # read in data from untappd api
        current_data = json.load(json_file)

    current_time = datetime.strptime(current_data[0]['first_created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
    new_time = current_time + timedelta(1)

    append_data = []
    total = 0
    while new_time > current_time:
        next_url = 'https://api.untappd.com/v4/user/beers/' + username+'?offset=' + str(total) + '&client_id='+client_id+"&client_secret="+client_secret
        checkins = requests.get(next_url)
        checkins_data = checkins.json()
        for checkin in checkins_data["response"]["beers"]["items"]:
            new_time = datetime.strptime(checkin['first_created_at'],'%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
            if new_time > current_time:
                append_data.append(checkin)
            else:
                break
        total += 25

    append_data.extend(current_data)
    with open("data/untappd_unique_beer.json", "w") as f:
        json.dump(append_data, f)

def update_bages(current_data):
    '''
    updating badges
    '''
    with open('data/untappd_checkins.json') as json_file: # read in data from untappd api
        data = json.load(json_file)[::-1]

    for d in data:
        if d['badges']['count'] > 0:
            for badge in d['badges']['items']:
                name = badge['badge_image']['lg']
                if not os.path.isfile( "data/badge_images/"+name.split('/')[-1]):
                    try:
                        url.urlretrieve(name, "data/badge_images/"+name.split('/')[-1])
                    except: 
                        pass

if __name__ == '__main__':

    if not os.path.exists('data/untappd_checkins.json'):
        current_data = requests.get("https://api.untappd.com/v4/user/checkins/?access_token="+access_token).json()["response"]["checkins"]["items"]
        with open("data/untappd_checkins.json", "w") as f:
            json.dump(current_data, f)
    else: 
        current_data = get_main_data()

    update_bages(current_data)

    if not os.path.exists('data/untappd_unique_beer.json'):
        unique_data = requests.get("https://api.untappd.com/v4/user/beers/"+username+"?client_id="+client_id+"&client_secret="+client_secret).json()["response"]["beers"]["items"]
        with open("data/untappd_unique_beer.json", "w") as f:
            json.dump(unique_data, f)
    else: 
        get_unique_data()