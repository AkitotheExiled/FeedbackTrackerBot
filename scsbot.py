import praw
from configparser import ConfigParser
import requests
import sqlite3
from datetime import datetime
import time
# TO DO LIST
# Have bot add

# POST FORMAT
# * Username
# * join_date
# * karma
# * confirmed feedback total
# View their confirmed feedback link

class Scs_Bot():

    def __init__(self):
        self.user_agent = "SportsCardSales Bot V0.2 by ScoopJr"
        print('Starting up...', self.user_agent)
        CONFIG = ConfigParser()
        CONFIG.read('config.ini')
        self.user = CONFIG.get('main', 'USER')
        self.password = CONFIG.get('main', 'PASSWORD')
        self.client = CONFIG.get('main', 'CLIENT_ID')
        self.secret = CONFIG.get('main', 'SECRET')
        self.subreddit = CONFIG.get('main', 'SUBREDDIT')
        self.token_url = "https://www.reddit.com/api/v1/access_token"
        self.token = ""
        self.t_type = ""
        self.reddit = praw.Reddit(client_id=self.client,
                                  client_secret=self.secret,
                                  password=self.password,
                                  user_agent=self.user_agent,
                                  username=self.user)
        self.flair = CONFIG.get('main', 'SEARCH_FLAIR')
        self.authors = []
        self.debug = bool(CONFIG.getboolean('main', 'DEBUG'))
        self.table = {}

    def get_token(self):
        """ Retrieves token for Reddit API."""
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']

    def query_data_for_user(self, user):
        db = sqlite3.connect('user_database.sqlite')
        cursor = db.cursor()
        sql = "SELECT total_fb, p_fb, neg_fb, n_fb FROM Users \
              WHERE username='{}'".format(str(user.lower()))
        cursor.execute(sql)
        db_data = cursor.fetchall()
        print(user, db_data)
        return db_data

    def get_date_from_utc(self, utc_timestamp):
        post_time = datetime.utcfromtimestamp(int(utc_timestamp)).strftime('%B %Y')
        #post_time = datetime.strptime(post_time, '%Y-%B')
        return post_time

    def bot_action(self):
        reply_template = "* Username: u/{}\n* Join date: {}\n* Post Karma: {}\n* Comment Karma: {} \n* Feedback: {}\n\n[You may view this users feedback here.]({})\n\nThis information does not guarantee a successful sale.  It is for you to use to screen potential sellers."

        tracker_link = 'https://www.reddit.com/r/SportsCardTracker/search/?q={}&restrict_sr=1&sort=new'
        feedback = None
        subreddit = self.reddit.subreddit(self.subreddit)
        do_not_comment = False
        for post in subreddit.stream.submissions():
            print('Combing through posts...')
            do_not_comment = False
            if post.archived or post.locked:
                continue
            for comment in post.comments:
                if comment.author.name.lower() == self.user.lower():
                    print(comment, comment.author.name)
                    do_not_comment = True
                    break
            if do_not_comment:
                continue
            try:
                feedback = self.query_data_for_user(post.author.name.lower())
            except Exception as e:
                print(e)
            if not feedback:
                feedback[0][0] = 0
            if not do_not_comment:
                print('Replying to post,',post.id)
                reply_text = reply_template.format(post.author.name, self.get_date_from_utc(post.author.created_utc), post.author.link_karma,
                                                    post.author.comment_karma, feedback[0][0], tracker_link.format(post.author.name))
                post.reply(reply_text)


if __name__ == '__main__':
    bot = Scs_Bot()
    bot.bot_action()


