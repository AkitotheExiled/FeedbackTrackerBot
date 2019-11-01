import praw
from configparser import ConfigParser
import requests, requests.auth
import re
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import numpy as np
import datetime


class Tracker_Bot():

    def __init__(self):
        self.user_agent = "FeedbackTrackerBot/V1.3 by ScoopJr"
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


    def get_token(self):
        """ Retrieves token for Reddit API."""
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']

    def find_users(self):
        """Finds the names of individuals who have a feedback tracker thread."""
        try:
            posts = np.stack(self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair))
            for post in posts:
                if post.author.name not in self.authors:
                    self.authors.append(post.author.name)
            return self.authors
        except Exception as e:
            print(e)


    def find_users_tthread(self, user):
        """ Returns the feedback from user's feedback thread.  If the thread has no feedback comment, it creates one."""
        try:
            user_info = {user: [{'t': None, 'p': None, 'n': None, 'n-': None}]}
            for post in self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair):
                if post.archived:
                    continue
                if post.author.name == user:
                    if not post.comments:
                        def_com = '|Feedback|0||\n|:-|:-|:-|\n|Positive 0|Neutral 0|Negative 0|'
                        post.reply(def_com)
                        for comment in post.comments:
                            if comment.author != self.user:
                                continue
                            if comment.author == self.user:
                                if not comment.stickied:
                                    comment2 = self.reddit.comment(comment.id)
                                    comment2.mod.distinguish(how='yes', sticky=True)
                                if comment.stickied:
                                    regex_search = re.compile(r'\d+').findall(comment.body)
                                    for item in regex_search:
                                        if item is None:
                                            regex_search[item] = 0
                                    try:
                                        user_info[user][0]['t'] = regex_search[0]
                                        user_info[user][0]['p'] = regex_search[1]
                                        user_info[user][0]['n'] = regex_search[2]
                                        user_info[user][0]['n-'] = regex_search[3]
                                    except Exception as e:
                                        print(e)
                                    if not self.reddit.submission(post.id).locked:
                                        self.reddit.submission(post.id).mod.lock()
                                    return user_info
                    if post.comments:
                        no_fb_com = False
                        for comment in post.comments:
                            if comment.author == self.user:
                                if comment.stickied & ('feedback' in comment.body.lower()):
                                    regex_search = re.compile(r'\d+').findall(comment.body)
                                    for item in regex_search:
                                        if item is None:
                                            regex_search[item] = 0
                                    try:
                                        user_info[user][0]['t'] = regex_search[0]
                                        user_info[user][0]['p'] = regex_search[1]
                                        user_info[user][0]['n'] = regex_search[2]
                                        user_info[user][0]['n-'] = regex_search[3]
                                    except Exception as e:
                                        print(e)
                                    return user_info
                                if not comment.stickied & ('feedback' in comment.body.lower()):
                                    comment2 = self.reddit.comment(comment.id)
                                    comment2.mod.distinguish(how='yes', sticky=True)
                                    regex_search = re.compile(r'\d+').findall(comment.body)
                                    for item in regex_search:
                                        if item is None:
                                            regex_search[item] = 0
                                    try:
                                        user_info[user][0]['t'] = regex_search[0]
                                        user_info[user][0]['p'] = regex_search[1]
                                        user_info[user][0]['n'] = regex_search[2]
                                        user_info[user][0]['n-'] = regex_search[3]
                                    except Exception as e:
                                        print(e)
                                    return user_info
                        no_fb_com = True
                        if no_fb_com:
                            if self.reddit.submission(post.id).locked:
                                self.reddit.submission(post.id).mod.unlock()
                            def_com = '|Feedback|0||\n|:-|:-|:-|\n|Positive 0|Neutral 0|Negative 0|'
                            post.reply(def_com)
                            if not self.reddit.submission(post.id).locked:
                                self.reddit.submission(post.id).mod.lock()
        except Exception as e:
            print(e)

    def search_for_feedback(self, user):
        """ Searchs for the user's feedback and returns the total feedback count."""
        try:
            user_info = {user: [{'t': 0, 'p': 0, 'p': 0, 'n': 0, 'n-': 0}]}
            for post in self.reddit.subreddit(self.subreddit).search(
                    query='title:' + user.lower() + ' NOT author:' + user.lower(), sort='new'):
                if (user.lower() != post.author.name.lower()) & (user.lower() in post.title.lower()):
                    if 'positive' in post.title.lower():
                        user_info[user][0]['p'] += 1
                    if 'negative' in post.title.lower():
                        user_info[user][0]['n-'] += 1
                    if 'neutral' in post.title.lower():
                        user_info[user][0]['n'] += 1
            user_info[user][0]['t'] = user_info[user][0]['p'] - user_info[user][0]['n-']
            print(user_info)
            return user_info
        except Exception as e:
            print(e)

    def findall(self, p, s):
        '''FOR DEBUGGING PURPOSES'''
        i = s.find(p)
        while i != -1:
            yield i
            i = s.find(p, i + 1)

    def update_user_feedback(self, user):
        """ Updates the users feedback by comparing the trade threads feedback and the feedback in the subreddit."""
        old_info = self.find_users_tthread(user)
        new_info = self.search_for_feedback(user)
        if int(old_info[user][0]['t']) != new_info[user][0]['t'] or int(old_info[user][0]['n']) != new_info[user][0][
            'n']:
            print(user + "'s" + " feedback is updating...")
            print('The bot will automatically update the information for you.')
            com_t, com_p, com_n, com_ne = new_info[user][0]['t'], new_info[user][0]['p'], new_info[user][0]['n'], \
                                          new_info[user][0]['n-']
            print(com_t, com_p, com_n, com_ne)
            for post in self.reddit.subreddit(self.subreddit).search(query=user + ' ' + 'flair:' + self.flair):
                if post.archived:
                    continue
                if post.author.name.lower() == user.lower():
                    for comment in post.comments:
                        if comment.author == self.user and comment.stickied:
                            if self.debug:
                                body = comment.body
                                # body2 = list(body)
                                regex = re.compile(r'\d+').findall(body)
                                # print(regex[0], regex[1], regex[2], regex[3])
                                for match in re.finditer(regex[0], body):
                                    print('DEBUG: Feedback 1 Position', match.start(), match.end())
                                    # body2[match.start():match.end()] = str(com_t)

                                for match in re.finditer(regex[1], body):
                                    print('DEBUG: Feedback 2 Position', match.start(), match.end())
                                    # body2[match.start():match.end()] = str(com_p)

                                for match in re.finditer(regex[2], body):
                                    print('DEBUG: Feedback 3 Position', match.start(), match.end())
                                    # body2[match.start():match.end()] = str(com_n)

                                for match in re.finditer(regex[3], body):
                                    print('DEBUG: Feedback 4 Position', match.start(), match.end())
                                    # body2[match.start():match.end()] = str(com_ne)
                                # body2 = "".join(body2)

                            body2 = '|Feedback|' + str(com_t) + '||\n|:-|:-|:-|\n|Positive ' + str(
                                com_p) + '|Neutral ' + str(com_n) + '|Negative ' + str(com_ne) + '|'
                            comment.edit(body2)

        if int(old_info[user][0]['t']) == new_info[user][0]['t']:
            return print(str(user) + ' has no new feedback.')


    def batch_update(self):
        """Loops through users with trade feedback threads and runs update_user_feedback"""
        users = self.find_users()
        for user in users:
            self.update_user_feedback(user)


if __name__ == '__main__':
    bot = Tracker_Bot()
    if bot.debug:
        logging.basicConfig()
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    scheduler = BackgroundScheduler()
    @scheduler.scheduled_job('interval',id='batch_job', minutes=3)
    def run_program():
        bot.batch_update()
    scheduler.start()
    scheduler.get_job(job_id='batch_job').modify(next_run_time=datetime.datetime.now())
    #scheduler.add_job(run_program, 'interval', id='batch_id_001', minutes=3, next_run_time=datetime.datetime.now())
    input('The bot is running in the background. The bot will run every 3 minutes. Press enter to exit.')
    scheduler.shutdown()


