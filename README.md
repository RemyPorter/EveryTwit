This Twitter bot scrapes 10,000 tweets off of Twitter, and uses PyMarkovChain to generate the next tweet. It's basically garbage.

Depends on there being a .credentials file which contains a JSON object with the keys "appname", "consumerkey" and "consumersecret", which are your twitter identifiers. It will do the oauth_dance to grant permission for whatever account you choose to use, and store the tokens in a file called .tokens.

Run:

    $ python3 bot.py

The Credentials object is actually probably reusable, and simplifies credential management nicely.