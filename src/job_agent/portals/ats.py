from __future__ import annotations

from typing import ClassVar

from job_agent.portals.base import AtsJobPortal, PortalKind


class GreenhousePortal(AtsJobPortal):
    portal_id: ClassVar[str] = "greenhouse"
    display_name: ClassVar[str] = "Greenhouse"
    kind: ClassVar[PortalKind] = "ats"
    site_filter: ClassVar[str] = "site:greenhouse.io"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("greenhouse.io",)


class LeverPortal(AtsJobPortal):
    portal_id: ClassVar[str] = "lever"
    display_name: ClassVar[str] = "Lever"
    site_filter: ClassVar[str] = "site:jobs.lever.co"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("lever.co",)


class AshbyPortal(AtsJobPortal):
    portal_id: ClassVar[str] = "ashby"
    display_name: ClassVar[str] = "Ashby"
    site_filter: ClassVar[str] = "site:jobs.ashbyhq.com"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("ashbyhq.com",)
