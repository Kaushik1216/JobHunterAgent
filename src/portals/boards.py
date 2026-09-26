from __future__ import annotations

from typing import ClassVar

from portals.base import BoardJobPortal, PortalKind


class LinkedInPortal(BoardJobPortal):
    portal_id: ClassVar[str] = "linkedin"
    display_name: ClassVar[str] = "LinkedIn"
    kind: ClassVar[PortalKind] = "board"
    site_filter: ClassVar[str] = "site:linkedin.com/jobs/view/"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("linkedin.com",)

    def accepts_url(self, url: str) -> bool:
        if not super().accepts_url(url):
            return False
        return "/jobs/view/" in url.lower()


class IndeedPortal(BoardJobPortal):
    portal_id: ClassVar[str] = "indeed"
    display_name: ClassVar[str] = "Indeed"
    site_filter: ClassVar[str] = "site:indeed.com/viewjob"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("indeed.com",)

    def accepts_url(self, url: str) -> bool:
        if not super().accepts_url(url):
            return False
        lower = url.lower()
        return any(p in lower for p in ("/viewjob", "/rc/clk", "/job/"))


class NaukriPortal(BoardJobPortal):
    portal_id: ClassVar[str] = "naukri"
    display_name: ClassVar[str] = "Naukri"
    site_filter: ClassVar[str] = "site:naukri.com/job-listings"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("naukri.com",)

    def accepts_url(self, url: str) -> bool:
        if not super().accepts_url(url):
            return False
        return "/job-listings" in url.lower()


class GlassdoorPortal(BoardJobPortal):
    portal_id: ClassVar[str] = "glassdoor"
    display_name: ClassVar[str] = "Glassdoor"
    site_filter: ClassVar[str] = "site:glassdoor.com"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("glassdoor.com",)


class WellfoundPortal(BoardJobPortal):
    portal_id: ClassVar[str] = "wellfound"
    display_name: ClassVar[str] = "Wellfound"
    site_filter: ClassVar[str] = "site:wellfound.com/jobs"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("wellfound.com", "angel.co")
