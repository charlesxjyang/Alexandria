###---Master Function---###
def master_function(f_name,l_name,email,queries,database='CrossRef',graph_filename,csv_filename):
    from email import *
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

###---Querying---###
def date_extract_pub(date):
        #maybe just use dateutil for most cases?
    try:
        from dateutil import parser
        return parser.parse(date)
    except:
        from datetime import datetime
        seasons = ['Winter','Summer','Fall','Spring']
        if any(season in date for season in seasons):
            try:
                #sometimes format 2000 Fall
                return datetime.strptime(date.split(' ')[0],'%Y')
            except:
                #sometimes format Ssummer 2017
                return datetime.strptime(date.split(' ')[1], '%Y')

###--Helper Functions---###
def sort_date_weight(date_and_weight):
    '''date_and_weight is numpy array of shape 
    it sorts based on dates, which is the first row, and shuffles around the associated weight for each date as well
    returns a dataframe with index of dates and one column of weights
    '''
    import pandas as pd
    from datetime import date
    sort_by_date = date_and_weight[:,date_and_weight[0,:].argsort(axis=0,kind='mergesort')]
    sort_dates = sort_by_date[0,:]
    sort_weights = sort_by_date[1,:]
    #remove any dates from before the current date
    sort_dates = sort_dates[sort_dates<pd.Timestamp(date.today())]
    sort_weights = sort_weights[:len(sort_dates)]
    df = pd.DataFrame(data=sort_weights,index=sort_dates,columns=['weights'])
    df.index.name='dates'
    return df
def weight_database_checker(database,cite_flag,relev_flag):
    '''Checks that cite_flag,relev_flag are appropriate for given database'''
    if database=='Arxiv':
        assert cite_flag==False, 'Cite flag is not false'
        assert relev_flag==False, 'Relev flag is not false'
        cite_flag=False
        relev_flag=False
        return cite_flag,relev_flag
    return cite_flag,relev_flag
