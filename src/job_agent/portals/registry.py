from __future__ import annotations

from job_agent.config import Settings
from job_agent.exceptions import ConfigurationError
from job_agent.portals.ats import AshbyPortal, GreenhousePortal, LeverPortal
from job_agent.portals.base import JobPortal
from job_agent.portals.boards import (
    GlassdoorPortal,
    IndeedPortal,
    LinkedInPortal,
    NaukriPortal,
    WellfoundPortal,
)

PORTAL_REGISTRY: dict[str, type[JobPortal]] = {
    LinkedInPortal.portal_id: LinkedInPortal,
    IndeedPortal.portal_id: IndeedPortal,
    NaukriPortal.portal_id: NaukriPortal,
    GlassdoorPortal.portal_id: GlassdoorPortal,
    WellfoundPortal.portal_id: WellfoundPortal,
    GreenhousePortal.portal_id: GreenhousePortal,
    LeverPortal.portal_id: LeverPortal,
    AshbyPortal.portal_id: AshbyPortal,
}


def list_portal_ids() -> list[str]:
    return sorted(PORTAL_REGISTRY)


def portal_display_name(portal_id: str) -> str:
    cls = PORTAL_REGISTRY.get(portal_id)
    if cls is None:
        return "Job board"
    return cls.display_name


def apply_label_for_portal(portal_id: str) -> str:
    name = portal_display_name(portal_id)
    if name == "Job board":
        return "Apply"
    return f"Apply on {name}"


def create_portals(settings: Settings, portal_ids: list[str] | None = None) -> list[JobPortal]:
    requested = portal_ids if portal_ids is not None else settings.enabled_portal_ids()
    if not requested:
        raise ConfigurationError("No job portals enabled. Set JOB_AGENT_SEARCH_PORTALS.")

    unknown = [portal_id for portal_id in requested if portal_id not in PORTAL_REGISTRY]
    if unknown:
        known = ", ".join(list_portal_ids())
        raise ConfigurationError(f"Unknown job portal(s): {', '.join(unknown)}. Known: {known}")

    return [PORTAL_REGISTRY[portal_id](settings) for portal_id in requested]
