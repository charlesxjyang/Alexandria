from helper import *


###---PLOS---###
def title_query_plos(queries,cite_flag=False,relev_flag=False):
    from time import sleep
    from math import ceil
    import json
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
        plos_query = json.loads(requester(url).text)
        start=0
        rows=100
        total_results = plos_query['response']['numFound']
        iterations = ceil(total_results/rows)
        for _ in range(iterations-1):
            sleep(10)
            plos_query = json.loads(requester(url).text)
            dates,weights=date_extract_plos(plos_query)
            total_dates.extend(dates)
            total_weights.extend(weights)
            start+=rows
            url='http://api.plos.org/search?q=title:'+title+'&start='+str(start)+'&rows=100&wt=json&fl=publication_date&api_key='+api
        date_and_weight=np.vstack([total_dates,total_weights])
        df = sort_date_weight(date_and_weight)
        query_results.append(df)
    return query_results,total_results

