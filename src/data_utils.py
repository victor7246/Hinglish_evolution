from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
import pandas as pd
from glob import glob
import sys
import re
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import codecs,string
import json
from torch.utils.data import Dataset
import argparse
import torch

def clean_tweets(text):
    text = text.lower()
    text = re.sub(r'@\w+','',text)
    text = re.sub(r'http\w+','',text)
    text = re.sub(r'#\w+','',text)
    text = re.sub(r'\d+','',text)
    return text.strip()

def remove_html(text):
    text = text.replace("\n"," ")
    pattern = re.compile('<.*?>') #all the HTML tags
    return pattern.sub(r'', text)

def remove_email(text):
    text = re.sub(r'[\w.<>]*\w+@\w+[\w.<>]*', " ", text)
    return text

def language_identification(pipeline, text):
    results = pipeline(text)
    languages = {}
    text = ""
    
    for i, val in enumerate(results):
        if val['word'].startswith("##"):
            text += val['word'].replace("##",'')
        else:
            text += val['word']
        
        if i != len(results)-1:
            if results[i+1]['word'].startswith('##') == False:
                text += " "
                #languages.append(results[i]['entity'])
                languages[text.split()[-1]] = results[i]['entity']
        else:
            languages[text.split()[-1]] = results[i]['entity']
    
    return languages        

def detect_language(character):
    maxchar = max(character)
    if u'\u0900' <= maxchar <= u'\u097f':
        return 'hindi'
    else:
        return 'english'
    
def get_year(x):
    l = re.findall(r'\d+ year',x)
    if len(l) > 0:
        return int(l[0].split(' ')[0])
    else:
        return 0