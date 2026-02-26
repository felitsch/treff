/**
 * Hashtag-Sets-Konfiguration fuer den Hashtag-Manager
 *
 * Vordefinierte Hashtag-Gruppen organisiert nach:
 * - Brand-Hashtags (immer verwenden)
 * - Nischen-Hashtags (themenspezifisch)
 * - Trending-Hashtags (saisonale Trends)
 * - Laender-Hashtags (pro Zielland)
 *
 * Integriert in:
 * - HashtagManager.vue (Vordefinierte Sets laden)
 * - AI Hashtag-Suggestion (/api/ai/suggest-hashtags)
 * - backend/app/core/strategy_loader.py
 *
 * @module hashtagSets
 * @see frontend/src/components/posts/HashtagManager.vue
 * @see frontend/src/config/social-content.json - Quell-Daten
 * @see backend/app/api/routes/hashtag_sets.py - DB-gespeicherte Sets
 */

// ═══════════════════════════════════════════════════════════════════
// BRAND HASHTAGS (immer mindestens 1 verwenden)
// ═══════════════════════════════════════════════════════════════════

export const BRAND_HASHTAGS = {
  primary: ['#TREFFSprachreisen', '#HighschoolYear', '#MeinTREFFJahr'],
  secondary: ['#TREFFAlumni', '#TREFFFamily', '#TREFFSprachreisen1984'],
  campaign: ['#DeinAuslandsjahr2027', '#TREFFGoesGlobal'],
}

// ═══════════════════════════════════════════════════════════════════
// NISCHEN-HASHTAGS (themenspezifisch)
// ═══════════════════════════════════════════════════════════════════

export const NICHE_HASHTAGS = {
  auslandsjahr: {
    name: 'Auslandsjahr & Austausch',
    hashtags: [
      '#Auslandsjahr', '#Schüleraustausch', '#HighSchoolAbroad',
      '#StudyAbroad', '#GapYear', '#Austauschschüler',
      '#AuslandsjahrUSA', '#AuslandsjahrKanada',
    ],
  },
  reise_bildung: {
    name: 'Reise & Bildung',
    hashtags: [
      '#WeltEntdecken', '#Fernweh', '#Reiselust',
      '#Bildung', '#Sprachreise', '#KulturellerAustausch',
      '#InterkulturelleBildung',
    ],
  },
  teenager_leben: {
    name: 'Teenager-Leben',
    hashtags: [
      '#TeenagerLeben', '#Schulzeit', '#Abitur',
      '#NachDemAbi', '#GenZ', '#Zukunft',
    ],
  },
}

// ═══════════════════════════════════════════════════════════════════
// LAENDER-HASHTAGS (pro Zielland)
// ═══════════════════════════════════════════════════════════════════

export const COUNTRY_HASHTAGS = {
  usa: {
    name: 'USA',
    flag: '🇺🇸',
    hashtags: [
      '#HighSchoolUSA', '#AuslandsjahrUSA', '#AmericanHighSchool',
      '#USATravel', '#ExchangeStudentUSA',
    ],
  },
  kanada: {
    name: 'Kanada',
    flag: '🇨🇦',
    hashtags: [
      '#HighSchoolKanada', '#AuslandsjahrKanada', '#CanadaLife',
      '#ExchangeStudentCanada', '#StudyInCanada',
    ],
  },
  australien: {
    name: 'Australien',
    flag: '🇦🇺',
    hashtags: [
      '#HighSchoolAustralien', '#AuslandsjahrAustralien', '#AustraliaLife',
      '#StudyDownUnder', '#ExchangeStudentAustralia',
    ],
  },
  neuseeland: {
    name: 'Neuseeland',
    flag: '🇳🇿',
    hashtags: [
      '#HighSchoolNeuseeland', '#AuslandsjahrNeuseeland', '#NewZealandLife',
      '#StudyInNZ', '#KiwiLife',
    ],
  },
  irland: {
    name: 'Irland',
    flag: '🇮🇪',
    hashtags: [
      '#HighSchoolIrland', '#AuslandsjahrIrland', '#IrelandLife',
      '#StudyInIreland', '#ExchangeStudentIreland',
    ],
  },
}

// ═══════════════════════════════════════════════════════════════════
// PREDEFINED HASHTAG SETS (ready-to-use combinations)
// ═══════════════════════════════════════════════════════════════════

