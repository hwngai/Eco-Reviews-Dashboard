from app_store_scraper import AppStore
import pandas as pd
import numpy as np
import json
import re
from itunes_app_scraper.scraper import AppStoreScraper

def extract_appStore_info_from_url(apple_url):
    app_info_pattern = r'/([a-zA-Z0-9\-]+)\/id(\d+)'
    gl_pattern = r"https://apps\.apple\.com/([a-z]{2})/app/.*"

    app_info_match = re.search(app_info_pattern, apple_url)
    gl_match = re.search(gl_pattern, apple_url)

    app_name, app_id = app_info_match.groups() if app_info_match else (None, None)
    gl_value = gl_match.group(1) if gl_match else "us"

    return app_name, app_id, gl_value


def fetch_and_reviews(apple_url, country='us', review_limit=200, output_csv='reviews.csv'):
    app_name, app_id, gl_value = extract_appStore_info_from_url(apple_url)

    if app_name is None or app_id is None:
        print("Unable to extract app info from the URL.")
        return

    appStore = AppStore(country=country, app_name=app_name, app_id=app_id)
    appStore.review(how_many=review_limit)

    df = pd.DataFrame(np.array(appStore.reviews), columns=['review'])
    df = df.join(pd.DataFrame(df.pop('review').tolist()))

    name_mapping = {'date': 'at', 'review': 'content', 'rating': 'score', 'developerResponse': 'replyContent'}
    df = df.rename(columns=name_mapping)

    df['thumbsUpCount'] = pd.Series(dtype="float64")
    df['reviewCreatedVersion'] = pd.Series(dtype="float64")

    df = df[['at', 'userName', 'content', 'replyContent', 'score', 'thumbsUpCount', 'reviewCreatedVersion']]

    df.to_csv(output_csv, index=False)
    print(f"Reviews saved to {output_csv}")



apple_url = "https://apps.apple.com/us/app/slack/id618783545"
fetch_and_reviews(apple_url,country = "vn", review_limit =  1000)




apple_url = "https://apps.apple.com/us/app/slack/id618783545"
app_name, app_id, gl_value = extract_appStore_info_from_url(apple_url)

print(app_name, app_id, gl_value)

scraper = AppStoreScraper()
app_details = scraper.get_app_details(app_id, country="vn", lang="vi")
print("get_app_details", app_details)

with open('app_details.json', 'w') as outfile:
    json.dump(app_details, outfile, indent=4)
