from helper import *

def title_query_pubmed(queries,relev_flag=False,cite_flag=False):
    from time import sleep
    import json
    from math import ceil
    import numpy as np
    def date_extract_pub(date):
        import re
        try:
            from dateutil import parser
            return parser.parse(date)
        except:
            seasons = ['Winter','Summer','Fall','Spring']
            #removes all non-numeric characters
            if any(season in date for season in seasons):
                return parser.parse(re.sub("[^0-9]", "", date))
            elif '-' in date:
                #sometimes format like 2017 May-Aug
                #or 2017 Sep - Oct
                return parser.parse(date.split('-')[0])
            elif '/' in date:
                #sometimes format 2017 Jul/Aug
                return parser.parse(date.split('/')[0])
            print(date)
    def check_journal(key):
        #sometiems no pubtype available
        try:
            if esummary_query['result'][key]['pubtype'][0]=='Journal Article':
                return True
            return False
        except:
            return False
    def query_pub(keys):
        """Returns dates and weights for a json file"""
        dates = [date_extract_pub(esummary_query['result'][key]['pubdate']) for key in keys if check_journal(key)]
        weights = np.ones(len(dates))
        return dates,weights

    def search_summary():
        import requests
        import json
        from urllib.parse import quote_plus
        from time import sleep
        summary_query = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?&retmode=json&query_key='+query_key+'&webenv='+quote_plus(web_env)+'&retmax='+str(retmax)+'&retstart='+str(retstart)
        sleep(0.75)
        esummary_query = json.loads(requester(summary_query).text)
        print(summary_query)
        #check if error loading
        while 'result' not in esummary_query:
            print(summary_query)
            esummary_query = json.loads(requester(summary_query).text)
        keys = esummary_query['result']['uids']
        dates,weights = query_pub(keys)
        return dates,weights

    #query certain journal, open access fulltext only, authors,
    query_results = []
    total_results = []
    API = '0d10504be9dfd62f3fc15b0a4fdfc4016009'
    email = 'charlesxjyang@berkeley.edu'
    assert relev_flag==False,"Pubmed has no relevance score"
    assert cite_flag==False,"Pubmed has poor citation database"
    for title in queries:
        #usehistory stores query in server
        #use query_key to specify which set, web_env specifies which environment/server
        #datetype is the date returned, in our case publication date
        #field=title means we only search titles
        retstart=0
        retmax=250
        total_dates = []
        total_weights = []
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term='+title+'&datetype=pdat&field=title&retmax='+str(retmax)+'&retmode=json&usehistory=y&API_key='+API+'&email='+email
        esearch_query = json.loads(requester(url).text)
        query_key = esearch_query["esearchresult"]["querykey"]
        web_env = esearch_query["esearchresult"]['webenv']
        total_requests = int(esearch_query["esearchresult"]['count'])
        total_results.append(total_requests)
        iterations = ceil(total_requests//retmax)
        for _ in range(iterations):
            url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term='+title+'&datetype=pdat&field=title&retmax='+str(retmax)+'&retmode=json&usehistory=y&API_key='+API+'&retstart='+str(retstart)+'&email='+email
            sleep(0.75)
            esearch_query = json.loads(requester(url).text)
            dates,weights = search_summary()
            total_dates.extend(dates)
            total_weights.extend(weights)
            query_key = esearch_query["esearchresult"]["querykey"]
            retstart+=retmax
        date_and_weight=np.vstack([total_dates,total_weights])
        df = sort_date_weight(date_and_weight)
        query_results.append(df)
    return query_results,total_results

