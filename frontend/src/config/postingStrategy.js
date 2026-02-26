/**
 * Posting-Strategie-Konfiguration fuer Smart-Features
 *
 * Zentrale Konfiguration fuer plattform-spezifische Posting-Regeln,
 * die vom SmartScheduler, Kalender-Generator und KI-Vorschlaegen
 * genutzt wird.
 *
 * Definiert pro Plattform:
 * - postingFrequency: min/max/ideal Posts pro Woche
 * - bestTimes: Optimale Zeiten pro Wochentag
 * - maxPostsPerDay: Tageshoechstgrenze
 * - contentFormats: Erlaubte Formate
 * - captionRules: Zeichenlimits, Hashtag-Empfehlungen
 *
 * @module postingStrategy
 * @see frontend/src/components/creator/SmartScheduler.vue - Nutzt bestTimes
 * @see frontend/src/config/social-content.json - Quell-Daten
 * @see backend/app/api/routes/smart_scheduling.py - Backend Smart-Schedule
 * @see backend/app/core/strategy_loader.py - Backend Strategy Loader
 */

// ═══════════════════════════════════════════════════════════════════
// PLATFORM DEFINITIONS
// ═══════════════════════════════════════════════════════════════════

export const PLATFORMS = {
  instagram_feed: {
    id: 'instagram_feed',
    name: 'Instagram Feed',
    icon: 'camera',
    color: '#E1306C',
  },
  instagram_stories: {
    id: 'instagram_stories',
    name: 'Instagram Stories',
    icon: 'device-mobile',
    color: '#F77737',
  },
  instagram_reels: {
    id: 'instagram_reels',
    name: 'Instagram Reels',
    icon: 'film',
    color: '#833AB4',
  },
  tiktok: {
    id: 'tiktok',
    name: 'TikTok',
    icon: 'musical-note',
    color: '#000000',
  },
}

// ═══════════════════════════════════════════════════════════════════
// POSTING STRATEGY PER PLATFORM
// ═══════════════════════════════════════════════════════════════════

