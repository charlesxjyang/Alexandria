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
        
