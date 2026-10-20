/**
 * NeuroCare Nexus — Platform Activity Pipeline (Phase D)
 * Analytics Formatting Utilities
 */

/**
 * Formats a raw second count into human-readable duration string.
 * Examples:
 *   3660s -> "1h 1m"
 *   540s  -> "9m"
 *   45s   -> "45s"
 *   0s    -> "0s"
 *   null  -> "No data"
 */
export const formatDuration = (totalSeconds) => {
  if (totalSeconds === null || totalSeconds === undefined) return 'No data';
  const sec = Math.round(Number(totalSeconds));
  if (isNaN(sec) || sec < 0) return 'No data';
  if (sec === 0) return '0s';

  const hours = Math.floor(sec / 3600);
  const minutes = Math.floor((sec % 3600) / 60);
  const remainingSeconds = sec % 60;

  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  if (minutes > 0) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }
  return `${remainingSeconds}s`;
};

/**
 * Formats a date string (YYYY-MM-DD or ISO) into readable label (e.g. "Oct 19")
 */
export const formatDateLabel = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch (e) {
    return dateStr;
  }
};

/**
 * Formats ISO string into clean relative time ("Just now", "2m ago", etc.)
 */
export const formatRelativeTime = (isoStr) => {
  if (!isoStr) return 'Never';
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    if (diffMs < 0) return 'Just now';
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
  } catch (e) {
    return 'Invalid date';
  }
};

/**
 * Formats ISO string into full readable local datetime
 */
export const formatFullDateTime = (isoStr) => {
  if (!isoStr) return 'N/A';
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return 'N/A';
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (e) {
    return 'N/A';
  }
};
