# How to access your data

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
2. The url in the browser should have changed to https://untappd.com/oauth/authenticate/personal?code=###################. The ################### is your access token. Make sure to save this also. 

# Collecting Data

1. Open `user_information.txt` and fill in the user, client_id, client_secret, and the access_token.
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


Note: You'll need python3 and various packages to collect and analyze the data. Make sure to have them installed or the scripts won't work. 