export const PREDEFINED_SETS = [
  {
    id: 'brand_standard',
    name: 'Brand Standard',
    description: 'Basis-Set für jeden Post — immer mindestens diese verwenden',
    category: 'brand',
    hashtags: [
      '#TREFFSprachreisen', '#HighschoolYear', '#MeinTREFFJahr',
      '#Auslandsjahr', '#Schüleraustausch',
    ],
    platformRecommendation: 'alle',
  },
  {
    id: 'erfahrungsbericht',
    name: 'Erfahrungsbericht',
    description: 'Für Testimonials und persönliche Geschichten',
    category: 'thema',
    hashtags: [
      '#TREFFSprachreisen', '#MeinTREFFJahr', '#Auslandsjahr',
      '#Schüleraustausch', '#HighSchoolAbroad', '#StudyAbroad',
      '#GapYear', '#Fernweh', '#WeltEntdecken',
      '#TREFFAlumni',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'laender_spotlight_usa',
    name: 'USA Spotlight',
    description: 'Für USA-bezogene Posts und Vergleiche',
    category: 'land',
    country: 'usa',
    hashtags: [
      '#TREFFSprachreisen', '#HighSchoolUSA', '#AuslandsjahrUSA',
      '#AmericanHighSchool', '#USATravel', '#ExchangeStudentUSA',
      '#Auslandsjahr', '#AmericaTheBeautiful',
      '#HighSchoolAbroad', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'laender_spotlight_kanada',
    name: 'Kanada Spotlight',
    description: 'Für Kanada-bezogene Posts',
    category: 'land',
    country: 'kanada',
    hashtags: [
      '#TREFFSprachreisen', '#HighSchoolKanada', '#AuslandsjahrKanada',
      '#CanadaLife', '#ExchangeStudentCanada', '#StudyInCanada',
      '#Auslandsjahr', '#OhCanada',
      '#HighSchoolAbroad', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'laender_spotlight_australien',
    name: 'Australien Spotlight',
    description: 'Für Australien-bezogene Posts',
    category: 'land',
    country: 'australien',
    hashtags: [
      '#TREFFSprachreisen', '#HighSchoolAustralien', '#AuslandsjahrAustralien',
      '#AustraliaLife', '#StudyDownUnder', '#ExchangeStudentAustralia',
      '#Auslandsjahr', '#DownUnder',
      '#HighSchoolAbroad', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'laender_spotlight_neuseeland',
    name: 'Neuseeland Spotlight',
    description: 'Für Neuseeland-bezogene Posts',
    category: 'land',
    country: 'neuseeland',
    hashtags: [
      '#TREFFSprachreisen', '#HighSchoolNeuseeland', '#AuslandsjahrNeuseeland',
      '#NewZealandLife', '#StudyInNZ', '#KiwiLife',
      '#Auslandsjahr', '#Aotearoa',
      '#HighSchoolAbroad', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'laender_spotlight_irland',
    name: 'Irland Spotlight',
    description: 'Für Irland-bezogene Posts',
    category: 'land',
    country: 'irland',
    hashtags: [
      '#TREFFSprachreisen', '#HighSchoolIrland', '#AuslandsjahrIrland',
      '#IrelandLife', '#StudyInIreland', '#ExchangeStudentIreland',
      '#Auslandsjahr', '#EmeraldIsle',
      '#HighSchoolAbroad', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'tipps_tricks',
    name: 'Tipps & Tricks',
    description: 'Für Ratgeber, Packlisten, How-Tos',
    category: 'thema',
    hashtags: [
      '#TREFFSprachreisen', '#Auslandsjahr', '#Schüleraustausch',
      '#AustauschjährTipps', '#HighSchoolAbroad',
      '#Reisetipps', '#PacklisteAusland', '#StudyAbroadTips',
      '#Fernweh', '#WeltEntdecken',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'bewerbung_fristen',
    name: 'Bewerbung & Fristen',
    description: 'Für Bewerbungsaufrufe und Frist-Erinnerungen',
    category: 'thema',
    hashtags: [
      '#TREFFSprachreisen', '#Auslandsjahr', '#DeinAuslandsjahr2027',
      '#BewerbungAusland', '#Highschool2027',
      '#TraumVomAusland', '#JetztBewerben',
      '#Schüleraustausch', '#MeinTREFFJahr',
    ],
    platformRecommendation: 'instagram_feed',
  },
  {
    id: 'tiktok_standard',
    name: 'TikTok Standard',
    description: 'Optimiert für TikTok (3-5 Hashtags + Trending)',
    category: 'plattform',
    hashtags: [
      '#TREFFSprachreisen', '#Auslandsjahr', '#HighSchoolAbroad',
      '#StudyAbroad', '#fyp',
    ],
    platformRecommendation: 'tiktok',
  },
  {
    id: 'reels_standard',
    name: 'Reels Standard',
    description: 'Optimiert für Instagram Reels',
    category: 'plattform',
    hashtags: [
      '#TREFFSprachreisen', '#MeinTREFFJahr', '#Auslandsjahr',
      '#Schüleraustausch', '#HighSchoolAbroad',
      '#Reels', '#InstagramReels',
    ],
    platformRecommendation: 'instagram_reels',
  },
]

// ═══════════════════════════════════════════════════════════════════
// HASHTAG RULES
// ═══════════════════════════════════════════════════════════════════

export const HASHTAG_RULES = [
  'Immer mindestens 1 Brand-Hashtag verwenden (#TREFFSprachreisen)',
  'Mix aus grossen (100k+ Posts) und kleinen (<10k Posts) Hashtags',
  'Instagram: 8-12 Hashtags optimal (nicht alle 30 nutzen)',
  'TikTok: 3-5 Hashtags + 1-2 Trending',
  'Hashtags rotieren — nicht immer die gleichen verwenden',
  'Land-spezifische Hashtags bei Land-bezogenem Content',
]

// ═══════════════════════════════════════════════════════════════════
// PLATFORM LIMITS
// ═══════════════════════════════════════════════════════════════════

export const PLATFORM_HASHTAG_LIMITS = {
  instagram_feed: { min: 5, max: 30, ideal: 10 },
  instagram_stories: { min: 0, max: 10, ideal: 3 },
  instagram_reels: { min: 3, max: 30, ideal: 7 },
  tiktok: { min: 3, max: 10, ideal: 5 },
}

// ═══════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

/**
 * Get a predefined set by ID.
 * @param {string} setId - Set ID
 * @returns {object|undefined}
 */
export function getSetById(setId) {
  return PREDEFINED_SETS.find(s => s.id === setId)
}

/**
 * Get predefined sets filtered by category.
 * @param {string} category - Category (brand|thema|land|plattform)
 * @returns {object[]}
 */
export function getSetsByCategory(category) {
  return PREDEFINED_SETS.filter(s => s.category === category)
}

/**
 * Get predefined sets for a specific country.
 * @param {string} countryKey - Country key (usa|kanada|australien|neuseeland|irland)
 * @returns {object[]}
 */
export function getSetsForCountry(countryKey) {
  return PREDEFINED_SETS.filter(s => s.country === countryKey)
}

/**
 * Get country hashtags for a given country.
 * @param {string} countryKey - Country key
 * @returns {string[]}
 */
export function getCountryHashtags(countryKey) {
  const country = COUNTRY_HASHTAGS[countryKey]
  return country ? country.hashtags : []
}

/**
 * Get all brand hashtags (primary + secondary + campaign).
 * @returns {string[]}
 */
export function getAllBrandHashtags() {
  return [
    ...BRAND_HASHTAGS.primary,
    ...BRAND_HASHTAGS.secondary,
    ...BRAND_HASHTAGS.campaign,
  ]
}

/**
 * Get hashtag limit for a platform.
 * @param {string} platformId - Platform ID
 * @returns {{ min: number, max: number, ideal: number }}
 */
export function getHashtagLimit(platformId) {
  return PLATFORM_HASHTAG_LIMITS[platformId] || { min: 5, max: 30, ideal: 10 }
}

/**
 * Build an optimized hashtag set for a post.
 * Combines brand + country + niche hashtags within the platform's ideal count.
 * @param {object} options
 * @param {string} options.platform - Platform ID
 * @param {string} [options.country] - Country key
 * @param {string} [options.niche] - Niche key (auslandsjahr|reise_bildung|teenager_leben)
 * @returns {string[]}
 */
export function buildOptimizedSet({ platform, country, niche }) {
  const limit = getHashtagLimit(platform)
  const result = []

  // 1. Always include 1-2 brand hashtags
  result.push(BRAND_HASHTAGS.primary[0]) // #TREFFSprachreisen
  if (limit.ideal > 5) {
    result.push(BRAND_HASHTAGS.primary[2]) // #MeinTREFFJahr
  }

  // 2. Add country hashtags (2-3)
  if (country && COUNTRY_HASHTAGS[country]) {
    const countryTags = COUNTRY_HASHTAGS[country].hashtags
    result.push(...countryTags.slice(0, Math.min(3, limit.ideal - result.length)))
  }

  // 3. Add niche hashtags to fill up
  if (niche && NICHE_HASHTAGS[niche]) {
    const nicheTags = NICHE_HASHTAGS[niche].hashtags
    const remaining = limit.ideal - result.length
    if (remaining > 0) {
      result.push(...nicheTags.slice(0, remaining))
    }
  }

  // 4. Fill with general auslandsjahr hashtags if still room
  const remaining = limit.ideal - result.length
  if (remaining > 0) {
    const filler = NICHE_HASHTAGS.auslandsjahr.hashtags
      .filter(h => !result.includes(h))
    result.push(...filler.slice(0, remaining))
  }

  return [...new Set(result)] // Deduplicate
}

/**
 * Get all unique categories from predefined sets.
 * @returns {string[]}
 */
export function getSetCategories() {
  return [...new Set(PREDEFINED_SETS.map(s => s.category))]
}

/**
 * Get all country keys.
 * @returns {string[]}
 */
export function getCountryKeys() {
  return Object.keys(COUNTRY_HASHTAGS)
}
