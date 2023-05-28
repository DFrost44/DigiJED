#!/usr/bin/env python3

import requests
import pandas as pd

r1 = requests.get('https://bank.gov.ua/NBU_Exchange/exchange_site?start=20210101&end=20211231&valcode=eur&sort=exchangedate&order=desc&json')
r2 = requests.get('https://bank.gov.ua/NBU_Exchange/exchange_site?start=20210101&end=20211231&valcode=usd&sort=exchangedate&order=desc&json')

df1 = pd.read_json( r1.text)
df2 = pd.read_json( r2.text)

df = pd.merge(df1,df2,on='exchangedate')
df = df.loc[::-1].reset_index(drop=True)

#print(df)

df.to_csv('./2/data_file.csv')

