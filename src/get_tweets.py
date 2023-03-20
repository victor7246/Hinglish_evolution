import os
from dotenv import load_dotenv
import tweepy as tw
import pandas as pd

from datetime import timedelta, datetime
from ratelimit import limits
import requests

import json
import time
# importing module
import logging

from tqdm import tqdm
import argparse

assert load_dotenv() == True

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def connect_to_endpoint(url, headers, params):
    response = requests.request("GET",
                                search_url,
                                headers=headers,
                                params=params)
    
    if response.status_code == 429:#exhausted API Limit
        a = int(response.headers["Retry-After"])
        print("Waiting for {} seconds".format(a))
        time.sleep(a)
        response = requests.request("GET", search_url, headers=headers, params=params)
        
    if response.status_code != 200:#Status code == 200 implies success in retriving, anything else implies some error.
        print(response.status_code)
        raise Exception(response.status_code, response.text)
    return response.json()

def main(start_date, end_date, topic, lang, max_results=50):
        headers = create_headers(bearer_token)
        # Replace with conversation ID below (Tweet ID of the root Tweet)
        query_params = {
            #'query': 'conversation_id:{}'.format(conversation_id),
            'query': '({}) has:geo place_country:IN (place:delhi OR place:mumbai)'.format(topic), #lang:{} #'government (indian) OR politics (indian) lang:hi', #
            'tweet.fields': 'id,text,author_id,created_at,lang,public_metrics,in_reply_to_user_id,geo',
            'start_time': start_date+'T00:00:00Z', #'2010-01-01T00:00:00Z',
            'end_time': end_date+'T00:00:00Z', #'2011-01-25T00:00:00Z',
            'max_results': max_results}
        json_response = connect_to_endpoint(search_url, headers, query_params)
        return json_response
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get historical tweets')
    parser.add_argument('--query', type=str,
                        help='Query expression for tweet search')
    parser.add_argument('--out_file', type=str,
                        help='Path for output file')

    args = parser.parse_args()
    
    if os.path.exists(os.path.dirname(args.out_file)) == False:
        os.makedirs(os.path.dirname(args.out_file))
        
    # Replace your own bearer token below from the academic research project in the Twitter developer portal
    bearer_token = os.environ['bearer_token']

    # Archive search endpoint - crucial for searching older tweets; ensure you are using this and not the "recent search" endpoint
    search_url = "https://api.twitter.com/2/tweets/search/all"

    json_response = {'data':[]}
    topic = args.query #'government OR politics'
    lang = 'en'
    start_date = datetime(2011, 1, 1)
    time_delta = (datetime.today()-start_date).days

    for i in tqdm(range(time_delta)): #range(time_delta)
        end_date = start_date + timedelta(days=1)
        
        try:
            sample_json = main(start_date = datetime.strftime(start_date, "%Y-%m-%d"), \
                                end_date = datetime.strftime(end_date, "%Y-%m-%d"), \
                                topic = topic, \
                                lang = lang)
        except:
            sample_json = {}
            
        if 'data' in sample_json:
            if i == 0:
                json_response = sample_json
            else:
                json_response['data'] += sample_json['data']

        start_date = start_date + timedelta(days=1)

        time.sleep(4)
    
    if 'data' in json_response:
        if len(json_response['data']) > 0:
            tweets_df = pd.DataFrame.from_dict(json_response['data'])
            tweets_df = tweets_df.rename(columns={'author_id':'author'})
            tweets_df['topic'] = args.query
            tweets_df.to_csv(args.out_file, sep='\t', index=False)