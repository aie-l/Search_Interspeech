# Search Interspeech
Uses the Semantic Scholar API to search and download Interspeech papers based on keyword search.

The tool is tested on python 3.9 and is quite slow, as it is doing lookups and reconstruction of URLs from DOIs.

## Use

1. Download the git repository.
2. Install required packages.
3. call ```python search_s2.py --query QUERY```, where QUERY is to be replaced by your query.

### Installing packages
Install packages by running ```pip install --requirements.txt```

### Search options
 --start_year START_YEAR Enter the first year to be included in the search (e.g., 1970).
 
  --end_year END_YEAR   Enter the last year to be included in the search.
  
  --venues VENUES       Enter the venues to be searched through (e.g., `interspeech,IberSPEECH`)
  
  --queries QUERIES [QUERIES ...], -q QUERIES [QUERIES ...]
                        Enter the first query here using the Semantic Scholar API query format.
                        For example, to search for two queries one searching for ASR and English and one
                        for TTS and English write:
                        --queries "ASR + English" "TTS + English"
                        The quotation marks are required to ensure that the query is correctly parsed.

  --fields FIELDS       Enter S2 fields (bulk search) to return (e.g., `title,year,externalIds').
  
  --csv\_name CSV\_NAME   Add the name of the file to save results to.
  
  --download DOWNLOAD   Download the PDFs as well as creating a spreadsheet.
  
  --download\_dir DOWNLOAD\_DIR
                        Directory to store downloaded PDFs to (Make sure that it exists).

