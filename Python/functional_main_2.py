###---Master Function---###
from email import *
from arxiv import *
from crossref import *
from visualization import *
def master_function(f_name,l_name,email,queries,graph_filename,csv_filename,database='CrossRef'):
    queries = [phrase.lstrip() for phrase in queries.split(',')]
    if database=='Crossref':
        query_results = title_query_crossref(queries,cite_flag=False,relev_flag=False)
    elif database=='Arxiv':
        query_results = title_query_arxiv(queries,cite_flag=False,relev_flag=False)
    date_visualization(queries,query_results,database=database,graph_filename=graph_filename,csv_filename=csv_filename)
    send_email('fromaddr',email,f_name,l_name,graph_filename=graph_filename,csv_filename=csv_filename)
    

def timer(queries,database='Arxiv'):
    import time
    if database=='Arxiv':
        start = time.clock()
        query_results,num_query = title_query_arxiv(queries)
        end = time.clock()
        print(num_query)
        print(end-start)
        print((end-start)/sum(num_query))
    elif database=='CrossRef':
        start = time.clock()
        query_results,num_query = title_query_crossref(queries)
        end = time.clock()
        print(num_query)
        print(end-start)
        print((end-start)/num_query)

###---PLOS---###
def title_query_plos(queries,cite_flag=False,relev_flag=False):
    from time import sleep
    import requests
    import json
    from math import ceil
    from urllib.parse import quote_plus
    import numpy as np
    query_results = []
    def date_extract_plos(plos_query):
        dates = [date_extract_plos_2(query['publication_date']) for query in plos_query['response']['docs']]
        weights = np.ones(len(dates))
        return dates,weights
    def date_extract_plos_2(date):
        from datetime import datetime
        return datetime.strptime(date.split('T')[0],'%Y-%m-%d')

    api = quote_plus('o9MBDAVCB8cCBedg_Bhc')
    
    for title in queries:
        url = 'http://api.plos.org/search?q=title:'+title+'&start=0&rows=100&wt=json&fl=publication_date&api_key='+api
        total_dates = []
        total_weights = []
        plos_query = json.loads(requests.get(url,timeout=10).text)
        start=0
        rows=100
        total_results = plos_query['response']['numFound']
        iter = ceil(total_results/rows)
        for _ in range(iter):
            sleep(10)
            plos_query = json.loads(requests.get(url,timeout=10).text)
            dates,weights=date_extract_plos(plos_query)
            total_dates.extend(dates)
            total_weights.extend(weights)
            start+=rows
            url='https:// http://api.plos.org/search?q=title:'+title+'&start='+str(start)+'&rows=100&wt=json&fl=publication_date&api_key='+api
        date_and_weight=np.vstack([total_dates,total_weights])
        df = sort_date_weight(date_and_weight)
        query_results.append(df)
    return query_results

