import praw
from datetime import datetime, timedelta, timezone
import os
import requests, requests.auth
import re
from src.classes.baseclass import RedditBaseClass
from src.database.database import Users, Feedback, Database
from src.classes.logger import Logger
import time, static





class Tracker_Bot(RedditBaseClass):

    def __init__(self):
        super().__init__()
        self.user_agent = "PC:FeedbackTrackerBot:V1.5 by ScoopJr"
        print('Starting up...', self.user_agent)
        self.reddit = praw.Reddit(client_id=self.client,
                                  client_secret=self.secret,
                                  password=self.password,
                                  user_agent=self.user_agent,
                                  username=self.user)

        self.authors = []
        self.table = {}
        self.td = timezone(-timedelta(hours=7), name="RPST") # getting timezone for PST
        self.config_json = {}
        self.unixnow = datetime.timestamp(datetime.now(self.td.utc)) # turning the time of now into a datetime aware object
        self.queue = {"data": []} # holding our data from pushshift
        self.counter = 0
        self.values = ['positive', 'negative', 'neutral'] # values from the title
        self.regex_for_title = r"(positive|negative|neutral)[(\s|\S)]+u\/([a-zA-Z0-9!$*-_]*)" #matches positive/negative/neutral and gets the username
        self.db = Database()
        self.log = Logger()
        self.logger = self.log.logger

    def get_token(self):
        """ Retrieves token for Reddit API."""
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']

    def check_for_database(self):
        for file in os.listdir(os.getcwd()):
            if static.DATABASE_NAME in file:
                return True
        return False

    def digit_search(self, string):
        """Searches string for the one digit or more and returns it as a list."""
        regex_search = re.compile(r'\d+').findall(string)
        for item in regex_search:
            if item is None:
                regex_search[item] = 0
        return regex_search


    def get_or_create(self, model, **kwargs):
        instance = self.db.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            self.db.session.add(instance)
            self.db.session.commit()

    def exist_check_or_add_posts(self, model, **kwargs):
        instance = self.db.session.query(model).filter_by(**kwargs).first()
        if instance:
            print(instance)
            return True
        else:
            try:
                instance = model(**kwargs)
                self.db.session.add(instance)
                self.db.session.commit()
                return False
            except Exception as e:
                print(e)




    def new_logic(self):
        for item in self.queue["data"]:
            receiver = self.get_username_and_value_from_title(self.regex_for_title, item["title"].lower())
            print(f"Value,Title: {receiver}, Item: {item}")
            if not receiver:
                continue
            rep_value = receiver[0][0]
            person_exists = self.db.session.query(Users).filter_by(name=receiver[0][1]).first()
            if rep_value == 'positive':
                self.exist_check_or_add_posts(Feedback, post_id=item["postid"], author=item["author"],
                                              receiver=receiver[0][1],
                                              feedback_type=1)
            elif rep_value == 'negative':
                self.exist_check_or_add_posts(Feedback, post_id=item["postid"], author=item["author"],
                                              receiver=receiver[0][1],
                                              feedback_type=-1)
            elif rep_value == 'neutral':
                self.exist_check_or_add_posts(Feedback, post_id=item["postid"], author=item["author"],
                                              receiver=receiver[0][1],
                                              feedback_type=0)
            if not person_exists:
                self.get_or_create(Users, name=receiver[0][1])



    def get_allposts_wpush(self, before_utc, after_utc, loop=True):
        rounded_before = round(before_utc)
        rounded_after = round(after_utc)
        url = f"https://api.pushshift.io/reddit/search/submission/?subreddit={self.subreddit}&sort=desc&sort_type=created_utc&after={rounded_after}&before={rounded_before}&size=1000"
        after = None
        before = rounded_after - 10000000
        headers = {'user-agent': self.user_agent}
        print(url)
        try:
            data = requests.get(url).json()
            print(data)
            if not data["data"]:
                self.counter = 0
                print(self.queue[0])
                return self.queue
            if requests.get(url).status_code == requests.codes.ok:
                for items in data["data"]:
                    try:
                        after = items["created_utc"]
                        self.queue["data"].append({"postid": items["id"]})
                        self.queue["data"][self.counter]["title"] = items["title"]
                        self.queue["data"][self.counter]["author"] = items["author"].lower()
                        self.counter += 1
                    except Exception as e:
                        print(e.with_traceback())
                        pass
                if loop:
                    time.sleep(5)
                    self.get_allposts_wpush(after, before)
            else:
                print(self.queue)
                self.counter = 0
                return self.queue
        except Exception:
            self.logger.info("Error getting pushshift post data", exc_info=True)

    def get_utc_days_ago(self, days):
        if days == 0:
            return self.unixnow
        past_date = datetime.now(tz=self.td) - timedelta(days)
        return datetime.timestamp(past_date)

    def get_value_from_title(self, title, **kwargs):
        for item in kwargs.values():
            if item in title:
                return item

    def get_username_and_value_from_title(self, regex_pattern, title):
        regex_pat = re.compile(regex_pattern,re.IGNORECASE)
        title_matches = re.findall(regex_pat, f"{title}")
        return title_matches

    def get_date_from_utc(self, utc_timestamp):
        post_time = datetime.utcfromtimestamp(int(utc_timestamp)).strftime('%B %Y')
        # post_time = datetime.strptime(post_time, '%Y-%B')
        return post_time


    def main(self):
        if not self.check_for_database():
            self.get_allposts_wpush(self.unixnow, self.unixnow - 500000)
            self.new_logic()
        else:
            subreddit = self.reddit.subreddit(self.subreddit)
            while True:
                for post in subreddit.stream.submissions(pause_after=3):
                    if post is None:
                        break
                    print(f'Going through the subreddit: {post.id}: {post.title} by {post.author.name}')
                    regex_matches = self.get_username_and_value_from_title(self.regex_for_title, post.title.lower())
                    if not regex_matches:
                        continue
                    rep_receiver = regex_matches[0][1].lower()
                    rep_value = regex_matches[0][0]
                    if rep_value == 'positive':
                        self.exist_check_or_add_posts(Feedback, post_id=post.id, author=post.author.name.lower(),
                                                      receiver=rep_receiver,
                                                      feedback_type=1)

                    elif rep_value == 'negative':
                        self.exist_check_or_add_posts(Feedback, post_id=post.id, author=post.author.name.lower(),
                                                      receiver=rep_receiver,
                                                      feedback_type=-1)
                    elif rep_value == 'neutral':
                        self.exist_check_or_add_posts(Feedback, post_id=post.id, author=post.author.name.lower(),
                                                      receiver=rep_receiver,
                                                      feedback_type=0)
                print("Going to sleep for 1 day")
                time.sleep(self.delay)





if __name__ == '__main__':
    bot = Tracker_Bot()
    bot.main()

