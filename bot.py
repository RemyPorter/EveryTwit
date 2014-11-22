"""This module manages a twitter bot. Run with python3 bot.py"""

import twitter
import pymarkovchain
import time
import json
import os
import io

class Credentials:
    """Wrap the Twitter's OAuth API. Depends on a JSON dict
    in file .credentials, which contains the appname, consumerkey,
    and consumersecret."""
    def __init__(self, filename=".credentials"):
        with open(filename) as f:
            data = json.loads(f.read())
        self.app_name = data["appname"]
        self.consumer_key = data["consumerkey"]
        self.consumer_secret = data["consumersecret"]

    def dance(self, token_file=".token"):
        """Perform the oauth_dance to get user tokens, store them
        in a file .token"""
        return twitter.oauth_dance(self.app_name, self.consumer_key, 
            self.consumer_secret, token_file)

    def get_keys(self, token_file=".token"):
        """Load the tokens from .token file."""
        with open(token_file) as f:
            token = f.readline().strip()
            secret = f.readline().strip()
        return (token, secret)

    def sign_in(self, token_file=".token", sign_in_type=twitter.Twitter):
        """Performs a sign-in, returning an object of sign_in_type.
        Checks for the token file, and if it doesn't exist, does
        the oauth_dance to build it."""
        if not os.path.exists(token_file):
            self.dance(token_file)
        (token, secret) = self.get_keys(token_file)
        auth = twitter.OAuth(token, secret, 
            self.consumer_key, self.consumer_secret)
        return sign_in_type(auth=auth)

class Accumulate:
    """Listens to a TwitterStream, and builds a MarkovChain from the data"""
    def __init__(self, credentials):
        """Credentials object is used to perform the sign-in."""
        self.data_store = io.StringIO()
        self.creds = credentials


    def clear_data(self):
        """Wipe the current data store that we've pulled from
        Twitter."""
        self.data_store = io.StringIO()

    def listen(self, tweet_count=1000):
        """Listen to a Twitter steam, storing the results
        in a StringIO object."""
        self.clear_data()
        stream = self.creds.sign_in(sign_in_type=twitter.TwitterStream)
        iterator = stream.statuses.sample()
        count = 0
        for twit in iterator:
            if len(twit.get("text", "")) > 0:
                self.data_store.write(twit["text"])
                count += 1
            if count >= tweet_count:
                break

    def peek_data(self):
        """The data we've currently swiped from Twitter."""
        return self.data_store.getvalue()

    def analyze(self):
        """Take the data and return a MarkovChain object
        based on it."""
        chain = pymarkovchain.MarkovChain()
        chain.generateDatabase(self.data_store.getvalue(), sentenceSep='[\n]')
        return chain

class Tweeter:
    """Send updates to Twitter, based on Accumulate data."""
    def __init__(self, credentials):
        self.twitter = credentials.sign_in(sign_in_type=twitter.Twitter)
        self.accumulator = Accumulate(credentials)

    def build_tweet(self, chain):
        """Build a tweet. It tries to get as close to 140 characters
        as it can."""
        tweet = chain.generateString()
        next_str = chain.generateString()
        while len(tweet) + len(next_str) < 139:
            tweet += " " + next_str
            next_str = chain.generateString()
        return tweet

    def run_once(self, tweet_count=10000):
        """Scan tweet_count tweets, and then post a single tweet."""
        self.accumulator.listen(tweet_count)
        chain = self.accumulator.analyze()
        tweet = self.build_tweet(chain)
        self.twitter.statuses.update(status=tweet[:140])

    def run(self, tweet_count=10000, sleep_between_tweets=15):
        """Run indefinitely, sleeping between each tweet."""
        while(True):
            self.run_once(tweet_count)
            time.sleep(sleep_between_tweets*60)

def main():
    c = Credentials()
    twit = Tweeter(c)
    twit.run()

if __name__ == "__main__":
    main()






