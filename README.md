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
DEBUG=False
```

#### SEARCH_FLAIR
This is the flair for feedback tracker posts for each user.


##### requiremennts.txt
```
altgraph==0.16.1
APScheduler==3.6.1
certifi==2019.9.11
chardet==3.0.4
future==0.18.1
idna==2.8
numpy==1.17.3
pefile==2019.4.18
praw==6.4.0
prawcore==1.0.1
pytz==2019.3
pywin32-ctypes==0.2.0
requests==2.22.0
six==1.12.0
tzlocal==2.0.0
update-checker==0.16
urllib3==1.25.6
websocket-client==0.56.0
```

##### Changing bot run time?
The bot is scheduled to run every 2 minutes by default.  If you want to change the bot you will need to open up the script file ft_bot.py in an editor(Notepad++, Pycharm, Atom, etc).

Scroll all the way down to the bottom of the script to here.
> scheduler.add_job(bot.batch_update,'interval', id='batch_id_001', minutes=2)

Only change the last argument(minutes=2) to change how often the bot runs.


30 Seconds
```
scheduler.add_job(bot.batch_update,'interval', id='batch_id_001', seconds=30)
```

1 minute
```
scheduler.add_job(bot.batch_update,'interval', id='batch_id_001', minutes=1)
```
5 minutes
```
scheduler.add_job(bot.batch_update,'interval', id='batch_id_001', minutes=5)
```
