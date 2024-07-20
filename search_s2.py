import os
import csv
import pydoi
import requests
import argparse
from tqdm import tqdm
from typing import List


def extract_url(paper):
    """Get URL for paper. Give preference to DOI."""
    if "DOI" in paper["externalIds"].keys():
        resolved = pydoi.get_url(paper["externalIds"]["DOI"])
        return resolved if resolved else paper["url"]
    elif "ArXiv" in paper["externalIds"].keys():
        arxiv_idx = paper["externalIds"]["ArXiv"]
        return f"https://arxiv.org/abs/{arxiv_idx}"
    else:
        return False


def get_idx(paper):
    """Get DOI from S2."""
    external_ids = [idx.upper() for idx in paper["externalIds"].keys()]
    if "DOI" in external_ids:
        return paper["externalIds"]["DOI"]
    elif "ARXIV" in external_ids:
        return paper["externalIds"]["ArXiv"]
    else:
        return paper["externalIds"]["CorpusId"]


def url_to_pdf_link(url):
    """Parse URL into the link for the PDF."""
    if not url:
        return None
    else:
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


def write_results(writer, results, header=False):
    """Write results to file."""

    if header:
        writer.writerow(header)

    for line in results:
        line.append("")
        writer.writerow(line)


def search_s2(
    queries: List[str],
    venues: str,
    fields: List[str],
    start_year=None,
    end_year=None,
    **kwargs,
):
    """Search S2 for one term at a time."""

    idx_list = []
    # Set up strings
    start_year_url = f"{start_year}-" if start_year else ""
    if end_year:
        end_year_url = f"{end_year}" if start_year else f"&year=-{end_year}"
    else:
        end_year_url = ""
    year_str = f"&year={start_year_url}{end_year_url}"
    venue_str = f"&venue={venues}"

    # Ensure ExternalIds (contain DOI) is always the last element.
    if "externalIds" not in fields:
        fields.append("externalIds")
    elif "ExternalIds" in fields:
        fields.pop("ExternalIds")
    if "authors" not in fields:
        fields.append("authors")
    if "year" not in fields:
        fields.append("year")

    fields_str = f"&fields={fields}"
    base_str = "http://api.semanticscholar.org/graph/v1/paper/search/bulk?"

    for term in queries:
        url = f"{base_str}query={term}{fields_str}{venue_str}{year_str}"
        print(url)
        r = requests.get(url).json()
        print(f"Will retrieve an estimated {r['total']} documents for {term}")

        while True:
            if "data" in r:
                for paper in tqdm(r["data"]):
                    idx = get_idx(paper)
                    if idx not in idx_list:
                        idx_list.append(idx)
                        res = {key: paper.get(key) for key in fields.split(',')}
                        res.update({"idx": idx, "term": term, "url": None, "pdf": None})
                        yield res

            if "token" not in r:
                break
            r = requests.get(f"{url}&token={r['token']}").json()


def main():
    parser = argparse.ArgumentParser(
        description="""Search for & download papers from ISCA venues via Semantic Scholar.
        The API description is here:
        https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_paper_bulk_search
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--start_year",
        type=int,
        help="Enter the first year to be included in the search.",
        default=1970,
    )
    parser.add_argument(
        "--end_year",
        type=int,
        help="Enter the last year to be included in the search.",
        default=2024,
    )
    parser.add_argument(
        "--venues",
        type=str,
        help="Enter the venues to be searched through (e.g., `interspeech,IberSPEECH`)",
        default="Interspeech",
    )
    parser.add_argument(
        "--queries",
        "-q",
        help="""Enter the first query here using the Semantic Scholar API query format.
For example, to search for two queries one searching for ASR and English and one
for TTS and English write:
--queries "ASR + English" "TTS + English"

The quotation marks are required to ensure that the query is correctly parsed.
        """,
        required=True,
        nargs="+",
    )
    parser.add_argument(
        "--fields",
        help="Enter S2 fields (bulk search) to return (e.g., `title,year,externalIds').",
        default="title,abstract,authors,year,venue,openAccessPdf,externalIds",
    )
    parser.add_argument(
        "--csv",
        help="Add the name of the file to save results to.",
        default="results.tsv",
    )
    parser.add_argument(
        "--download",
        help="Download the PDFs as well as creating a spreadsheet.",
        default=True,
    )
    parser.add_argument(
        "--download_dir",
        help="Directory to store downloaded PDFs to",
        default="pdfs/",
    )
    args = parser.parse_args()
    args_dict = args.__dict__

    search_results = search_s2(**args_dict)
    to_write = []
    header = ["idx", "link", "pdf", "title", "abstract", "venue"]

    if args.download:
        os.makedirs(args.download_dir, exist_ok=True)

    for paper in search_results:
        paper["errors"] = []

        url = extract_url(paper)
        pdf_url = url_to_pdf_link(url) if url else ""
        paper["errors"].append("Interspeech URL not ")

        if url:
            paper["link"] = url
        else:
            paper["link"] = paper["url"]
            paper["errors"].append("Paper URL not found")

        if pdf_url:
            paper["pdf"] = pdf_url
        else:
            paper["pdf"] = ""
            paper["errors"].append("PDF URL not found")

        if args.download:
            download_pdf(pdf_url, args.download_dir)

        line = [paper[key] for key in header]

        to_write.append(line)

    with open(args.csv, "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        write_results(writer, to_write, header + ["Relevant"])


if __name__ == "__main__":
    main()
