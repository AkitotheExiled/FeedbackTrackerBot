import praw
from configparser import ConfigParser
import requests, requests.auth
import re
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

class Tracker_Bot():

    def __init__(self):
        self.user_agent = "FeedbackTrackerBot/V1.2 by ScoopJr"
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
        self.debug = bool(CONFIG.get('main', 'DEBUG'))



    def get_token(self):
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']

    def find_users(self):
        for post in self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair):
            if post.author.name not in self.authors:
                self.authors.append(post.author.name)
        return self.authors

    def find_users_tthread(self, user):
        user_info = {user: [{'t': None, 'p': None, 'n': None, 'n-': None}]}
        for post in self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair):
            if post.archived:
                continue
            if post.author.name == user:
                if post.comments:
                    for comment in post.comments:
                        if comment.author == self.user and not comment.stickied:
                            comment2 = self.reddit.comment(comment.id)
                            comment2.mod.distinguish(how='yes', sticky=True)
                        if comment.author != self.user and not comment.stickied:
                            if self.reddit.submission(post.id).locked:
                                self.reddit.submission(post.id).mod.unlock()
                            def_com = '|Feedback|0||\n|:-|:-|:-|\n|Positive 0|Neutral 0|Negative 0|'
                            post.reply(def_com)
                            comment.refresh()
                            if not self.reddit.submission(post.id).locked:
                                self.reddit.submission(post.id).mod.lock()
                            continue
                        if comment.author == self.user and comment.stickied:
                            regex_search = re.compile(r'\d+').findall(comment.body)
                            if regex_search is None:
                                regex_search = [0, 0, 0, 0]
                            user_info[user][0]['t'] = regex_search[0]
                            user_info[user][0]['p'] = regex_search[1]
                            user_info[user][0]['n'] = regex_search[2]
                            user_info[user][0]['n-'] = regex_search[3]
                            return user_info
                elif not post.comments:
                    def_com = '|Feedback|0||\n|:-|:-|:-|\n|Positive 0|Neutral 0|Negative 0|'
                    post.reply(def_com)
                    for comment in post.comments:
                        comment.refresh()
                        if comment.author == self.user and not comment.stickied:
                            comment2 = self.reddit.comment(comment.id)
                            comment2.mod.distinguish(how='yes', sticky=True)
                        if comment.author == self.user and comment.stickied:
                            regex_search = re.compile(r'\d+').findall(comment.body)
                            if regex_search is None:
                                regex_search = [0, 0, 0, 0]
                            user_info[user][0]['t'] = regex_search[0]
                            user_info[user][0]['p'] = regex_search[1]
                            user_info[user][0]['n'] = regex_search[2]
                            user_info[user][0]['n-'] = regex_search[3]
                            if not self.reddit.submission(post.id).locked:
                                self.reddit.submission(post.id).mod.lock()
                            return user_info

    def search_for_feedback(self, user):
        try:
            user_info = {user: [{'t': 0, 'p': 0, 'p': 0, 'n': 0, 'n-': 0}]}
            for post in self.reddit.subreddit(self.subreddit).new():
                if (user.lower() != post.author.name.lower()) & (user.lower() in post.title.lower()):
                    if '[positive]' in post.title.lower():
                        user_info[user][0]['p'] += 1
                    if '[negative]' in post.title.lower():
                        user_info[user][0]['n-'] += 1
                    if '[neutral]' in post.title.lower():
                        user_info[user][0]['n'] += 1
            user_info[user][0]['t'] = user_info[user][0]['p'] - user_info[user][0]['n-']
            print(user_info)
            return user_info
        except Exception as e:
            print(e)

    def findall(self, p,s):
        '''FOR DEBUGGING PURPOSES'''
        i = s.find(p)
        while i != -1:
            yield i
            i = s.find(p, i+1)

    def update_user_feedback(self, user):
        old_info = self.find_users_tthread(user)
        new_info = self.search_for_feedback(user)
        if new_info is None:
            new_info = {user: [{'t': 0, 'p': 0, 'p': 0, 'n': 0, 'n-': 0}]}
        if old_info is None:
            old_info = {user: [{'t': 0, 'p': 0, 'p': 0, 'n': 0, 'n-': 0}]}
        if int(old_info[user][0]['t']) != new_info[user][0]['t'] or int(old_info[user][0]['n']) != new_info[user][0]['n']:
            print(user + "'s" + " feedback is updating...")
            print('The bot will automatically update the information for you.')
            com_t = new_info[user][0]['t']
            print('Com_t', com_t)
            com_p = new_info[user][0]['p']
            com_n = new_info[user][0]['n']
            com_ne = new_info[user][0]['n-']
            for post in self.reddit.subreddit(self.subreddit).search(query=user + ' ' + 'flair:' + self.flair):
                if post.archived:
                    continue
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

                        body2 = '|Feedback|'+str(com_t)+'||\n|:-|:-|:-|\n|Positive '+str(com_p)+'|Neutral '+str(com_n)+'|Negative '+str(com_ne)+'|'
                        comment.edit(body2)

        if int(old_info[user][0]['t']) == new_info[user][0]['t']:
            return print(str(user) + ' has no new feedback.')
    def batch_update(self):
        users = self.find_users()
        for user in users:
            self.update_user_feedback(user)

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    bot = Tracker_Bot()
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(bot.batch_update,'interval', id='batch_id_001', minutes=2)
    input('The bot is running in the background. Press enter to exit.')
    scheduler.shutdown()



