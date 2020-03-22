import numpy as np
import requests



def arxiv_sections_extract():
    url = 'http://export.arxiv.org/oai2?verb=ListSets'
    query = requests.get(url).text
    start_sep = '<setSpec>'
    end_sep = '</setSpec>'
    #this is number of results per page
    list_spec = []
    split = query.split(start_sep)
    for spec in split:
        if end_sep in spec:
            list_spec.append(spec.split(end_sep)[0])
    return list_spec

Arxiv_sections = np.array(arxiv_sections_extract())
np.save('Arxiv_sections',Arxiv_sections)
