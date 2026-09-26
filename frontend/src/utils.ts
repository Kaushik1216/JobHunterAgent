export function getScoreClass(score: number, evaluated: boolean): string {
  if (!evaluated) return "";
  if (score >= 0.8) return "high";
  if (score >= 0.7) return "med";
  return "low";
}

export function getCleanApplyUrl(url: string): string {
  if (!url) return "#";
  const trimmed = url.trim();

  // LinkedIn: normalize to canonical https://www.linkedin.com/jobs/view/<id>/
  const liMatch = trimmed.match(/linkedin\.com\/jobs\/view\/(?:[\w-]+-)?(\d+)/i);
  if (liMatch) {
    return `https://www.linkedin.com/jobs/view/${liMatch[1]}/`;
  }

  // Indeed: ensure clean viewjob with jk parameter
  const indeedMatch = trimmed.match(/[?&]jk=([a-zA-Z0-9]+)/);
  if (trimmed.toLowerCase().includes("indeed.com") && indeedMatch) {
    return `https://www.indeed.com/viewjob?jk=${indeedMatch[1]}`;
  }

  return trimmed;
}

export function getDirectSearchUrl(company: string, title: string, location?: string): string {
  const query = `${company} ${title} ${location || ""} careers apply`.trim();
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

