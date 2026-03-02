import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Mock data — realistic articles for demo/testing
MOCK_ARTICLES = [
    {
        "title": "Impact of Intermittent Fasting on Longevity Markers in Middle-Aged Adults",
        "id": "34567890",
        "authors": "Chen Y, Patel R, Williams S",
        "pub_date": "2026-02-15",
        "abstract": (
            "This randomized controlled trial investigated the effects of 16:8 intermittent "
            "fasting on biomarkers associated with aging in 240 middle-aged adults over 12 months. "
            "Participants in the fasting group showed significant reductions in fasting insulin "
            "(−18.3%, p<0.001), IGF-1 (−12.7%, p=0.003), and inflammatory markers including "
            "CRP (−22.1%, p<0.001) compared to the ad libitum control group. Telomere length "
            "attrition was 40% slower in the fasting cohort. No adverse metabolic effects were "
            "observed. These findings suggest that time-restricted eating may slow key molecular "
            "aging pathways in humans."
        ),
    },
    {
        "title": "CRISPR-Cas13 Reduces Off-Target RNA Editing in Human Cell Lines",
        "id": "98765432",
        "authors": "Zhang L, Kim J, Nakamura T",
        "pub_date": "2026-01-28",
        "abstract": (
            "Off-target effects remain a major barrier to clinical translation of RNA-targeting "
            "CRISPR systems. We engineered a high-fidelity Cas13d variant (hfCas13d) by "
            "introducing point mutations in the HEPN catalytic domain that increase target-spacer "
            "mismatch sensitivity. In HEK293T and primary T-cell lines, hfCas13d reduced "
            "transcriptome-wide off-target cleavage by 87% while retaining >95% on-target "
            "knockdown efficiency for three therapeutic gene targets (PCSK9, KRAS-G12D, MYC). "
            "RNA-seq confirmed minimal collateral damage. This variant offers a path toward "
            "safer RNA therapeutics with CRISPR technology."
        ),
    },
    {
        "title": "mRNA Vaccine Platform Shows Broad-Spectrum Efficacy Against Influenza Subtypes",
        "id": "45678901",
        "authors": "Fernandez A, Okonkwo C, Gupta M",
        "pub_date": "2026-02-03",
        "abstract": (
            "Current influenza vaccines require annual reformulation due to antigenic drift. "
            "We developed a nucleoside-modified mRNA vaccine encoding conserved epitopes from "
            "the hemagglutinin stalk and neuraminidase domains of 12 influenza A and B subtypes. "
            "In ferret challenge models, a two-dose regimen induced broadly neutralizing "
            "antibodies and conferred protection against H1N1, H3N2, H5N1, and B/Yamagata "
            "lineages (survival rates 90–100% vs 20–40% in controls). T-cell responses were "
            "durable at 6 months post-vaccination. Phase I human trials are planned for Q3 2026."
        ),
    },
]


def fetch_abstracts(keyword: str, max_results: int = 10) -> List[Dict]:
    """
    Fetches recent abstracts from PubMed using the Entrez API.
    Falls back to mock data if MOCK_MODE is active or if the fetch fails.
    """
    if settings.MOCK_MODE:
        logger.info(f"Mock mode active. Returning static data for: {keyword}")
        return MOCK_ARTICLES

    # Live PubMed fetch via Biopython Entrez
    try:
        from Bio import Entrez, Medline

        Entrez.email = settings.PUBMED_EMAIL
        Entrez.tool = "Bio-Intel-Agent"

        # Search for recent articles matching the keyword
        logger.info(f"Searching PubMed for: {keyword} (max {max_results})")
        search_handle = Entrez.esearch(
            db="pubmed",
            term=keyword,
            retmax=max_results,
            sort="date",
            datetype="pdat",
            reldate=30,  # last 30 days
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()

        pmids = search_results.get("IdList", [])
        if not pmids:
            logger.warning(f"No PubMed results for '{keyword}' in last 30 days.")
            return []

        logger.info(f"Found {len(pmids)} PMIDs: {pmids}")

        # Fetch full records for those PMIDs
        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="medline",
            retmode="text",
        )
        records = list(Medline.parse(fetch_handle))
        fetch_handle.close()

        articles = []
        for record in records:
            title = record.get("TI", "No title")
            abstract = record.get("AB", "")
            pmid = record.get("PMID", "")
            authors = ", ".join(record.get("AU", [])[:3])
            pub_date = record.get("DP", "")

            if not abstract:
                continue  # Skip articles without abstracts

            articles.append({
                "title": title,
                "id": pmid,
                "authors": authors,
                "pub_date": pub_date,
                "abstract": abstract,
            })

        logger.info(f"Fetched {len(articles)} articles with abstracts from PubMed.")
        return articles

    except Exception as e:
        logger.error(f"Failed to fetch from PubMed: {e}. Falling back to mock data.")
        return MOCK_ARTICLES
