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
* orca


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
3. Fill in the following link with your information replaced https://untappd.com/oauth/authorize/?client_id=CLIENTID&client_secret=CLIENTSECRET&response_type=code&redirect_url=redirect_url&code=CODE

    1. CLIENTID = your client_id
    2. CLIENTSECRET = your client_secret
    3. redirect_url = your callback URL
    4. CODE (not code, it is the one in all caps) = the code received from Step 2. You don't need the code anymore after this
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

3.  Because of the rate limit imposed by the Untappd API, the script could take a long time if you have thousands of checkins. Each subsequent run only downloads new checkins so it should be quick depending on how often you run this. The data should now all be downloaded into the `data/` directory that was created.


# Analyzing Data
1. Run the python file `Untappd_Analytics.py`. In the terminal, type in 
```python
 python Untappd_Analytics.py 
 ```
2. The `graphs/` directory should contain all of images. 

# Updating Data and Visualizations
## Run these scripts every time you want to update your information. Make sure to do it often if you don't want to get hit by the rate limit. 
1. Run the python file `Untappd_Data.py`.
2. Run the python file `Untappd_Analytics.py`.

# If you have any new ideas for graphs/analysis, leave a request in the Issues tab and I'll get to it. 