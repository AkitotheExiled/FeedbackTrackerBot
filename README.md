# FeedbackTrackerBot
 Tracks the feedback for users on /r/SportsCardTracker
 
##### Demo up at www.reddit.com/r/kgamers
 
 #### How does it work?
 1. Completely fill out the fields in config.ini.  You may leave SEARCH_FLAIR alone if this is for /r/SportsCardTracker.
 2. Run the bot and it will search the users for their feedback tracker posts and then gather all their feedback and make updates if necessary.
 3. If any issues come up, please submit an issue here or PM me on reddit.
 
 ### config.ini
 ```
USER = yourusername
PASSWORD= yourpassword
CLIENT_ID= yourclient
SECRET= yoursecret
SUBREDDIT= yoursubreddit
SEARCH_FLAIR=Feedback Tracker
```

#### SEARCH_FLAIR
This is the flair for feedback tracker posts for each user.


##### requiremennts.txt
```
certifi==2019.9.11
chardet==3.0.4
idna==2.8
praw==6.4.0
prawcore==1.0.1
requests==2.22.0
six==1.12.0
update-checker==0.16
urllib3==1.25.6
websocket-client==0.56.0
```
