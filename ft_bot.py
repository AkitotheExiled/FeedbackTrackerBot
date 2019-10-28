import praw
from configparser import ConfigParser
import requests, requests.auth
import re


class Tracker_Bot():

    def __init__(self):
        self.user_agent = "FeedbackTrackerBot/V1.0 by ScoopJr"
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
                if user in post.title:
                    if '[Positive]' in post.link_flair_text:
                        user_info[user][0]['p'] += 1
                    if '[Negative]' in post.link_flair_text:
                        user_info[user][0]['n-'] += 1
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
        if int(old_info[user][0]['t']) == new_info[user][0]['t']:
            return print(str(user) + ' has no new feedback.')
        if int(old_info[user][0]['t']) != new_info[user][0]['t']:
            print('This ' + user + ' has a feedback discrepency.')
            print('I highly recommend you manually review and correct it.  However, would you like the bot to fix it automatically? \n Please type yes or no to continue.')
            reply = input()
            if reply in ['yes', 'y', 'es', 'yea','yeah']:
                com_t = new_info[user][0]['t']
                com_p = new_info[user][0]['p']
                com_n = new_info[user][0]['n']
                com_ne = new_info[user][0]['n-']
                for post in self.reddit.subreddit(self.subreddit).search(query=user + ' ' + 'flair:' + self.flair):
                    if post.archived:
                        continue
                    for comment in post.comments:
                        if comment.author == self.user and comment.stickied:
                            body = comment.body
                            body2 = list(body)
                            regex = re.compile(r'\d+').findall(body)
                            # print(regex[0], regex[1], regex[2], regex[3])
                            for match in re.finditer(regex[0], body):
                                print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #', match.start(), match.end())
                                body2[match.start():match.end()] = str(com_t)
                            for match in re.finditer(regex[1], body):
                                print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #', match.start(), match.end())
                                body2[match.start():match.end()] = str(com_p)
                            for match in re.finditer(regex[2], body):
                                print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #', match.start(), match.end())
                                body2[match.start():match.end()] = str(com_n)
                            for match in re.finditer(regex[3], body):
                                print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #', match.start(), match.end())
                                body2[match.start():match.end()] = str(com_ne)
                            '''
                            body2[10] = str(com_t)
                            body2[35] = str(com_p)
                            body2[45] = str(com_n)
                            body2[56] = str(com_ne)
                            '''
                            body2 = "".join(body2)
                            comment.edit(body2)
            if reply in ['no', 'nah', 'n', 'na']:
                return print(user, 'needs a manual review on their feedback tracker. \n If you believe this to be an error plesae contact github.com/AkitoTheExiled for bot assistance.')
        else:
            com_t = int(old_info[user][0]['t']) + new_info[user][0]['t']
            com_p = int(old_info[user][0]['p']) + new_info[user][0]['p']
            com_n = int(old_info[user][0]['n']) + new_info[user][0]['n']
            com_ne = int(old_info[user][0]['n-']) + new_info[user][0]['n-']
            for post in self.reddit.subreddit(self.subreddit).search(query=user + ' ' + 'flair:' + self.flair):
                if post.archived:
                    continue
                for comment in post.comments:
                    if comment.author == self.user and comment.stickied:
                        body = comment.body
                        body2 = list(body)
                        regex = re.compile(r'\d+').findall(body)
                        #print(regex[0], regex[1], regex[2], regex[3])
                        for match in re.finditer(regex[0], body):
                            print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #',match.start(), match.end())
                            body2[match.start():match.end()] = str(com_t)
                        for match in re.finditer(regex[1], body):
                            print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #',match.start(), match.end())
                            body2[match.start():match.end()] = str(com_p)
                        for match in re.finditer(regex[2], body):
                            print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #',match.start(), match.end())
                            body2[match.start():match.end()] = str(com_n)
                        for match in re.finditer(regex[3], body):
                            print('THESE NUMBERS CORRESPOND TO THE FEEDBACK #',match.start(), match.end())
                            body2[match.start():match.end()] = str(com_ne)
                        print(body2)
                        '''
                        body2[10] = str(com_t)
                        body2[35] = str(com_p)
                        body2[45] = str(com_n)
                        body2[56] = str(com_ne)
                        '''
                        body2 = "".join(body2)
                        comment.edit(body2)

    def batch_update(self):
        users = self.find_users()
        for user in users:
            self.update_user_feedback(user)

if __name__ == '__main__':
    bot = Tracker_Bot()
    bot.batch_update()

