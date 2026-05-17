"""Google Search Console integration [PLACEHOLDER] — Section 6.2.

When ``GSC_CREDENTIALS_PATH`` is unset, returns mock GSC data shaped
identically to the real GSC API response after parsing.
"""

import logging

from config import settings

logger = logging.getLogger("seo_portal.gsc")


async def get_gsc_performance(site_url: str, days: int = 90) -> dict:
    """Fetch search-performance data from Google Search Console.

    Real implementation: google-auth + googleapiclient.discovery →
    searchanalytics.query() with dimensions=['page','query'] over `days`.
    Returns the GSCData dict (see mock for the exact shape).
    """
    if not settings.gsc_enabled:
        # [PLACEHOLDER] no credentials configured → mock GSC data
        logger.info("GSC_CREDENTIALS_PATH unset — returning mock GSC data")
        return _mock_gsc_data(site_url)

    # TODO: implement real GSC fetch when GSC_CREDENTIALS_PATH is set
    # from google.oauth2 import service_account
    # from googleapiclient.discovery import build
    # creds = service_account.Credentials.from_service_account_file(
    #     settings.gsc_credentials_path,
    #     scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    # )
    # service = build("searchconsole", "v1", credentials=creds)
    # ... service.searchanalytics().query(siteUrl=settings.gsc_site_url, body=...)
    raise NotImplementedError(
        "[PLACEHOLDER] Real GSC fetch is not implemented yet. "
        "Unset GSC_CREDENTIALS_PATH to use mock data."
    )


def _mock_gsc_data(site_url: str) -> dict:
    """Mock GSC data — identical shape to the real GSC response after parsing.
    A freshly registered site has no traffic yet."""
    return {
        "total_clicks_90d": 0,
        "total_impressions_90d": 0,
        "avg_ctr": 0.0,
        "avg_position": 0.0,
        "top_queries": [],  # {query, clicks, impressions, ctr, position}
        "top_pages": [],  # {page, clicks, impressions, ctr, position}
        "low_ctr_pages": [],  # >200 impressions and CTR < 2%
        "quick_wins": [],  # queries at position 11-20 with >100 impressions
        "indexing_errors": 0,
        "indexed_pages": 0,
        "data_source": "mock",  # "gsc_api" when real
    }
