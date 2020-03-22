from helper import *

###---Arxiv---###

def arxiv_section_scraper(section="physics:hep-ex",save_every=10**4):
    '''Scrapes all publications for title,abstract,creation date, and arxiv_id for given section'''
    from time import sleep
    import pandas as pd
    import numpy as np
    import re
    #current_date = time.strftime("%d/%m/%Y")
    #date_sections = [['1991-01-01','2000-12-31'],['2001-01-01','2005-12-31'],
    #                 ['2006-01-01','2010-12-31'],['2011-01-01','2013-12-31'],
    #                 ['2014-01-01','2016-12-31'],['2017-01-01','2017-12-31'],
    #                 ['2018-01-01','2018-12-31'],['2019-01-01','2019-12-31'],
    #                 ['2020-01-01','2020-03-20']]
    def year_to_str_range(a:int):
        str_a = str(a)
        if a<90:
            if len(str_a)==1:
                str_a = '0'+str_a
            return ['20' + str_a+'-01-01','20'+str_a+'-12-31']
        if a>=90:
            return ['19'+str_a+'-01-01','19'+str_a+'-12-31']
    date_sections = [year_to_str_range(a) for a in range(6,21)]
    possible_sections = np.load('Arxiv_sections.npy')
    assert section in list(possible_sections),'Invalid section name'
    query_count = 1
    def article_param_scraper(query,params=['title','abstract','created','id','doi']):
        import numpy as np
        start_sep = '<record>'
        end_sep = '</record>'
        split = query.split(start_sep)
        param_list = []
        for _ in range(len(params)):
            param_list.append([])
        for string in split[1:-1]:
            for idx,param in zip(list(range(len(params))),params):
                value = param_scraper(string,param)
                assert len(value)==1
                if value == []:
                    param_list[idx].append(np.nan)
                else:
                    param_list[idx].append(value[0])
        #special edge case for last query
        for idx,param in zip(list(range(len(params))),params):
            string = split[-1].split(end_sep)[0]
            value = param_scraper(string,param)
            assert len(value)==1
            if value == []:
                param_list[idx].append(np.nan)
            else:
                param_list[idx].append(value[0])
        return param_list
    def param_scraper(query,param='created'):
        start_sep = '<'+param+'>'
        end_sep = '</'+param+'>'
        vals = []
        if param=='resumptionToken':
            split = query.split(end_sep)
            split = split[0].split('">')
            return split[-1]
        split = query.split(start_sep)
        for value in split:
            if end_sep in value:
                vals.append(value.split(end_sep)[0])
        return vals
    df = pd.DataFrame(columns=("title", "abstract", "created","arxiv_id"))
    base_url = 'http://export.arxiv.org/oai2?verb=ListRecords&'
    for date in date_sections:
        url = base_url + 'from='+date[0]+'&until='+date[1]+'&metadataPrefix=arXiv&set='+section
        print(url)
        while True:
            sleep(0.75)
            query = requester(url).text
            if 'noRecordsMatch' in query:
                break
            elif 'Retry' in query:
                #finds how long to sleep based on error message
                sep = query.split('Retry')[1].split('seconds')[0]
                sec= int(re.search(r'\d+', sep).group())
                sleep(sec+1)
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
            df = df.append(pd.DataFrame(contents), ignore_index=True)
            if len(df)>query_count:
                query_count+=save_every
                df.to_csv("tmp")
            next_token = param_scraper(query,'resumptionToken')
            print(next_token)
            if next_token=='':
                break
            url = base_url+'resumptionToken='+next_token
            print(url)
    return df

def all_arxiv_section_scraper():
    import numpy as np
    import time
    possible_sections = np.load('Arxiv_sections.npy')
    for section in possible_sections:
        start = time.clock()
        df = arxiv_section_scraper(section)
        end = time.clock()
        csv_name = section+'_section_scraper.csv'
        df.to_csv(csv_name)
        print(section+' length: '+str(len(df)))
        print(section+' scraping time: '+str(end-start))
        


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

section = 'physics'
df,count = arxiv_section_scraper(section)
print(count)
df.to_pickle(section+'.pkl')