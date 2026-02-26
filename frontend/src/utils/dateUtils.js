/**
 * Shared date formatting utilities with isNaN guards.
 *
 * The backend API returns dates as ISO datetime strings
 * (e.g., "2026-02-26T00:00:00" from Python's datetime.isoformat()).
 * These helpers ensure that invalid or missing date strings never
 * produce NaN or "Invalid Date" in the UI.
 */

/**
 * Safely parse a date string from the API.
 * Handles both "YYYY-MM-DD" and full ISO datetime "YYYY-MM-DDTHH:MM:SS" formats.
 * Returns null if the date is invalid.
 *
 * @param {string|null|undefined} dateStr - ISO date string from the API
 * @returns {Date|null} Parsed Date object, or null if invalid
 */
export function parseDate(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  return isNaN(d.getTime()) ? null : d
}

/**
 * Safely parse a date string, extracting only the date portion (YYYY-MM-DD).
 * Useful when you need to combine a date with a separate time, or when the
 * API returns a full ISO datetime but you only care about the calendar date.
 *
 * @param {string|null|undefined} dateStr - ISO date string from the API
 * @returns {Date|null} Parsed Date object at midnight local time, or null if invalid
 */
export function parseDateOnly(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr.substring(0, 10) + 'T00:00:00')
  return isNaN(d.getTime()) ? null : d
}

/**
 * Format a date string for display (dd.mm.yyyy German locale).
 * Returns the fallback string if the date is invalid.
 *
 * @param {string|null|undefined} dateStr - ISO date string from the API
 * @param {string} fallback - Value to return when the date is invalid
 * @returns {string} Formatted date string or fallback
 */
export function formatDate(dateStr, fallback = '') {
  const d = parseDate(dateStr)
  if (!d) return fallback
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/**
 * Format a date string as short date (e.g., "26. Feb.").
 * Returns the fallback string if the date is invalid.
 *
 * @param {string|null|undefined} dateStr - ISO date string from the API
 * @param {string} fallback - Value to return when the date is invalid
 * @returns {string} Short formatted date string or fallback
 */
export function formatDateShort(dateStr, fallback = '') {
  const d = parseDate(dateStr)
  if (!d) return fallback
  return d.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' })
}
