export function getScoreClass(score: number, evaluated: boolean): string {
  if (!evaluated) return "";
  if (score >= 0.8) return "high";
  if (score >= 0.7) return "med";
  return "low";
}