export const POSTING_STRATEGY = {
  instagram_feed: {
    postingFrequency: {
      minPerWeek: 3,
      maxPerWeek: 5,
      idealPerWeek: 4,
      description: '3-5 Feed-Posts pro Woche für konsistente Präsenz',
    },
    bestTimes: {
      montag:     { times: ['17:00', '18:00', '19:00'], peak: '18:00', score: 80 },
      dienstag:   { times: ['17:00', '18:00', '19:00', '20:00'], peak: '18:00', score: 95 },
      mittwoch:   { times: ['17:00', '18:00', '19:00'], peak: '18:00', score: 80 },
      donnerstag: { times: ['17:00', '18:00', '19:00', '20:00'], peak: '18:00', score: 90 },
      freitag:    { times: ['17:00', '18:00', '19:00'], peak: '17:00', score: 75 },
      samstag:    { times: ['11:00', '12:00', '13:00', '14:00'], peak: '12:00', score: 85 },
      sonntag:    { times: ['11:00', '12:00', '13:00'], peak: '12:00', score: 70 },
    },
    maxPostsPerDay: 1,
    contentFormats: ['Carousel', 'Single Image', 'Infografik', 'Zitat-Kachel', 'Erfahrungsbericht'],
    captionRules: {
      maxLength: 2200,
      idealLengthRange: [150, 500],
      firstLineHook: true,
      ctaAtEnd: true,
      hashtagCount: { min: 5, max: 15, ideal: 10 },
      emojiDensity: 'moderat — alle 1-2 Saetze ein passender Emoji',
    },
    bestDays: ['Dienstag', 'Donnerstag', 'Samstag'],
    bestPractices: [
      'Erste Zeile muss SOFORT Aufmerksamkeit erregen (Hook)',
      'Carousel-Posts erzielen 3x mehr Engagement als Single-Image',
      'Call-to-Action in jeder Caption: Link in Bio, DM, Kommentar',
      'Gesichter und echte Menschen performen 38% besser als Grafiken',
      'Speichern ist die wichtigste Engagement-Metrik',
    ],
  },

  instagram_stories: {
    postingFrequency: {
      minPerWeek: 5,
      maxPerWeek: 14,
      idealPerWeek: 7,
      description: 'Täglich mindestens 1 Story, idealerweise 3-5 Frames pro Tag',
    },
    bestTimes: {
      montag:     { times: ['07:30', '12:00', '17:30', '20:00'], peak: '17:30', score: 85 },
      dienstag:   { times: ['07:30', '12:00', '17:30', '20:00'], peak: '12:00', score: 80 },
      mittwoch:   { times: ['07:30', '12:00', '17:30', '20:00'], peak: '17:30', score: 85 },
      donnerstag: { times: ['07:30', '12:00', '17:30', '20:00'], peak: '20:00', score: 80 },
      freitag:    { times: ['07:30', '12:00', '17:30', '20:00'], peak: '17:30', score: 90 },
      samstag:    { times: ['10:00', '14:00', '18:00'], peak: '14:00', score: 75 },
      sonntag:    { times: ['10:00', '14:00', '18:00'], peak: '18:00', score: 70 },
    },
    maxPostsPerDay: 3,
    contentFormats: ['Umfrage', 'Quiz', 'Behind-the-Scenes', 'Countdown', 'Q&A', 'Testimonial-Snippet', 'Swipe-Up/Link'],
    captionRules: {
      maxLength: 300,
      idealLengthRange: [30, 100],
      firstLineHook: false,
      ctaAtEnd: false,
      hashtagCount: { min: 0, max: 5, ideal: 3 },
      emojiDensity: 'hoch — Stories sind visuell und emotional',
    },
    bestDays: ['Montag', 'Mittwoch', 'Freitag'],
    bestPractices: [
      'Interaktive Sticker nutzen: Umfragen, Quiz, Fragen-Box',
      'Maximal 7 Frames pro Story-Sequenz',
      'Text gross und zentriert — viele schauen ohne Ton',
      'Hintergrundmusik/Trending Audio für Atmosphäre',
      'Stories-Highlights für dauerhafte Themen nutzen',
    ],
  },

  instagram_reels: {
    postingFrequency: {
      minPerWeek: 2,
      maxPerWeek: 4,
      idealPerWeek: 3,
      description: '2-4 Reels pro Woche — Video-Content wird bevorzugt vom Algorithmus',
    },
    bestTimes: {
      montag:     { times: ['17:00', '18:00', '19:00'], peak: '18:00', score: 80 },
      dienstag:   { times: ['17:00', '18:00', '19:00', '20:00'], peak: '19:00', score: 90 },
      mittwoch:   { times: ['17:00', '18:00', '19:00'], peak: '18:00', score: 80 },
      donnerstag: { times: ['17:00', '18:00', '19:00', '20:00'], peak: '19:00', score: 95 },
      freitag:    { times: ['17:00', '18:00', '19:00'], peak: '18:00', score: 85 },
      samstag:    { times: ['11:00', '12:00', '14:00', '15:00'], peak: '14:00', score: 80 },
      sonntag:    { times: ['11:00', '12:00', '14:00'], peak: '12:00', score: 70 },
    },
    maxPostsPerDay: 2,
    contentFormats: ['POV-Video', 'Storytelling', 'Before/After', 'Listicle', 'Cultural Shock', 'Day in My Life'],
    captionRules: {
      maxLength: 2200,
      idealLengthRange: [100, 300],
      firstLineHook: true,
      ctaAtEnd: true,
      hashtagCount: { min: 3, max: 10, ideal: 7 },
      emojiDensity: 'moderat — weniger Text, mehr Video-Inhalt',
    },
    duration: {
      minSeconds: 5,
      maxSeconds: 90,
      idealRangeSeconds: [15, 60],
      description: '15-60 Sekunden für maximale Watch-Time',
    },
    bestDays: ['Dienstag', 'Donnerstag', 'Freitag'],
    bestPractices: [
      'Die ersten 2 Sekunden entscheiden alles — Hook sofort',
      'Trending Audio verwenden für mehr Reichweite',
      'Vertikales Format 9:16 ist Pflicht',
      'Text-Overlays für Informations-Vermittlung',
      'CTA am Ende: Folgen, Speichern, Kommentieren',
    ],
  },

  tiktok: {
    postingFrequency: {
      minPerWeek: 5,
      maxPerWeek: 14,
      idealPerWeek: 7,
      description: 'TikTok belohnt Konsistenz: 1-2x täglich für optimalen Algorithmus-Boost',
    },
    bestTimes: {
      montag:     { times: ['16:00', '17:00', '19:00', '21:00'], peak: '17:00', score: 80 },
      dienstag:   { times: ['16:00', '17:00', '19:00', '21:00'], peak: '19:00', score: 90 },
      mittwoch:   { times: ['16:00', '17:00', '19:00', '21:00'], peak: '17:00', score: 80 },
      donnerstag: { times: ['16:00', '17:00', '19:00', '21:00'], peak: '19:00', score: 90 },
      freitag:    { times: ['16:00', '17:00', '19:00', '21:00'], peak: '19:00', score: 85 },
      samstag:    { times: ['10:00', '12:00', '15:00', '19:00'], peak: '15:00', score: 85 },
      sonntag:    { times: ['10:00', '12:00', '15:00', '19:00'], peak: '12:00', score: 75 },
    },
    maxPostsPerDay: 2,
    contentFormats: ['Storytelling', 'POV-Videos', 'Duette', 'Stitches', 'Vlogs', 'Listicles', 'Trend-Adaptionen'],
    captionRules: {
      maxLength: 300,
      idealLengthRange: [50, 150],
      firstLineHook: false,
      ctaAtEnd: false,
      hashtagCount: { min: 3, max: 7, ideal: 5 },
      emojiDensity: 'niedrig — TikTok ist video-zentriert',
    },
    duration: {
      minSeconds: 5,
      maxSeconds: 180,
      idealRangeSeconds: [15, 60],
      description: '15-60 Sekunden für maximale Watch-Time. Längere Videos nur bei Storytelling.',
    },
    bestDays: ['Dienstag', 'Donnerstag', 'Samstag'],
    bestPractices: [
      'Die ersten 2 Sekunden entscheiden ALLES',
      'Trending Sounds verwenden',
      'Authentizität schlägt Perfektion',
      'Untertitel sind Pflicht (40% schauen ohne Ton)',
      'Kommentare innerhalb der ersten Stunde beantworten',
    ],
  },
}

