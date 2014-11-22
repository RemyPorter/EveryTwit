import twitter
import pymarkovchain
import time
import json
import os
import io

class Credentials:
    def __init__(self, filename=".credentials"):
        with open(filename) as f:
            data = json.loads(f.read())
        self.app_name = data["appname"]
        self.consumer_key = data["consumerkey"]
        self.consumer_secret = data["consumersecret"]

    def dance(self, token_file=".token"):
        return twitter.oauth_dance(self.app_name, self.consumer_key, 
            self.consumer_secret, token_file)

    def get_keys(self, token_file=".token"):
        with open(token_file) as f:
            token = f.readline().strip()
            secret = f.readline().strip()
        return (token, secret)

    def sign_in(self, token_file=".token", sign_in_type=twitter.Twitter):
        if not os.path.exists(token_file):
            self.dance(token_file)
        (token, secret) = self.get_keys(token_file)
        auth = twitter.OAuth(token, secret, 
            self.consumer_key, self.consumer_secret)
        return sign_in_type(auth=auth)

class Accumulate:
    def __init__(self, credentials, markov_store=".markov"):
        self.data_store = io.StringIO()
        self.creds = credentials


    def clear_data(self):
        self.data_store = io.StringIO()

    def listen(self, tweet_count=1000):
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
        return self.data_store.getvalue()

    def analyze(self):
        chain = pymarkovchain.MarkovChain()
        chain.generateDatabase(self.data_store.getvalue(), sentenceSep='[\n]')
        return chain

class Tweeter:
    def __init__(self, credentials):
        self.twitter = credentials.sign_in(sign_in_type=twitter.Twitter)
        self.accumulator = Accumulate(credentials)

    def build_tweet(self, chain):
        tweet = chain.generateString()
        next_str = chain.generateString()
        while len(tweet) + len(next_str) < 139:
            tweet += " " + next_str
            next_str = chain.generateString()
        return tweet

    def run_once(self, tweet_count=10000):
        self.accumulator.listen(tweet_count)
        chain = self.accumulator.analyze()
        tweet = self.build_tweet(chain)
        self.twitter.statuses.update(status=tweet[:140])

    def run(self, tweet_count=10000, sleep_between_tweets=15):
        while(True):
            self.run_once(tweet_count)
            time.sleep(sleep_between_tweets*60)

def main():
    c = Credentials()
    twit = Tweeter(c)
    twit.run()

if __name__ == "__main__":
    main()






