###---Visualization---###
def date_visualization(queries,query_results,graph_filename,csv_filename,month_flag=False,year_flag=True,weight_flag=False,cite_flag=False,database='CrossRef'):
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