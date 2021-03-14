import os
import signal
from datetime import datetime

# Reddit api library
import praw

# global program flag
program_flag = False


def run():
    # turn on the program flag
    global program_flag
    program_flag = True

    # program kill switch
    def signal_handler(number, frame):
        global program_flag
        program_flag = False

    # kill signal handler
    signal.signal(signal.SIGTERM, signal_handler)

    # setup PRAW (Reddit)
    print("Initialize PRAW (Reddit)...")
    reddit = praw.Reddit(
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        user_agent=os.environ['USER_AGENT']
    )
    reddit.read_only = True

    print("searching comments from reddit r/all via reddit.subreddit.stream...")
    subreddit = reddit.subreddit("all")

    # for calculating runtime
    start_time = datetime.now()
    delta = 0

    # open reddit comment stream
    generator = subreddit.stream.comments()
    for comment in generator:

        # calculate runtime
        delta = (datetime.now() - start_time)

        # if command to quit is set at some point
        if not program_flag:

            # close the stream
            print("Closing subreddit comment stream...")
            generator.close()

        # make words in comments lowercase for comparison
        print("comment_body")

    print("Closing database connection...")
    print("Total runtime: " + str(delta))


if __name__ == '__main__':
    run()
