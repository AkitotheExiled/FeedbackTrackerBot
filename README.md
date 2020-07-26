# FeedbackTrackerBot
 Tracks the feedback for users on /r/SportsCardTracker
 
##### Demo up at www.reddit.com/r/kgamers
 
 #### How does it work?
Feedback_tracker.py
1. Gathers all feedback in your feedback tracker subreddit.
* It checks titles for the words, [positive, negative, neutral] and based on the word it assigns a value(1,-1,0)
------
Feedback_reply.py
1. Replies to all posts in your sale subreddit with the user's feedback data.
 
 ### config.ini
 ```
USER = yourusername
PASSWORD= yourpassword
CLIENT_ID= yourclient
SECRET= yoursecret
SUBREDDIT_TRACKER= yoursubreddit
SUBREDDIT_REPLY= yoursubreddit
SEARCH_FLAIR=Feedback Tracker
DEBUG=False
```

#### SUBREDDIT_TRACKER
This is your subreddit where you track user feedback.  User's will post feedback about their sellers and the bot takes that information and adds it into the database. An example,

```
title: [positive] u/scoopjr
bot will take that feedback and give scoopjr a +1.
```

#### SUBREDDIT_REPLY
This subreddit is where users will buy/sell/trade.  This is used for feedback_reply.py where that script will automatically reply to users with feedback information.  An example,
```
title: Selling prime rib steak! 200$ shipped
bot replies:
"User: /u/scoopjr
Join date: Jan 2014
Comment Karma: 0
Post Karma: 0
Feedback: 0
This bot is used for screening purposes and does not guarantee a successful trade/purchase.  
```


#### Title format
```
Title format: [positive] u/username or positive /u/username

```
The above format is a requirement to track feedback from users.  Please see the automoderator rule for setting this up automatically with automod.


##### requirements.txt
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
PyInstaller==3.6
pytz==2019.3
pywin32-ctypes==0.2.0
requests==2.22.0
six==1.12.0
SQLAlchemy==1.3.18
tzlocal==2.0.0
update-checker==0.16
urllib3==1.25.6
websocket-client==0.56.0

```
##### How many subreddits do I need to run this bot?
2 subreddits. 1 for tracking feedback and another for buying/selling.

##### How do I run this bot on my subreddit?
1.You need to run feedback_tracker.py
2.Then, you may run feedback_reply.py

##### Will you run this bot for me?
No, you may run this bot off a Raspberry Pi, home PC, or online cloud service.  I will not run this bot for you.

##### What was that automoderator rule for enforcing title formatting, again?
```
---
    ~title (regex,full-exact): '[\[\{.]*(positive|negative|neutral)[(\s|\S)]+u\/([a-zA-Z0-9!$*-_]*)'
    action: remove
    comment: This submission does not follow the following format: [positive] u/username
```
