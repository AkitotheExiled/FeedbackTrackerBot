import praw
from configparser import ConfigParser
import requests, requests.auth
import re
import numpy as np
import sqlite3




class Tracker_Bot():

    def __init__(self):
        self.user_agent = "FeedbackTrackerBot/V1.5 by ScoopJr"
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

    def find_users_tthread(self, user):
        """ Returns the feedback from user's feedback thread.  If the thread has no feedback comment, it creates one."""
        try:
            user_info = {user: [{'t': None, 'p': None, 'n': None, 'n-': None}]}
            for post in self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair):
                if post.archived:
                    continue
                if str(post.author.name) == user:
                    if not post.comments:
                        return user_info
                    for comment in post.comments:
                        if str(comment.author) != self.user:
                            continue
                        if str(comment.author) == self.user and comment.stickied and 'Feedback' in comment.body:
                                regex_search = self.digit_search(str(comment.body))
                                try:
                                    user_info[user][0]['t'] = regex_search[0]
                                    user_info[user][0]['p'] = regex_search[1]
                                    user_info[user][0]['n'] = regex_search[2]
                                    user_info[user][0]['n-'] = regex_search[3]
                                except Exception as e:
                                    print(e)
                                return user_info
            return user_info
        except Exception as e:
            print('0')


    def find_users(self):
        """Finds the names of individuals who have a feedback tracker thread."""
        no_com = True
        try:
            posts = np.stack(self.reddit.subreddit(self.subreddit).search(query='flair:' + self.flair))
            for post in posts:
                if str(post.author.name) not in self.authors:
                    self.authors.append(str(post.author.name))
                for comment in post.comments:
                    if str(comment.author) == self.user and comment.stickied and 'Feedback' in comment.body:
                        no_com = False
                        break
                    elif str(comment.author) == self.user and not comment.stickied and 'Feedback' in comment.body:
                        no_com = False
                        comment2 = self.reddit.comment(comment.id)
                        comment2.mod.distinguish(how='yes', sticky=True)
                        break
                if no_com:
                    try:
                        db_data = self.query_data_for_user(post.author.name.lower())
                        com_t = db_data[0][0]
                        com_p = db_data[0][1]
                        com_n = db_data[0][3]
                        com_ne = db_data[0][2]
                        def_com = '|Feedback|' + str(com_t) + '||\n|:-|:-|:-|\n|Positive ' + str(
                            com_p) + '|Neutral ' + str(com_n) + '|Negative ' + str(com_ne) + '|'
                        post.reply(def_com)
                        default_com = False
                    except Exception as e:
                        default_com = True
                    else:
                        if default_com:
                            def_com = '|Feedback|0||\n|:-|:-|:-|\n|Positive 0|Neutral 0|Negative 0|'
                            post.reply(def_com)
            return self.authors
        except Exception as e:
            print(e)

    def digit_search(self, string):
        """Searches string for the one digit or more and returns it as a list."""
        regex_search = re.compile(r'\d+').findall(string)
        for item in regex_search:
            if item is None:
                regex_search[item] = 0
        return regex_search

    def search_for_feedback(self, user):
        """ Searchs for the user's feedback and returns the total feedback count."""
        try:
            user_info = {user: [{'t': 0, 'p': 0, 'p': 0, 'n': 0, 'n-': 0}]}
            for post in self.reddit.subreddit(self.subreddit).search(
                    query='title:' + user.lower() + ' NOT author:' + user.lower(), sort='new'):
                if (user.lower() != str(post.author.name).lower()) & (user.lower() in str(post.title).lower()):
                    if 'positive' in str(post.title).lower():
                        user_info[user][0]['p'] += 1
                    if 'negative' in str(post.title).lower():
                        user_info[user][0]['n-'] += 1
                    if 'neutral' in str(post.title).lower():
                        user_info[user][0]['n'] += 1
            user_info[user][0]['t'] = user_info[user][0]['p'] - user_info[user][0]['n-']
            print(user_info)
            return user_info
        except Exception as e:
            print(e)

    def query_data_for_user(self, user):
        db = sqlite3.connect('user_database.sqlite')
        cursor = db.cursor()
        sql = "SELECT total_fb, p_fb, neg_fb, n_fb FROM Users \
              WHERE username='{}'".format(str(user.lower()))
        cursor.execute(sql)
        db_data = cursor.fetchall()
        print(user,db_data)
        return db_data

    def logic_for_database(self, user):
        user_data = self.search_for_feedback(user)
        db_data = self.query_data_for_user(user)
        tt_data = self.find_users_tthread(user)
        try:
            if db_data:
                if int(user_data[user][0]['t']) != int(db_data[0][0]) or int(tt_data[user][0]['t']) != db_data[0][0]:
                    print(str(user) + ' has new feedback.  Updating users feedback now...')
                    if int(user_data[user][0]['t']) > int(db_data[0][0]):
                        self.update_feedback_db(user, user_data)
                        self.update_tracker_redditpost(user, user_data)
                    elif int(db_data[0][0]) > int(user_data[user][0]['t']) and int(db_data[0][0]) > int(tt_data[user][0]['t']):
                        print(str(user) + ' database data does not match their feedback counted on the subreddit for Total Feedback.')
                        print('A feedback post may have been deleted for this user. Their feedback count will always match what is in the database.')
                        self.update_tracker_redditpost(user, db_data)
                if int(user_data[user][0]['t']) == db_data[0][0] and int(tt_data[user][0]['t']) == db_data[0][0]:
                    if int(user_data[user][0]['n']) == db_data[0][3] and int(tt_data[user][0]['n']) == db_data[0][3]:
                        print(str(user) + ' has no new feedback.')
                    else:
                        if int(user_data[user][0]['n']) > int(db_data[0][3]):
                            self.update_feedback_db(user, user_data)
                            self.update_tracker_redditpost(user, user_data)
                        elif int(db_data[0][3]) > int(user_data[user][0]['n']) and int(db_data[0][3]) > int(tt_data[user][0]['n']):
                            print(str(user) + ' databases data doesnt equal the current feedback on the subreddit.')
                            print('A feedback post may have been deleted for this user. Their feedback count will always match what is in the database.')
                            self.update_tracker_redditpost(user, db_data)
                        else:
                            print(str(user) + ' has no new feedback.')

            else:
                print(str(user) + ' was not found in the database.  Adding their feedback in...')
                self.insert_feedback_db(user, user_data)
        except Exception as e:
            print(e)

    def create_table_database(self):
        try:
            db = sqlite3.connect('user_database.sqlite')
            cursor = db.cursor()
            sql_statement = ('''CREATE TABLE IF NOT EXISTS Users (
                                ID INTEGER PRIMARY KEY,
                                username TEXT UNIQUE,
                                total_fb INTEGER DEFAULT 0,
                                p_fb INTEGER DEFAULT 0,
                                neg_fb INTEGER DEFAULT 0,
                                n_fb INTEGER DEFAULT 0);''')
            cursor.execute(sql_statement)
        except Exception as e:
            print(e)

    def update_feedback_db(self, user, user_data):
        user_name = user.lower()
        data = user_data
        db = sqlite3.connect('user_database.sqlite')
        cursor = db.cursor()
        try:
            sql_insert_statement = ('''UPDATE Users 
                                    SET total_fb={}, p_fb={}, neg_fb={}, n_fb={}
                                    WHERE username="{}"''').format(data[user][0]['t'], data[user][0]['p'], data[user][0]['n-'],
                                              data[user][0]['n'], user_name)
            cursor.execute(sql_insert_statement)
            db.commit()
            db.close()
        except Exception as e:
            print(e)

    def insert_feedback_db(self, user, user_data):
        user_name = user.lower()
        data = user_data
        db = sqlite3.connect('user_database.sqlite')
        cursor = db.cursor()
        try:
            sql_state = "INSERT INTO Users (username, total_fb, p_fb, neg_fb, n_fb) VALUES ('{}', {}," \
                        "{}, {}, {});".format(user_name, data[user][0]['t'], data[user][0]['p'], data[user][0]['n-'],
                                              data[user][0]['n'])
            cursor.execute(sql_state)
            print('SQL STATEMENT', sql_state)
            db.commit()
            db.close()
        except Exception as e:
            print('EXCEPTION COMING..')
            print(e)

    def batch_update(self):
        users = self.find_users()
        for user in users:
            self.logic_for_database(user)

    def update_tracker_redditpost(self, user, user_data):
        """ Updates the users feedback by comparing the trade threads feedback and the feedback in the subreddit."""
        print(user_data)
        try:
            com_t = user_data[user][0]['t']
            com_p = user_data[user][0]['p']
            com_n = user_data[user][0]['n']
            com_ne = user_data[user][0]['n-']
            print('Updating ' + str(user) + 's' + ' tracker post.')
        except Exception as e:
            try:
                com_t = user_data[0][0]
                com_p = user_data[0][1]
                com_n = user_data[0][3]
                com_ne = user_data[0][2]
                print('Updating ' + str(user) + 's' + ' tracker post.')
            except Exception as e:
                print(e)

        no_com = True
        for post in self.reddit.subreddit(self.subreddit).search(query=user + ' ' + 'flair:' + self.flair):
            if post.archived:
                continue
            if str(post.author.name).lower() == user.lower():
                for comment in post.comments:
                    if str(comment.author) == self.user and comment.stickied:
                        if self.reddit.submission(post.id).locked:
                            self.reddit.submission(post.id).mod.unlock()
                            body2 = '|Feedback|' + str(com_t) + '||\n|:-|:-|:-|\n|Positive ' + str(
                                com_p) + '|Neutral ' + str(com_n) + '|Negative ' + str(com_ne) + '|'
                            comment.edit(body2)
                            self.reddit.submission(post.id).mod.lock()
                        if not self.reddit.submission(post.id).locked:
                            self.reddit.submission(post.id).mod.lock()




if __name__ == '__main__':
    bot = Tracker_Bot()
    bot.batch_update()

