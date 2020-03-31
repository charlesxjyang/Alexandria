# From https://github.com/JohnGiorgi/biorxiv-scraper

__all__ = ['bioRxivScraper']

# Cell
import re
from typing import Dict
from typing import List
from typing import Union

import requests
from tqdm import trange

from bs4 import BeautifulSoup as bs

# Cell
class bioRxivScraper():
    """A simple class for scraping articles and their metadata from bioRxiv."""
    def __init__(self):
        url_advanced_search_base = "https://www.biorxiv.org/search/%20jcode%3Abiorxiv"
        # F-formatted string for advanced search querys
        url_advanced_search_params = ("%20subject_collection_code%3A{0}%20"
                                      "limit_from%3A{1}-{2}-01%20limit_to%3A{1}-{3}-01%20"
                                      # Choose an extremely large num to fit all results on on page
                                      "numresults%3A100000")

        self.url_advanced_search = url_advanced_search_base + url_advanced_search_params
        # F-formatted string for direct (i.e. via the doi) search querys
        self.url_direct_link_base = 'https://www.biorxiv.org/{0}'
        # TODO (John): It may be better to scrape this from the bioRxiv homepage, that way it remains up-to-date
        # For now, hardcoding is an OK alternative
		# Updated by Charles
        self.subject_areas = [
            "Animal Behavior and Cognition", "Biochemistry", "Bioengineering", "Bioinformatics", "Biophysics",
            "Cancer Biology", "Cell Biology", "Clinical Trials", "Developmental Biology", "Ecology", "Evolutionary Biology","Epidemiology",
            "Genetics", "Genomics", "Immunology", "Microbiology", "Molecular Biology", "Neuroscience",
            "Paleontology", "Pathology", "Pharmacology and Toxicology", "Physiology", "Plant Biology",
            "Scientific Communication and Education", "Synthetic Biology", "Systems Biology", "Zoology"
        ]

    def by_year(self, start_year: int, end_year: int = None, subject_areas: Union[str, List] = None) -> Dict:
        """Returns a dictionary keyed by doi, that contains the data/metadata of all articles uploaded
        between `start_year` and `end_year` for a given `subject_area`.
        Args:
            subject_area (str):
        """
        end_year = start_year if end_year is None else end_year

        if subject_areas is not None:
            if isinstance(subject_areas, str):
                subject_areas = [subject_areas]
            for sa in subject_areas:
                if sa not in self.subject_areas:
                    raise ValueError(f'subject_area must be one of {self.subject_areas}. Got {subject_areas}.')
        else:
            subject_areas = self.subject_areas

        scraped_content = {}

        for subject_area in subject_areas:
            url_encoded_subject_area = self._url_encode_subject_area(subject_area)
            for year in range(start_year, end_year + 1):
                for month in trange(1, 13,
                    unit='month',
                    desc=f"Scraping subject area: {subject_area}",
                    dynamic_ncols=True
                ):
                    resp = self._advanced_search(subject_area, year, month)
                    html = bs(resp.text, features="html.parser")

                    articles = html.find_all('li', attrs={'class': 'search-result'})
                    for article in articles:
                        article_content = self._extract_content_from_article(article)

                        if any(content is None for content in article_content.values()):
                            continue

                        resp = self._direct_search(article_content["content_id"])
                        html = bs(resp.text, features="html.parser")

                        abstract = html.find("p", attrs={"id": re.compile(r"p-\d+")})

                        if abstract is None:
                            continue
                        abstract = abstract.text.strip()

                        # Collect year / month / title information
                        # TODO (John): Can we scrape the published date, and add only
                        # one field here: "data_published"
                        scraped_content[article_content["doi"]] = {
                            'month': month,
                            'year': year,
                            'title': article_content["title"],
                            'abstract': abstract,
                            'subject_area': subject_area,
                            'authors': article_content["authors"],
                        }

        return scraped_content

    def _url_encode_subject_area(self, subject_area: str) -> str:
        return '%20'.join(subject_area.split(' '))

    def _advanced_search(self, subject_area: str, year: int, month: int):
        subject_area = self._url_encode_subject_area(subject_area)
        resp = requests.post(self.url_advanced_search.format(subject_area, year, month, month + 1))
        resp.raise_for_status()
        return resp

    def _direct_search(self, content_id: str):
        resp = requests.post(self.url_direct_link_base.format(content_id))
        resp.raise_for_status()
        return resp

    def _extract_content_from_article(self, article):
        """Given an `article` (the html representation of an article scraped from bioRxiv),
        returns a dictionary containing important data and meta data (e.g. the title, authors and doi)."""
        linked_title =  article.find('a', attrs={'class': 'highwire-cite-linked-title'})
        if linked_title is not None:
            content_id = linked_title['href'].strip()
            doi = '/'.join(content_id.split('/')[-2:])[:-2]
            title = linked_title.find('span', attrs={'class': 'highwire-cite-title'})
            if title is not None:
                title = title.text.strip()
        else:
            content_id, doi, title = None, None, None
        authors = article.find_all('span', attrs={'class': 'highwire-citation-author'})
        authors = [author.text.strip() for author in authors]

        return {"content_id": content_id, "doi": doi, "title": title, "authors": authors}