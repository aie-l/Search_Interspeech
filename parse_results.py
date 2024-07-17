import os
import csv
import json
import pydoi
import requests
from tqdm import tqdm
from argparse import ArgumentParser


def search_s2(
    query: list,
    fields: list,
    year: int = 1987,
    max_results: int = 20000,
    venue: str = "Interspeech",
    **kwargs,
):
    """Search Semantic scholar for papers."""

    # Ensure ExternalIds (contain DOI) is always the last element.
    if 'externalIds' not in fields:
        fields.append('externalIds')
    elif 'ExternalIds' in fields:
        fields.pop('ExternalIds')
    fields.append('ExternalIds')

    fields = ",".join(fields) if len(fields) > 1 else fields
    query = ",".join(query) if len(query) > 1 else query
    url = f"http://api.semanticscholar.org/graph/v1/paper/search/bulk?query={query}&fields={','.join(fields)}&year={year}-&venue={venue}&limit={max_results}"
    r = requests.get(url).json()
    collected = 0

    print(f"Will retrieve an estimated {r['total']} documents")

    while True:
        if "data" in r:
            for paper in tqdm(r["data"]):
                res = {key: paper.get(key) for key in fields}
                collected += 1
                yield res

        if "token" not in r:
            break
    r = requests.get(f"{url}&token={r['token']}").json()
    print(f"Done!\n{collected} papers retrieved.")


def extract_doi(paper):
    try:
        return paper["externalIds"]["DOI"]
    except KeyError:
        return False


def extract_url(doi):
    """Use the DOI to get the actual URL for the publication."""
    resp = pydoi.get_url(doi)
    return resp


def parse_url(url):
    """Parse URL into the link for the PDF."""
    if "arxiv" in url:
        url = url.replace("abs", "pdf")
        url = f"{url}.pdf"
    elif "isca-archive" in url:
        url = url.replace("html", "pdf")
    return url


def download_pdf(url, out_dir):
    """Download the PDF in a given url."""
    f_name = url.split("/")[-1]
    path = f"{out_dir}/{f_name}"

    try:
        resp = requests.get(url)
        with open(path, "wb") as file:
            file.write(resp.content)
        return True
    except Exception:
        return False


def write_tsv(results, fields, header=False, out_file='results.tsv'):
    """Write the results to a tab separated file."""
    with open(out_file, 'a', encoding='utf-8') as outf:
        writer = csv.writer(outf, delimter = '\t')
        if header:
            writer.writerow(header)

        if 'error' not in fields:
            fields.append('error')
        if 'query' not in fields:

        for paper in results:











def main():
    parser = ArgumentParser(description="A commandline script to search for and download papers from one or more venues from the ISCA archives using Semantic Scholar.")
    parser.add_argument("--year", type=int, desc="Enter the first year to be included in the search.", default=1970)
    parser.add_argument("--venues", type=str, desc="Enter the venues to be searched through (e.g., `interspeech,IberSPEECH`)", default="interspeech")
    parser.add_argument("--max_results", type=int, desc="Enter the maximum number of results to return.", default=20000)
    parser.add_argument("--query", "-q", desc="Enter the query here following the Semantic Scholar API query format.", required=True)
    parser.add_argument("--fields", desc="Enter the SemanticScholar API fields (bulk search) to return for each record (e.g., `title,year,venue,externalIds' -- `externalIds' is required).", default="title,year,externalIds,venue,openAccessPdf")
    parser.add_argument("--download", desc="Download the PDFs as well as creating a spreadsheet.", default=True)
    parser.add_argument("--download_dir", desc="Directory to store downloaded PDFs to", default="pdfs/")
    args = parser.parse_args()

    fields = args.fields.split(',')
    if 'externalIds' not in fields:
        fields.append('externalIds')
        args.fields = ",".join(fields)

    search_results = search_s2(**args)
    results = []

    for paper in search_results:
        paper = search_results.pop(paper)
        paper['errors'] = []

        # Extract DOI
        doi = extract_doi(paper)
        if doi:
            # Get the URL
            url = extract_url(doi)
            pdf_link = parse_url(url)

            if args.download:
                pdf = download_pdf(pdf_link, args.download_dir)
                if not pdf:
                    paper['errors'].append("PDF Download")
        else:
            paper['errors'].append("DOI Lookup")

        results.append(paper)











def write_csv(info_dict):
    with open("paper_extracted_info.csv", "w", encoding="utf-8") as outfile:
        csvwriter = csv.writer(outfile)
        csvwriter.writerow(
            [
                "doi",
                "tile",
                "year",
                # "emotion sentences",
                # "valence sentences",
                # "arousal sentences",
                # "para sentences",
                "tool" "url",
                "pdf",
                "text",
                "downloaded",
            ]
        )

        for doi, info in info_dict.items():
            row = [doi] + [
                info["title"],
                info["year"],
                # ";".join(info["emotion"]),
                # ";".join(info["valence"]),
                # ";".join(info["arousal"]),
                # ";".join(info["paralinguistics"]),
                info["url"],
                info["pdf"],
                info["text"],
                info["extracted"],
            ]
            csvwriter.writerow(row)


if __name__ == "__main__":
    pass
    # 0. Pull papers
    # get_references("")
    # 1. Extract DOIs
    # dois = extract_dois("papers.jsonl", "dois")
    # 2. Extract URLs (this is slow, can be sped up using multiprocessing.
    # extract_urls(dois, "urls")
    # 3. Download PDFs (this is slow, can be sped up using multiprocessing.
    # download_pdfs("urls.txt", None, "papers/")
    # 4. Run the pdf to text extraction script on the commandline.
    # 5. Extract all papers with a particular pattern.
