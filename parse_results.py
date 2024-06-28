import os
import csv
import json
import pydoi
import requests
from tqdm import tqdm
from os.path import exists
from collections import defaultdict


def search_s2(
    query: list,
    fields: list,
    year: int,
    paper_count: int = 2000,
    venue: str = "Interspeech",
    downlad: bool = True,
):
    fields = "title,year,externalIds,venue,openAccessPdf"
    url = f"http://api.semanticscholar.org/graph/v1/paper/search/bulk?query={query}&fields={','.join(fields)}&year={year}-&venue={venue}&limit={paper_count}"
    r = requests.get(url).json()
    print(f"Will retrieve an estimated {r['total']} documents")

    with open("papers.csv", "a") as tsv_file, open("err.txt", "a") as err:
        err_count = 0
        collected = 0
        err_writer = csv.writer(err, delimeter="\t")
        info_writer = csv.writer(tsv_file, delimiter="\t")

        while True:
            if "data" in r:
                for paper in tqdm(r["data"]):
                    res = [paper.get(key) for key in fields]
                    url = extract_url(paper)
                    if url:
                        collected += 1
                        url = parse_url(url)
                        res.append(url)
                        info_writer.write(res)

                        if download:
                            download_pdf(url, pdf_dir)

                    else:
                        err += 1
                        err_writer.write(paper["title"] + "\n")
                        continue
            if "token" not in r:
                break
        r = requests.get(f"{url}&token={r['token']}").json()
    print(f"Done!\n{collected} papers retrieved.\n{err_count} links not available.")


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

    resp = requests.get(url)
    with open(path, "wb") as file:
        file.write(resp.content)
    return 1


def download_pdfs(in_file, s2results, out_dir):
    with open(in_file, "r", encoding="utf-8") as urls, open(
        "dois.txt", "r", encoding="utf-8"
    ) as info, open("download.err", "a", encoding="utf-8") as err, open(
        "download.txt", "w", encoding="utf-8"
    ) as out_f:
        info_dict = {}
        counter = 0
        dl_counter = 0
        err_counter = 0

        for line in info:
            line = line.strip().split(",")
            info_dict[line[0]] = {item for item in line[1:]}

        for line in tqdm(urls, total=19230):
            try:
                doi, url = line.strip().split(",")
                parsed_url = parse_url(url)
                f_name = url.split("/")[-1]
                path = f"papers/{f_name}"

                # Download every paper
                counter += download_pdf(parsed_url)


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
    info_dict = search_files(
        ["emotion", "emo-", "paralinguistic", "para-linguistic", "valence", "arousal"]
    )
    # 6. Write CSV with all information presented.
    write_csv(info_dict)
