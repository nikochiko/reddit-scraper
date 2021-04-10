import json
import os
from collections import defaultdict
from datetime import datetime

import praw
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

user_agent = "Tres-Commas crypto analysis by twoBit"
reddit = praw.Reddit(
    user_agent=user_agent,
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET")
)

fetch_all_after = datetime(2015, 1, 1)    


def get_word_count_for_str(string):
    if string is None:
        return {}
    words = string.split()
    return { word: words.count(word) for word in words }


def fetch_subreddits():
    return reddit.subreddits.popular(limit=1000)


def fetch_submissions(sub, after=fetch_all_after):
    for submission in sub.new(limit=1000):
        created_date = datetime.fromtimestamp(submission.created_utc)
        created_date = datetime(year=created_date.year, month=created_date.month, day=created_date.day)
        if created_date.timestamp() < fetch_all_after.timestamp():
            return

        yield created_date, submission


def default_count_dict():
    return defaultdict(lambda: 0)


def get_word_count_for_sub(sub):
    count_by_date = defaultdict(default_count_dict)

    submission_no = 0
    for created_date, submission in fetch_submissions(sub):
        submission_no += 1
        print(f"Submission {submission_no}")

        now_dict = count_by_date[created_date.timestamp()]
 
        for word, cnt in get_word_count_for_str(submission.selftext).items():
            now_dict[word] += cnt
        
        submission.comments.replace_more(limit=0)
        for comment in submission.comments:
            for word, cnt in get_word_count_for_str(comment.body).items():
                now_dict[word] += cnt

    return count_by_date


if __name__ == "__main__":
    # datetimes = []
    # for submission in reddit.subreddit("all").stream.submissions():
    #     datetimes.append(datetime.fromtimestamp(submission.created_utc))
    #     if len(datetimes) >= 200:
    #         break
    main_dict = defaultdict(default_count_dict)

    try:
        for subr in fetch_subreddits():
            print(f"On subreddit r/{subr.display_name}")
            word_count_for_sub = get_word_count_for_sub(subr)

            for date, word_count_dict in word_count_for_sub.items():
                now_dict = main_dict[date]
                print(date, word_count_dict)
                for word, cnt in word_count_dict.items():
                    now_dict[word] += cnt

            with open(f"./bot-output-{subr.display_name}.json", "w") as fp:
                json.dump(word_count_for_sub, fp)

            with open("./bot-output.json", "w") as fp:
                json.dump(main_dict, fp)

    except Exception as e:
        with open(f"./bot-output-{subr.display_name}.json", "w") as fp:
            json.dump(word_count_for_sub, fp)
        with open("./bot-output.json", "w") as fp:
            json.dump(main_dict, fp)
        raise e

    with open("./bot-output.json", "w") as fp:
        json.dump(main_dict, fp)
