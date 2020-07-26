import praw
from praw.exceptions import APIException
from configparser import ConfigParser
import requests
from src.database.database import Users, Database
from src.classes.baseclass import RedditBaseClass
from src.classes.logger import Logger
from datetime import datetime
import time


class Scs_Bot(RedditBaseClass):

    def __init__(self):
        super().__init__()
        self.user_agent = "PC:FeedbackTracker Post Assist: V1.2 by /u/ScoopJr" # setting user agent
        print('Starting up...', self.user_agent)
        self.reddit = praw.Reddit(client_id=self.client,
                                  client_secret=self.secret,
                                  password=self.password,
                                  user_agent=self.user_agent,
                                  username=self.user)
        self.ok_flairs = ['sale', 'trade'] # the two flair_text that the bot will look out for in a list
        self.log = Logger()
        self.logger = self.log.logger # Logger().logger Logger class with the attribute logger = getlogger(__name__)
        self.error_delay = 70 # 1 minute and 10 seconds delay incase PRAW gets an APIEXCEPTION FROM REDDIT
        self.subreddit = self.sub_reply

    def get_token(self):
        """ Retrieves token for Reddit API."""
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']


    def get_date_from_utc(self, utc_timestamp):
        post_time = datetime.utcfromtimestamp(int(utc_timestamp)).strftime('%B %Y') # Turns the user join date into a readable format. I.E. 07/19/18 -> July 2018
        #post_time = datetime.strptime(post_time, '%Y-%B')
        return post_time

    def reply_post_with_feedback(self, post):
        reply_template = "* Username: u/{}\n* Join date: {}\n* Post Karma: {}\n* Comment Karma: {} \n* Feedback: {}\n\n[You may view this users feedback here.]({})\n\nThis information does not guarantee a successful sale.  It is for you to use to screen potential sellers."

        tracker_link = 'https://www.reddit.com/r/SportsCardTracker/search/?q={}&restrict_sr=1&sort=new' #prepping the link we will use to display users feedback on the sub
        feedback = None
        try:
            feedback = self.db.session.query(Users).filter_by(name=post.author.name.lower()).first() # Getting the user's feedback from our Users table
        except Exception as e:
            print(e)
        if feedback is not None:
            feedback_val = feedback.total # assigning users total feedback to a value
        else:
            feedback_val = 0 # if the user is none(does not exist) then they have 0 feedback
        print('Replying to post,', post.id)
        reply_text = reply_template.format(post.author.name, self.get_date_from_utc(post.author.created_utc),
                                               post.author.link_karma,
                                               post.author.comment_karma, feedback_val,
                                               tracker_link.format(post.author.name))
        post.reply(reply_text)
    def bot_action(self):
        subreddit = self.reddit.subreddit(self.subreddit)
        do_not_comment = False # False if the bot hasn't replied to a post, True if it already has
        for post in subreddit.stream.submissions(skip_existing=True):
            try:
                do_not_comment = False
                print(f'Searching {self.subreddit} for posts!')
                if post.archived:
                    continue
                for comment in post.comments:
                    if comment.author.name.lower() == self.user.lower():
                        print(f"Comment exists for {comment}, {comment.author.name}")
                        do_not_comment = True
                        break
                if do_not_comment:
                    continue
                else:
                    print(f"Replying to post: {post.title} with name: {post.title}")
                    self.reply_post_with_feedback(post)
            except APIException as exception:
                self.logger.info("Error has occurred within the API", exc_info=True)
                time.sleep(self.error_delay)
                pass





if __name__ == '__main__':
    bot = Scs_Bot()
    bot.bot_action()