def tick_optimizer(start_year,end_year,optimal_num_ticks=15):
    '''optimize the number/interval of xticks for visualization
    based on an arbitrary cost function
    cost = 0.5*(distance last tick mark is from latest year) + 0.5*(number of ticks - optimal number of ticks)
    we have decided to set optimal_number of ticks at 15
    '''
    #minimize distance between last invl and end_year
    #find optimal number of tick marks
    import numpy as np
    potential_intvls = [1,2,4,5,8,10,15,20,25,30,40,50,75,100]
    year_diff = end_year-start_year
    potential_intvls = [x for x in potential_intvls if x<year_diff]
    #cost 1 is how far away last tick mark will be from end_year
    cost_1 = [x % year_diff for x in potential_intvls]
    num_ticks = [year_diff//x for x in potential_intvls]
    #cost 2 is how far away from optimal num ticks we will have
    cost_2 = [abs(optimal_num_ticks - ticks) for ticks in num_ticks]
    #normalizing
    norm_cost_1 = [(x - np.mean(cost_1))/np.std(cost_1) for x in cost_1]
    norm_cost_2 = [(x - np.mean(cost_2))/np.std(cost_2) for x in cost_2]
    #assume we weight cost_1 and cost_2 the same
    best_idx = np.argmin([sum(x) for x in zip(norm_cost_1,norm_cost_2)])
    return potential_intvls[best_idx]
def requester(url):
    #one issue is slow wifi results in taking more than 15 seconds to load page
    import requests
    from time import sleep
    try:
        query = requests.get(url,timeout=30)
    except ConnectionError as e:
        #trying to handle connectionerrors
        sleep(5)
        print('HANDLING CONNECTION ERROR')
        query = requests.get(url,timeout=30)
        print('CONNECTION ERROR RESOLVED')
    return query
        
###---Arxiv---###
def arxiv_section_scraper(section="physics:hep-ex"):
    '''Scrapes all publications for title,abstract,creation date, and arxiv_id for given section'''
    from time import sleep
    import pandas as pd
    import numpy as np
    #current_date = time.strftime("%d/%m/%Y")
    date_sections = [['1991-01-01','2000-12-31'],['2001-01-01','2005-12-31'],
                     ['2006-01-01','2010-12-31'],['2011-01-01','2013-12-31'],
                     ['2014-01-01','2016-12-31'],['2017-01-01','2017-12-31']]
    possible_sections = np.load('Arxiv_sections.npy')
    assert section in list(possible_sections),'Invalid section name'
    def param_scraper(query,param='created'):
        start_sep = '<'+param+'>'
        end_sep = '</'+param+'>'
        vals = []
        if param=='resumptionToken':
            split = query.split(end_sep)
            split = split[0].split('">')
            return split[1]
        split = query.split(start_sep)
        for value in split:
            if end_sep in value:
                vals.append(value.split(end_sep)[0])
        return vals
    df = pd.DataFrame(columns=("title", "abstract", "created", "id", "doi"))
    base_url = 'http://export.arxiv.org/oai2?verb=ListRecords&'
    for date in date_sections:
        url = base_url + 'from='+date[0]+'&until='+date[1]+'&metadataPrefix=arXiv&set='+section
        print(url)
        while True:
            sleep(0.75)
            query = requester(url).text
            print(query)
            if 'noRecordsMatch' in query:
                break
            elif 'Retry after 10 seconds' in query:
                sleep(11)
                continue
            title = param_scraper(query,'title')
            abstract = param_scraper(query,'abstract')
            created = param_scraper(query,'created')
            arxiv_id = param_scraper(query,'id')
            contents = {'title': title,
                        'abstract': abstract,
                        'created': created,
                        'arxiv_id': arxiv_id,
                        }
            df = df.append(contents, ignore_index=True)
            next_token = param_scraper(query,'resumptionToken')
            print(next_token)
            if next_token==[]:
                break
            url = base_url+'resumptionToken='+next_token
            print(url)
    return df



def title_query_arxiv(queries,section='all',cite_flag=False,relev_flag=False):
    '''Returns all publication dates for given queries'''
    #403 Access denied means we've spammed the arxiv api too much
    from time import sleep
    from math import ceil
    import numpy as np
    import pandas as pd
    cite_flag,relev_flag=weight_database_checker('Arxiv',cite_flag,relev_flag)
    query_results = []
    total_results = []
    possible_sections = np.load('Arxiv_sections.npy')
    assert section in list(possible_sections)+['all'],'not a valid Arxiv Section'
    def date_arxiv_extract(query):
        start_sep = '<published>'
        end_sep = '</published>'
        #this is number of results per page
        dates = []
        split = query.split(start_sep)
        for date in split:
            if end_sep in date:
                dates.append(date_extract_arxiv_2(date.split(end_sep)[0]))
        weights = np.ones(len(dates))
        return dates,weights
    def date_extract_arxiv_2(date):
        from datetime import datetime
        return datetime.strptime(date.split('T')[0],'%Y-%m-%d')
    def regex_totalresults(query):
        import re
        end = query.find('</opensearch:totalResult')
        return int(re.findall('\d+',query[:end])[-1])
    for title in queries:
        start = 0
        max_results = 100
        total_dates = []
        total_weights = []
        base_url = 'http://export.arxiv.org/api/query?search_query='
        for word in title.split(' '):
            base_url+='all:'+word+'&'
        url=base_url+'start='+str(start)+'&max_results='+str(max_results)
        if section!='all':
            url+='&cat='+section
        query = requester(url).text
        total_requests = regex_totalresults(query)
        total_results.append(total_requests)
        iterations = ceil(total_requests//max_results)
        for _ in range(iterations):
            sleep(0.75)
            query = requester(url).text
            dates,weights = date_arxiv_extract(query)
            total_dates.extend(dates)
            total_weights.extend(weights)
            start+=max_results
            url=base_url+'start='+str(start)+'&max_results='+str(max_results)
            if section!='all':
                url+='cat='+section
        date_and_weight=np.vstack([total_dates,total_weights])
        sort_by_date = date_and_weight[:,date_and_weight[0,:].argsort(axis=0,kind='mergesort')]
        sort_dates = sort_by_date[0,:]
        sort_weights = sort_by_date[1,:]
        df = pd.DataFrame(data=sort_weights,index=sort_dates,columns=['weights'])
        df.index.name='dates'
        query_results.append(df)
    return query_results,total_results

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
        header = 'https://api.crossref.org/works?query.title='+title+'&rows=1000&cursor=*'
        current_json = json.loads(requester(header).text)
        total_requests = current_json['message']['total-results'] #probably can have some way to back calculate length of time needed to query to tell user how long to wait
        total_dates=[]
        total_weights=[]
        #already hardcoded number of rows to 1000
        while current_json['message']['items']:
            dates,weights = query_crossref(current_json)
            total_dates.extend(dates)
            total_weights.extend(weights)
            next_header = 'https://api.crossref.org/works?query.title='+title+'&rows=1000&mailto=charlesxjyang@berkeley.edu&cursor='+quote_plus(current_json['message']['next-cursor'])
            print(next_header)
            sleep(0.75)
            current_json = json.loads(requester(next_header).text)
        date_and_weight=np.vstack([total_dates,total_weights])
        df = sort_date_weight(date_and_weight)
        query_results.append(df)
    return query_results,total_requests
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


###---Visualization---###
def date_visualization(queries,query_results,month_flag=False,year_flag=True,database='CrossRef',weight_flag=False,cite_flag=False,graph_filename,csv_filename):
    import numpy as np
    def counts(dates):
        import pandas as pd
        if month_flag==True:
            freq='M'
            date_format='%Y-%m'
        elif year_flag==True:
            freq='AS'
            date_format='%Y'
        daterange = pd.date_range(start=dates.index.min(),end=dates.index.max(),freq=freq)
        daterange = daterange.strftime(date_format=date_format)
        counts = []
        for date in daterange:
            counter = count_and_weight(dates,date)
            counts.append(counter)
        final=pd.DataFrame(index=daterange)
        final['counts']=counts
        return final
    def count_and_weight(df,date):
        count = df[date]
        return sum(count['weights'])
    def title_format(queries,weight_print):
        query_format = ['"'+query+'"' for query in queries]
        title_format = ''
        if len(query_format)==1:
            title_format+=query_format[0]
        elif len(query_format)==2:
            title_format+=query_format[0]+' and '+query_format[1]
        else:
            title_format+='{}, and {}'.format(', '.join(query_format[:-1]), query_format[-1])
        if weight_print:
            title_format+= weight_print
            return title_format
        else:
            return title_format
    def weight_database_print(database,relev_flag=False,cite_flag=False):
        if (relev_flag==True):
            if cite_flag==True:
                weight_print = 'weighted by relevance score and citation count from '+database
            else:
                weight_print = 'weighted by relevance score from '+database
        elif cite_flag!=True:
            weight_print = 'weighted by citation count from '+database
        else:
            weight_print = 'from '+database
        return weight_print
    import matplotlib
    #matplotlib.use('Agg') #prevents anything from printing out
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd
    from matplotlib.ticker import MaxNLocator
    font = {'family' : 'georgia',
        'weight' : 'normal',
        'size'   : 16}
    matplotlib.rc('font', **font)
    fig,ax=plt.subplots(figsize=(25,15))
    years = mdates.YearLocator()
    
    
#    yearsFmt = mdates.DateFormatter('%Y')
#    ax.xaxis.set_major_formatter(yearsFmt)
#    ax.xaxis.set_major_locator(years)
    all_counts=[]
    for dates in query_results:
        all_counts.append(counts(dates))
    all_dates = pd.concat(all_counts,join='outer',axis=1)
    all_dates = all_dates.fillna(0)
    all_dates.columns = queries
    all_dates.index.name = 'Dates'
    assert all_dates.shape[1]==len(queries),'number of labels does not match number of cols'
    for col in range(all_dates.shape[1]):
        plt.plot_date(x=all_dates.index,y=all_dates.iloc[:,col],linestyle='solid',label='"'+queries[col]+'"')
    weight_database_print = weight_database_print(database,month_flag,year_flag)
    if weight_database_print is not None:
        ax.set_ylabel('Number of Publications '+weight_database_print,size=20)
    start, end = ax.get_xlim()
    #only int type on y axis
    fig.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel('Year',size=20)
    ax.set_title('Number of Publications on ' + title_format(queries,weight_database_print),size=24)
    start, end = ax.get_xlim()
    tick_intvl = tick_optimizer(int(all_dates.index[0]),int(all_dates.index[-1]))
    plt.xticks(np.arange(0,len(all_dates.index),tick_intvl),all_dates.index[::tick_intvl])
    #include minor tick marks somehows
    ax.xaxis.set_minor_locator(years)
    plt.legend(loc='best',prop={'size': 18},labelspacing=1.0,borderpad=0.5)
    
    fig.savefig(graph_filename+'.png')
    all_dates.to_csv(csv_filename+'.csv')