// ═══════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

/**
 * Get the posting strategy for a specific platform.
 * @param {string} platformId - Platform ID (e.g., 'instagram_feed')
 * @returns {object|undefined}
 */
export function getStrategyForPlatform(platformId) {
  return POSTING_STRATEGY[platformId]
}

/**
 * Get the best time for a given platform and day of week.
 * @param {string} platformId - Platform ID
 * @param {string} dayName - German day name (lowercase: 'montag', 'dienstag', ...)
 * @returns {{ times: string[], peak: string, score: number }|null}
 */
export function getBestTimeForDay(platformId, dayName) {
  const strategy = POSTING_STRATEGY[platformId]
  if (!strategy) return null
  return strategy.bestTimes[dayName.toLowerCase()] || null
}

/**
 * Get the peak posting time for a platform on a given date.
 * @param {string} platformId - Platform ID
 * @param {Date} date - JavaScript Date object
 * @returns {{ peak: string, score: number, allTimes: string[] }|null}
 */
export function getPeakTimeForDate(platformId, date) {
  const dayNames = ['sonntag', 'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag']
  const dayName = dayNames[date.getDay()]
  const dayInfo = getBestTimeForDay(platformId, dayName)
  if (!dayInfo) return null
  return {
    peak: dayInfo.peak,
    score: dayInfo.score,
    allTimes: dayInfo.times,
  }
}

/**
 * Get all platform IDs.
 * @returns {string[]}
 */
export function getPlatformIds() {
  return Object.keys(PLATFORMS)
}

/**
 * Get platform display info.
 * @param {string} platformId - Platform ID
 * @returns {{ id: string, name: string, icon: string, color: string }|undefined}
 */
export function getPlatformInfo(platformId) {
  return PLATFORMS[platformId]
}

/**
 * Check if posting at a given time is recommended for a platform.
 * Returns a score (0-100) indicating how good the time is.
 * @param {string} platformId - Platform ID
 * @param {Date} dateTime - Full date+time
 * @returns {{ score: number, isPeak: boolean, isRecommended: boolean, warning: string|null }}
 */
export function evaluatePostingTime(platformId, dateTime) {
  const dayNames = ['sonntag', 'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag']
  const dayName = dayNames[dateTime.getDay()]
  const strategy = POSTING_STRATEGY[platformId]
  if (!strategy) return { score: 50, isPeak: false, isRecommended: false, warning: null }

  const dayInfo = strategy.bestTimes[dayName]
  if (!dayInfo) return { score: 50, isPeak: false, isRecommended: false, warning: null }

  const timeStr = `${String(dateTime.getHours()).padStart(2, '0')}:${String(dateTime.getMinutes()).padStart(2, '0')}`
  const hourStr = `${String(dateTime.getHours()).padStart(2, '0')}:00`

  const isPeak = timeStr === dayInfo.peak || hourStr === dayInfo.peak
  const isRecommended = dayInfo.times.includes(hourStr)

  let score = 30 // baseline
  if (isRecommended) score = dayInfo.score
  if (isPeak) score = Math.min(100, dayInfo.score + 5)

  // Warning for very early or late hours
  let warning = null
  const hour = dateTime.getHours()
  if (hour < 7) warning = 'Sehr frühe Uhrzeit — wenige User online'
  else if (hour >= 22) warning = 'Späte Uhrzeit — sinkende Reichweite'
  else if (!isRecommended) warning = 'Außerhalb der empfohlenen Zeiten für diese Plattform'

  return { score, isPeak, isRecommended, warning }
}

/**
 * Get a summary of all platforms' ideal posting frequency.
 * @returns {Array<{ platform: string, name: string, idealPerWeek: number, maxPerDay: number }>}
 */
export function getFrequencySummary() {
  return Object.entries(POSTING_STRATEGY).map(([id, strategy]) => ({
    platform: id,
    name: PLATFORMS[id]?.name || id,
    idealPerWeek: strategy.postingFrequency.idealPerWeek,
    maxPerDay: strategy.maxPostsPerDay,
    description: strategy.postingFrequency.description,
  }))
}

/**
 * Get the best days across all platforms (unique, sorted by score).
 * @param {string} platformId - Platform ID
 * @returns {Array<{ day: string, peak: string, score: number }>}
 */
export function getBestDaysSorted(platformId) {
  const strategy = POSTING_STRATEGY[platformId]
  if (!strategy) return []

  return Object.entries(strategy.bestTimes)
    .map(([day, info]) => ({
      day: day.charAt(0).toUpperCase() + day.slice(1),
      peak: info.peak,
      score: info.score,
    }))
    .sort((a, b) => b.score - a.score)
}
