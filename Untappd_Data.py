import json
import requests
import urllib.request as url
import os.path
import os
import sys

if not os.path.exists('data/'):
    os.mkdir('data/')
    os.mkdir('data/badge_images/')

with open('user_information.txt','r') as f:
    data = [x.strip() for x in f.readlines()]
    
username     = data[0].split('= ')[1]
client_id    = data[1].split('= ')[1]
client_secret= data[2].split('= ')[1]
access_token = data[3].split('= ')[1]

######## full data

user = requests.get("https://api.untappd.com/v4/user/info/"+username+"?client_id="+client_id+"&client_secret="+client_secret)
user_data = user.json()
total_checkins = user_data["response"]["user"]["stats"]["total_checkins"]

print("Total Checkins = " + str(total_checkins))

checkins = requests.get("https://api.untappd.com/v4/user/checkins/?access_token="+access_token)

checkins_data = checkins.json()
full_data = checkins_data["response"]["checkins"]["items"]

while (len(full_data) < total_checkins):
    max_id   = checkins_data["response"]["pagination"]["max_id"]
    next_url = "https://api.untappd.com/v4/user/checkins/?max_id=" + str(max_id) + "&access_token="+access_token
    print(str(len(full_data)) + '/' + str(total_checkins))
    checkins = requests.get(next_url)
    checkins_data = checkins.json()
    full_data.extend(checkins_data["response"]["checkins"]["items"])

with open("data/untappd_checkins.json", "w") as f:
    json.dump(full_data, f)

########## unique data

user = requests.get("https://api.untappd.com/v4/user/beers/"+username+"?client_id="+client_id+"&client_secret="+client_secret)
checkins_data = user.json()
total_checkins = checkins_data["response"]['total_count']

print("Total Distinct Checkins = " + str(total_checkins))

# checkins = requests.get("https://api.untappd.com/v4/user/beers/?access_token="+access_token)

full_data = checkins_data["response"]['beers']['items']

total = 25
while (total < total_checkins):
    max_id   = checkins_data["response"]["pagination"]["max_id"]
    next_url = 'https://api.untappd.com/v4/user/beers/' + username+'?offset=' + str(total) + '&client_id='+client_id+"&client_secret="+client_secret
    print(str(total) + '/' + str(total_checkins))
    checkins = requests.get(next_url)
    checkins_data = checkins.json()
    full_data.extend(checkins_data["response"]["beers"]['items'])
    total += 25

with open("data/untappd_unique_beer.json", "w") as f:
    json.dump(full_data, f)

########## updating badges
print('Checking for new badges')

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

    