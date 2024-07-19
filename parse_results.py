import csv
import pydoi
import requests
from tqdm import tqdm
from typing import List
from argparse import ArgumentParser


def extract_url(paper):
    """Get URL for paper. Give preference to ArXiv"""
    if "ArXiv" in paper["externalIds"].keys():
        arxiv_idx = paper["externalIds"]["ArXiv"]
        return f"https://arxiv.org/abs/{arxiv_idx}"
    elif "DOI" in paper["externalIds"].keys():
        resolved = pydoi.get_url(paper["externalIds"]["DOI"])
        return resolved if resolved else paper["url"]
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


def url_to_pdf_link(url):
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


def search_s2(
    queries: List[str],
    venues: str,
    fields: List[str],
    year_start=None,
    year_end=None,
    **kwargs,
):
    """Search S2 for one term at a time."""

    idx_list = []
    # Set up strings
    year_start_url = "&year={year_start}-" if year_start else ""
    if year_end:
        year_end_url = f"{year_end}" if year_start else f"&year=-{year_end}"
    else:
        year_end_url = ""
    year_str = f"{year_start_url}{year_end_url}"
    venue_str = f"&venue={venues}"

    # Ensure ExternalIds (contain DOI) is always the last element.
    if "externalIds" not in fields:
        fields.append("externalIds")
    elif "ExternalIds" in fields:
        fields.pop("ExternalIds")
    fields_str = f"&fields={','.join(fields)}"
    base_str = "http://api.semanticscholar.org/graph/v1/paper/search/bulk?"

    for term in queries:
        url = f"{base_str}term={term}{fields_str}{venue_str}{year_str}"
        r = requests.get(url).json()
        print(f"Will retrieve an estimated {r['total']} documents for {term}")

        while True:
            if "data" in r:
                for paper in tqdm(r["data"]):
                    idx = get_idx(paper)
                    if idx not in idx_list:
                        idx_list.append(idx)
                        res = {key: paper.get(key) for key in fields}
                        res.update(
                            {"idx": idx, "url": extract_url(paper), "term": term}
                        )
                        yield res

            if "token" not in r:
                break
            r = requests.get(f"{url}&token={r['token']}").json()


def main():
    parser = ArgumentParser(
        description="""Search for & download papers from ISCA venues via Semantic Scholar.
        The API description is here:
        https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_paper_bulk_search
        """
    )
    parser.add_argument(
        "--year",
        type=int,
        desc="Enter the first year to be included in the search.",
        default=1970,
    )
    parser.add_argument(
        "--venues",
        type=str,
        desc="Enter the venues to be searched through (e.g., `interspeech,IberSPEECH`)",
        default="interspeech",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        desc="Enter the maximum number of results to return.",
        default=20000,
    )
    parser.add_argument(
        "--query",
        "-q",
        desc="Enter the query here following the Semantic Scholar API query format.",
        required=True,
    )
    parser.add_argument(
        "--fields",
        desc="Enter S2 fields (bulk search) to return (e.g., `title,year,externalIds').",
        default="title,year,venue,openAccessPdf,externalIds",
    )
    parser.add_argument(
        "--download",
        desc="Download the PDFs as well as creating a spreadsheet.",
        default=True,
    )
    parser.add_argument(
        "--download_dir", desc="Directory to store downloaded PDFs to", default="pdfs/"
    )
    args = parser.parse_args()

    search_results = search_s2(**args)
    to_write = []
    header = ["idx", "url", "pdf", "title", "abstract", "venue"]

    for paper in search_results:
        paper = search_results.pop(paper)
        paper["errors"] = []

        url = extract_url(paper)
        pdf_url = url_to_pdf_link(url)

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

    with open(args.csv, 'w', encoding = 'utf-8') as file:
        writer = csv.writer(file, delimiter = '\t')
        write_results(writer, to_write, header + ['Relevant'])


if __name__ == "__main__":
    pass
