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
        
def get_base_language(x):
    for key, val in x.POS.items():
        if val == 'VERB':
            if x.LID[key] == 'hin':
                return 'hin'
    return 'eng'

def calculate_CMI(x):
    return (x.total_words - max(x.Num_Hin, x.Num_Eng))*1.0/x.total_words
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run LID and POS on texts')
    parser.add_argument('--file', type=str,
                        help='File to input data')
    parser.add_argument('--data_source', type=str,
                        help='Input source: Twitter or, YouTube')
    parser.add_argument('--out_file', type=str,
                        help='Path to output data')

    args = parser.parse_args()
    
    if os.path.exists(os.path.dirname(args.out_file)) == False:
        os.makedirs(os.path.dirname(args.out_file))
        
    tokenizer = AutoTokenizer.from_pretrained("sagorsarker/codeswitch-hineng-lid-lince")
    model = AutoModelForTokenClassification.from_pretrained("sagorsarker/codeswitch-hineng-lid-lince")
    if torch.cuda.is_available():
        lid_model = pipeline('ner', model=model, tokenizer=tokenizer, device=0)
    else:
        lid_model = pipeline('ner', model=model, tokenizer=tokenizer)
        
    tokenizer = AutoTokenizer.from_pretrained("sagorsarker/codeswitch-hineng-pos-lince")
    model = AutoModelForTokenClassification.from_pretrained("sagorsarker/codeswitch-hineng-pos-lince")
    if torch.cuda.is_available():
        pos_model = pipeline('ner', model=model, tokenizer=tokenizer, device=0)
    else:
        pos_model = pipeline('ner', model=model, tokenizer=tokenizer)
    
    df_ = pd.read_csv(args.file, sep='\t', error_bad_lines=False, lineterminator='\n').dropna(subset=['text']).reset_index(drop=True)
    df_['text'] = df_.text.apply(lambda x: remove_html(remove_email(clean_tweets(x))))

    if args.data_source.lower() == 'youtube':
        df_['posted_time_in_years'] = df_.time.apply(get_year)
    elif args.data_source.lower() == 'twitter':
        df_.created_at = pd.to_datetime(df_.created_at)
        df_['posted_time_in_years'] = df_.created_at.dt.year
    else:
        raise ValueError("Data source should be youtube or, twitter")
        
    lids = []
    poses = []
    
    for i in tqdm(range(df_.shape[0])):
        lids.append(language_identification(lid_model, df_.text.iloc[i]))
        poses.append(language_identification(pos_model, df_.text.iloc[i]))
        
    df_['LID'] = lids #df_.text.apply(lambda x: language_identification(lid_model, x))
    df_['POS'] = poses #df_.text.apply(lambda x: language_identification(pos_model, x))

    df_['Num_Hin_dev'] = df_.text.apply(lambda x: [detect_language(i) for i in x.split()].count('hindi'))

    df_['total_words'] = df_.LID.apply(lambda x: len(x))
    df_['Num_Hin'] = df_.LID.apply(lambda x: list(x.values()).count("hin"))
    df_['Num_Eng'] = df_.LID.apply(lambda x: list(x.values()).count("en"))

    df_['Perc_Hin'] = df_['Num_Hin']/df_['total_words']
    df_['Perc_Eng'] = df_['Num_Eng']/df_['total_words']
    df_['Perc_Hin_Dev'] = df_['Num_Hin_dev']/df_['total_words']
    df_.to_csv(args.out_file, sep='\t', index=False)
    
    df_['base_language'] = df_.apply(get_base_language, axis=1)
    df_['CMI'] = df_.apply(calculate_CMI, axis=1)
    df_.to_csv(args.out_file, sep='\t', index=False)
    