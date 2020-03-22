from helper import *
###---Crossref---###
def title_query_crossref(queries,cite_flag=False,relev_flag=False):
    import numpy as np
    from time import sleep
    import json
    from urllib.parse import quote_plus
    cite_flag,relev_flag=weight_database_checker('CrossRef',cite_flag,relev_flag)
    query_results = []
    def check_print_journal(work):
        """Checks that published-print info available and its a journal article"""
        if ('type' in work) and ('published-print' in work):
            if work['type']=='journal-article':
                return True
        return False
    def date_extract_crossref(work):
        '''date is of format [2003,01,01]'''
        from datetime import datetime
        date = work['published-print']['date-parts'][0]
        if len(date)==1:
            try:
                return datetime(date[0],1,1)
            except:
                
                try:
                    #sometimes have [[0]] for date, substitute online publish date
                    return date_extract_online(work['published-online']['date-parts'][0])
                except:
                    #sometimes have [[0]] for onlien date as well
                    return date_extract_online(work['created']['date-parts'][0])
        elif len(date)==2:
            return datetime(date[0],date[1],1)
        elif len(date)==3:
            try:
                return datetime(date[0],date[1],date[2])
            except:
                #one time got [0,10,24]??
                try:
                    return date_extract_online(work['created']['date-parts'][0])
                except:
                    print('uhoh online date extract didnt work either')
                    print(work['published-print']['date-parts'][0])
        else:
            from dateutils import parser
            try:
                return parser.parse(date)
            except:
                print(date)
    def date_extract_online(online_date_parts):
        from datetime import datetime
        if len(online_date_parts)==1:
            return datetime(online_date_parts[0],1,1)
        elif len(online_date_parts)==2:
            return datetime(online_date_parts[0],online_date_parts[1],1)
        elif len(online_date_parts)==3:
            return datetime(online_date_parts[0],online_date_parts[1],online_date_parts[2])
    def query_crossref(current_json):
        import numpy as np
        dates = [date_extract_crossref(work) for work in current_json['message']['items'] if check_print_journal(work)]
        if (relev_flag==False) and (cite_flag==False):
            weights = np.ones(len(dates))
        elif (relev_flag==True) and (cite_flag==False):
            weights = [work['score'] for work in current_json['message']['items']]
        elif (relev_flag==False) and (cite_flag==True):
            weights = [work['is-referenced-by-count'] for work in current_json['message']['items'] if check_print_journal(work)]
        else:
            weight_1 = np.array([work['is-referenced-by-count'] for work in current_json['message']['items'] if check_print_journal(work)])
            weight_2 = np.array([work['score'] for work in current_json['message']['items'] if check_print_journal(work)])
            weights = list(weight_1*weight_2)
        return dates,weights

    for title in queries:
    #crossref uses deep page cursoring where each cursor points to the next page of results
        header = 'https://api.crossref.org/works?query.bibliographic='+title+'&rows=1000&cursor=*'
        current_json = json.loads(requester(header).text)
        print(current_json)
        total_requests = current_json['message']['total-results'] #probably can have some way to back calculate length of time needed to query to tell user how long to wait
        total_dates=[]
        total_weights=[]
        #already hardcoded number of rows to 1000
        while current_json['message']['items']:
            dates,weights = query_crossref(current_json)
            total_dates.extend(dates)
            total_weights.extend(weights)
            next_header = 'https://api.crossref.org/works?query.bibliographic='+title+'&rows=1000&mailto=charlesxjyang@berkeley.edu&cursor='+quote_plus(current_json['message']['next-cursor'])
            print(next_header)
            sleep(0.75)
            current_json = json.loads(requester(next_header).text)
        date_and_weight=np.vstack([total_dates,total_weights])
        df = sort_date_weight(date_and_weight)
        query_results.append(df)
    return query_results,total_requests
