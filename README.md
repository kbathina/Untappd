# How to access your data


Note: You'll need python3 and the following packages for this to work

* pandas
* json
* requests
* urllib.request
* sys
* collections
* datetime
* os
* itertools
* matplotlib
* numpy
* random
* folium
* seaborn
* plotly


## Apply for access
1. Go [here](https://untappd.com/api/dashboard) to request access from Untappd
2. I chose Personal App but you should choose whatever you need it for
3. You need the
    * Application name
    * Support URL (I put my personal website but it doesn't really matter unless you are trying to access the API for a website)
    * Callback URL (I just used a random word)
    * Description
4. Once accepted, you should have a Client ID and a Client Secret.

## Find Access Token 
1. Fill in the following link with your information replaced (CLIENTID, CALLBACKURL) https://untappd.com/oauth/authenticate/?client_id=CLIENTID&response_type=code&redirect_url=CALLBACKURL and go to the website.
2. The url in the browser should have changed to https://untappd.com/oauth/authenticate/personal?code=###################. The ################### is your code. Make sure to save this also. 
3. Fill in the following link with your information replaced (CLIENTID, CLIENTSECRET,CALLBACKURL,CODE) https://untappd.com/oauth/authorize/?client_id=CLIENTID&client_secret=CLIENTSECRET&response_type=code&redirect_url=CALLBACKURL&code=CODE
4. You should be sent to a page with your access_token

# Collecting Data

1. Create a txt file called `user_information.txt`. The file should look like this where ############ is replaced by your information 
```
username      = ############
client_id     = ############
client_secret = ############
access_token  = ############
```

2. Run the python file `Untappd_Data.py`. If you are going to run it in the terminal, type 
```python
 python Untappd_Data.py 
 ```
 3. The data should now all be downloaded into the `data/` directory that was created


# Analyzing Data
1. Run the python file `Untappd_Analytics.py`. In the terminal, type in 
```python
 python Untappd_Analytics.py 
 ```
2. The `graphs/` directory should contain all of images. 


# If you have any new ideas for graphs/analysis, leave a request in the Issues tab and I'll get to it. 