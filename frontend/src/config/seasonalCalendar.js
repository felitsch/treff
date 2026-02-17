/**
 * Saisonaler Content-Kalender fuer TREFF Sprachreisen
 *
 * Vollstaendiger 12-Monats-Redaktionskalender mit:
 * - Monatlichen Themes und Focus Pillars
 * - Key Dates (Bewerbungsfristen, Abreisewellen, Feiertage)
 * - Departure Waves pro Land (USA, Kanada, Australien, Neuseeland, Irland)
 * - Deutsche Feiertage und Schulferien
 * - Internationale Feiertage pro Zielland
 * - Content-Empfehlungen (Pillar, Post-Typ, Beispiel-Headline)
 *
 * Kompatibel mit dem bestehenden seasonalMarkers ref in CalendarView.vue
 * (Marker-Format: { date, type, label, icon, color, description })
 *
 * @module seasonalCalendar
 * @see frontend/src/views/CalendarView.vue - Consumer of seasonal markers
 * @see frontend/src/config/contentPillars.js - Content pillar definitions
 * @see backend/app/api/routes/calendar.py - Backend seasonal markers API
 *
 * @typedef {Object} MonthConfig
 * @property {number} month - Month number (1-12)
 * @property {string} theme - Monthly theme/focus
 * @property {string[]} focus_pillars - IDs from contentPillars.js
 * @property {KeyDate[]} key_dates - Important dates this month
 * @property {'low'|'medium'|'high'} posting_intensity - Recommended posting frequency
 * @property {string} intensity_reason - Why this intensity level
 *
 * @typedef {Object} KeyDate
 * @property {number} day - Day of month
 * @property {string} type - Category: bewerbungsfrist|abflugzeit|rueckkehr|schuljahresbeginn|feiertag|schulferien|messe|stipendium|content_highlight
 * @property {string} label - Display name
 * @property {string} icon - Emoji icon
 * @property {string} color - Color key (red|blue|green|purple|amber|teal|orange|pink|indigo)
 * @property {string} description - Detailed description
 * @property {string} country - Country code: DE|US|CA|AU|NZ|IE|ALL
 * @property {ContentRecommendation} content_recommendation - Suggested content
 *
 * @typedef {Object} ContentRecommendation
 * @property {string} pillar - Content pillar ID from contentPillars.js
 * @property {string} post_type - Carousel|Reel|Story|Single Image|Infografik|Story-Serie
 * @property {string} example_headline - Example headline for this date
 *
 * @typedef {Object} DepartureWave
 * @property {string} country - Country name
 * @property {string} country_code - ISO code (US|CA|AU|NZ|IE)
 * @property {string} flag - Flag emoji
 * @property {DeparturePeriod[]} departures - Departure periods
 *
 * @typedef {Object} DeparturePeriod
 * @property {string} season - Herbst|Fruehling|Sommer|Winter
 * @property {number} month - Departure month (1-12)
 * @property {number} day - Approximate departure day
 * @property {string} label - Description
 * @property {string} school_start - When school starts
 */

// ============================================================
// DEPARTURE WAVES PER COUNTRY
// ============================================================

export const DEPARTURE_WAVES = [
  {
    country: 'USA',
    country_code: 'US',
    flag: '\u{1F1FA}\u{1F1F8}',
    programs: ['Classic', 'Select'],
    departures: [
      {
        season: 'Herbst',
        month: 8,
        day: 15,
        label: 'Hauptabreise USA (August)',
        school_start: 'Ende August / Anfang September',
        return_month: 6,
        return_day: 15,
      },
      {
        season: 'Fruehling',
        month: 1,
        day: 10,
        label: 'Januar-Abreise USA (Halbjahr)',
        school_start: 'Januar',
        return_month: 6,
        return_day: 15,
      },
    ],
  },
  {
    country: 'Kanada',
    country_code: 'CA',
    flag: '\u{1F1E8}\u{1F1E6}',
    programs: ['Englisch', 'Franzoesisch (Quebec)'],
    departures: [
      {
        season: 'Herbst',
        month: 9,
        day: 1,
        label: 'Hauptabreise Kanada (September)',
        school_start: 'Anfang September',
        return_month: 6,
        return_day: 30,
      },
      {
        season: 'Fruehling',
        month: 2,
        day: 1,
        label: 'Februar-Abreise Kanada (Semester 2)',
        school_start: 'Anfang Februar',
        return_month: 6,
        return_day: 30,
      },
    ],
  },
  {
    country: 'Australien',
    country_code: 'AU',
    flag: '\u{1F1E6}\u{1F1FA}',
    programs: ['Highschool'],
    departures: [
      {
        season: 'Sommer (Suedhalbkugel)',
        month: 1,
        day: 20,
        label: 'Hauptabreise Australien (Januar)',
        school_start: 'Ende Januar / Anfang Februar (Term 1)',
        return_month: 12,
        return_day: 10,
      },
      {
        season: 'Winter (Suedhalbkugel)',
        month: 7,
        day: 10,
        label: 'Juli-Abreise Australien (Term 3)',
        school_start: 'Mitte Juli (Term 3)',
        return_month: 12,
        return_day: 10,
      },
    ],
  },
  {
    country: 'Neuseeland',
    country_code: 'NZ',
    flag: '\u{1F1F3}\u{1F1FF}',
    programs: ['Highschool'],
    departures: [
      {
        season: 'Sommer (Suedhalbkugel)',
        month: 1,
        day: 25,
        label: 'Hauptabreise Neuseeland (Januar)',
        school_start: 'Ende Januar / Anfang Februar (Term 1)',
        return_month: 12,
        return_day: 15,
      },
      {
        season: 'Winter (Suedhalbkugel)',
        month: 7,
        day: 15,
        label: 'Juli-Abreise Neuseeland (Term 3)',
        school_start: 'Mitte Juli (Term 3)',
        return_month: 12,
        return_day: 15,
      },
    ],
  },
  {
    country: 'Irland',
    country_code: 'IE',
    flag: '\u{1F1EE}\u{1F1EA}',
    programs: ['Highschool'],
    departures: [
      {
        season: 'Herbst',
        month: 9,
        day: 1,
        label: 'Abreise Irland (September)',
        school_start: 'Anfang September',
        return_month: 6,
        return_day: 1,
      },
    ],
  },
]

// ============================================================
// INTERNATIONAL HOLIDAYS PER COUNTRY
// ============================================================

export const INTERNATIONAL_HOLIDAYS = [
  // USA
  { month: 11, day: 28, label: 'Thanksgiving (USA)', icon: '\u{1F983}', color: 'orange', country: 'US', type: 'feiertag', description: 'Amerikanisches Erntedankfest - perfekt fuer Erfahrungsberichte von TREFF-Teilnehmern in den USA' },
  { month: 7, day: 4, label: 'Independence Day (USA)', icon: '\u{1F386}', color: 'blue', country: 'US', type: 'feiertag', description: 'Amerikanischer Unabhaengigkeitstag - Schueler erleben die Feiern hautnah mit' },
  { month: 10, day: 31, label: 'Halloween (USA/CA/IE)', icon: '\u{1F383}', color: 'orange', country: 'US', type: 'feiertag', description: 'Halloween in den USA, Kanada und Irland - ein Highlight fuer Austauschschueler' },
  { month: 2, day: 14, label: 'Super Bowl Sunday (USA)', icon: '\u{1F3C8}', color: 'blue', country: 'US', type: 'feiertag', description: 'Das groesste Sportereignis der USA - Kulturerlebnis fuer Austauschschueler' },
  { month: 5, day: 26, label: 'Memorial Day (USA)', icon: '\u{1F1FA}\u{1F1F8}', color: 'blue', country: 'US', type: 'feiertag', description: 'Amerikanischer Gedenktag - Start der Sommerferien, Ende des Schuljahres naht' },
  // Canada
  { month: 7, day: 1, label: 'Canada Day', icon: '\u{1F1E8}\u{1F1E6}', color: 'red', country: 'CA', type: 'feiertag', description: 'Kanadischer Nationalfeiertag - Austauschschueler feiern mit' },
  { month: 10, day: 14, label: 'Thanksgiving (Kanada)', icon: '\u{1F341}', color: 'orange', country: 'CA', type: 'feiertag', description: 'Kanadisches Erntedankfest im Oktober - frueher als in den USA' },
  // Australia
  { month: 1, day: 26, label: 'Australia Day', icon: '\u{1F1E6}\u{1F1FA}', color: 'blue', country: 'AU', type: 'feiertag', description: 'Australischer Nationalfeiertag - perfekt fuer Laender-Spotlight Content' },
  { month: 4, day: 25, label: 'ANZAC Day (AU/NZ)', icon: '\u{1F3D6}\u{FE0F}', color: 'green', country: 'AU', type: 'feiertag', description: 'Gedenktag in Australien und Neuseeland - kulturelles Erlebnis fuer Schueler' },
  // New Zealand
  { month: 2, day: 6, label: 'Waitangi Day (NZ)', icon: '\u{1F1F3}\u{1F1FF}', color: 'green', country: 'NZ', type: 'feiertag', description: 'Neuseelands Nationalfeiertag - Gruendungstag mit Maori-Kultur' },
  // Ireland
  { month: 3, day: 17, label: 'St. Patrick\'s Day (Irland)', icon: '\u{2618}\u{FE0F}', color: 'green', country: 'IE', type: 'feiertag', description: 'Irlands groesster Feiertag - Austauschschueler mittendrin in Dublin oder Cork' },
]

// ============================================================
// GERMAN HOLIDAYS & SCHOOL BREAKS (content-relevant)
// ============================================================

export const GERMAN_HOLIDAYS = [
  // Schulferien (approximate, varies by Bundesland - BW focus for TREFF)
  { month: 7, day: 25, label: 'Sommerferien-Start (BW)', icon: '\u{2600}\u{FE0F}', color: 'amber', country: 'DE', type: 'schulferien', description: 'Beginn der Sommerferien in Baden-Wuerttemberg - Hochsaison fuer Fernweh-Content' },
  { month: 9, day: 9, label: 'Sommerferien-Ende (BW)', icon: '\u{1F4DA}', color: 'amber', country: 'DE', type: 'schulferien', description: 'Ende der Sommerferien - neue Schueler starten Planung fuers naechste Jahr' },
  { month: 12, day: 23, label: 'Weihnachtsferien-Start', icon: '\u{1F384}', color: 'red', country: 'DE', type: 'schulferien', description: 'Weihnachtsferien - Familienzeit, aber auch Planungszeit fuers Auslandsjahr' },
  { month: 1, day: 7, label: 'Weihnachtsferien-Ende', icon: '\u{2744}\u{FE0F}', color: 'blue', country: 'DE', type: 'schulferien', description: 'Ende der Weihnachtsferien - Neujahrsvorsaetze: Auslandsjahr planen!' },
  { month: 4, day: 14, label: 'Osterferien-Start (BW)', icon: '\u{1F423}', color: 'pink', country: 'DE', type: 'schulferien', description: 'Osterferien - perfekte Zeit fuer Infoveranstaltungen und Beratungsgespraeche' },
  { month: 4, day: 25, label: 'Osterferien-Ende (BW)', icon: '\u{1F33C}', color: 'green', country: 'DE', type: 'schulferien', description: 'Ende der Osterferien - letzte Chance fuer manche Bewerbungsfristen' },
  { month: 5, day: 27, label: 'Pfingstferien-Start (BW)', icon: '\u{1F33B}', color: 'green', country: 'DE', type: 'schulferien', description: 'Pfingstferien - Vorbereitungszeit fuer Herbst-Abreisende' },
  { month: 10, day: 28, label: 'Herbstferien-Start (BW)', icon: '\u{1F342}', color: 'orange', country: 'DE', type: 'schulferien', description: 'Herbstferien - Schueler im Ausland berichten, Daheimgebliebene traumen' },
  // Feiertage
  { month: 1, day: 1, label: 'Neujahr', icon: '\u{1F389}', color: 'amber', country: 'DE', type: 'feiertag', description: 'Neujahr - Vorsaetze, neues Jahr, neue Abenteuer. Perfekt fuer Motivations-Content' },
  { month: 12, day: 25, label: 'Weihnachten', icon: '\u{1F384}', color: 'red', country: 'DE', type: 'feiertag', description: 'Weihnachten - Schueler im Ausland feiern mit Gastfamilien, emotionaler Content' },
  { month: 12, day: 31, label: 'Silvester', icon: '\u{1F386}', color: 'amber', country: 'DE', type: 'feiertag', description: 'Silvester - Jahresrueckblick, Highlights unserer Teilnehmer' },
  { month: 10, day: 3, label: 'Tag der Deutschen Einheit', icon: '\u{1F1E9}\u{1F1EA}', color: 'indigo', country: 'DE', type: 'feiertag', description: 'Tag der Deutschen Einheit - Thema: Weltoffenheit und Voelkerverstaendigung' },
]

// ============================================================
// 12-MONATS CONTENT-KALENDER
// ============================================================

export const MONTHLY_CALENDAR = [
  // ─── JANUAR ────────────────────────────────────────
  {
    month: 1,
    theme: 'Neustart & Aufbruch',
    focus_pillars: ['erfahrungsberichte', 'laender_spotlight', 'fristen_cta'],
    posting_intensity: 'high',
    intensity_reason: 'Neujahrsmotivation + Abreise Australien/NZ + Fruehjahrsbewerbungen starten',
    key_dates: [
      {
        day: 1,
        type: 'feiertag',
        label: 'Neujahr',
        icon: '\u{1F389}',
        color: 'amber',
        description: 'Neues Jahr, neues Abenteuer — Motivations-Content und Jahresvorschau',
        country: 'DE',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Carousel',
          example_headline: 'Neues Jahr, neues Land? 5 Gruende warum 2027 DEIN Jahr wird',
        },
      },
      {
        day: 10,
        type: 'abflugzeit',
        label: 'Abflug USA (Halbjahr)',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Januar-Abreise fuer USA Halbjahresprogramm',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Bye bye Deutschland! Unsere Januar-Abreisenden heben ab \u{2708}\u{FE0F}',
        },
      },
      {
        day: 20,
        type: 'abflugzeit',
        label: 'Abflug Australien/Neuseeland',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Abreisezeitraum fuer Australien & Neuseeland (Ende Januar)',
        country: 'AU',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Story-Serie',
          example_headline: 'Ab nach Down Under! Live-Updates von unseren Australien-Startern',
        },
      },
      {
        day: 26,
        type: 'feiertag',
        label: 'Australia Day',
        icon: '\u{1F1E6}\u{1F1FA}',
        color: 'blue',
        description: 'Australischer Nationalfeiertag',
        country: 'AU',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Carousel',
          example_headline: '10 Dinge die du ueber Australien wissen musst \u{1F1E6}\u{1F1FA}',
        },
      },
    ],
  },

  // ─── FEBRUAR ───────────────────────────────────────
  {
    month: 2,
    theme: 'Bewerbungsphase & Laender-Vergleiche',
    focus_pillars: ['tipps_tricks', 'laender_spotlight', 'fristen_cta'],
    posting_intensity: 'high',
    intensity_reason: 'Hauptbewerbungsphase + Kanada-Abreise + Schulstart Suedhalbkugel',
    key_dates: [
      {
        day: 1,
        type: 'abflugzeit',
        label: 'Abreise Kanada (Semester 2)',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Februar-Abreise fuer Kanada Semester 2',
        country: 'CA',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Auf nach Kanada! Unsere Semester-2-Starter sind unterwegs \u{1F1E8}\u{1F1E6}',
        },
      },
      {
        day: 1,
        type: 'schuljahresbeginn',
        label: 'Schulstart Australien/Neuseeland',
        icon: '\u{1F3EB}',
        color: 'green',
        description: 'Schuljahresbeginn in Australien & Neuseeland (Term 1)',
        country: 'AU',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Erster Schultag in Australien! So sieht der Schulalltag aus',
        },
      },
      {
        day: 6,
        type: 'feiertag',
        label: 'Waitangi Day (Neuseeland)',
        icon: '\u{1F1F3}\u{1F1FF}',
        color: 'green',
        description: 'Neuseelands Nationalfeiertag — Gruendungstag mit Maori-Kultur',
        country: 'NZ',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Carousel',
          example_headline: 'Waitangi Day: So feiert Neuseeland seinen Nationalfeiertag \u{1F1F3}\u{1F1FF}',
        },
      },
      {
        day: 14,
        type: 'content_highlight',
        label: 'Valentinstag / Super Bowl',
        icon: '\u{2764}\u{FE0F}',
        color: 'pink',
        description: 'Valentinstag + Super Bowl Weekend — Pop Culture Content',
        country: 'ALL',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Super Bowl mit der Gastfamilie: So ist es wirklich \u{1F3C8}',
        },
      },
      {
        day: 28,
        type: 'bewerbungsfrist',
        label: 'Fruehbewerbung empfohlen',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Fruehbewerbungen fuer alle Laender empfohlen — beste Chancen sichern',
        country: 'ALL',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Story',
          example_headline: 'Fruehbucher-Vorteil! Jetzt bewerben fuer die besten Plaetze',
        },
      },
    ],
  },

  // ─── MAERZ ────────────────────────────────────────
  {
    month: 3,
    theme: 'Fristen-Countdown & Irland-Spotlight',
    focus_pillars: ['fristen_cta', 'laender_spotlight', 'tipps_tricks'],
    posting_intensity: 'high',
    intensity_reason: 'USA Classic Bewerbungsfrist + JuBi Messe + St. Patrick\'s Day',
    key_dates: [
      {
        day: 1,
        type: 'messe',
        label: 'JuBi Messe Fruehling',
        icon: '\u{1F3AA}',
        color: 'teal',
        description: 'Jugendbildungsmesse (JuBi) - Fruehlingsstermine fuer Highschool-Interessenten',
        country: 'DE',
        content_recommendation: {
          pillar: 'behind_the_scenes',
          post_type: 'Story-Serie',
          example_headline: 'Triff uns auf der JuBi Messe! Alle Infos zum Auslandsjahr \u{1F3AA}',
        },
      },
      {
        day: 17,
        type: 'feiertag',
        label: 'St. Patrick\'s Day (Irland)',
        icon: '\u{2618}\u{FE0F}',
        color: 'green',
        description: 'Irlands groesster Feiertag — Austauschschueler feiern mittendrin',
        country: 'IE',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Reel',
          example_headline: 'St. Patrick\'s Day in Dublin: So feiert Irland! \u{2618}\u{FE0F}\u{1F1EE}\u{1F1EA}',
        },
      },
      {
        day: 31,
        type: 'bewerbungsfrist',
        label: 'Bewerbungsfrist USA Classic',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Bewerbungsschluss fuer USA Classic Programm (Herbstabreise)',
        country: 'US',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Single Image',
          example_headline: 'LETZTE CHANCE: USA Classic Bewerbung nur noch bis 31. Maerz! \u{23F0}',
        },
      },
    ],
  },

  // ─── APRIL ────────────────────────────────────────
  {
    month: 4,
    theme: 'Bewerbungsendspurt & Vorbereitung',
    focus_pillars: ['fristen_cta', 'tipps_tricks', 'faq'],
    posting_intensity: 'high',
    intensity_reason: 'Mehrere Bewerbungsfristen + Osterferien + ANZAC Day',
    key_dates: [
      {
        day: 14,
        type: 'schulferien',
        label: 'Osterferien-Start (BW)',
        icon: '\u{1F423}',
        color: 'pink',
        description: 'Osterferien — perfekte Zeit fuer Infoveranstaltungen und Beratung',
        country: 'DE',
        content_recommendation: {
          pillar: 'tipps_tricks',
          post_type: 'Carousel',
          example_headline: 'Osterferien-Checklist: 5 Schritte zum Auslandsjahr \u{1F4DD}',
        },
      },
      {
        day: 15,
        type: 'bewerbungsfrist',
        label: 'Bewerbungsfrist USA Select',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Bewerbungsschluss fuer USA Select Programm (Herbstabreise)',
        country: 'US',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Story',
          example_headline: 'USA Select: Bewerbung laeuft ab! Sichere dir deinen Platz \u{1F1FA}\u{1F1F8}',
        },
      },
      {
        day: 25,
        type: 'feiertag',
        label: 'ANZAC Day (AU/NZ)',
        icon: '\u{1F3D6}\u{FE0F}',
        color: 'green',
        description: 'Gedenktag in Australien und Neuseeland — kulturelles Erlebnis',
        country: 'AU',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Carousel',
          example_headline: 'Was ist ANZAC Day? So erleben unsere Schueler diesen besonderen Tag',
        },
      },
      {
        day: 30,
        type: 'bewerbungsfrist',
        label: 'Bewerbungsfrist Kanada',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Bewerbungsschluss fuer Kanada-Programme (Herbstabreise)',
        country: 'CA',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Single Image',
          example_headline: 'Kanada wartet! Bewerbungsfrist endet am 30. April \u{1F1E8}\u{1F1E6}',
        },
      },
    ],
  },

  // ─── MAI ──────────────────────────────────────────
  {
    month: 5,
    theme: 'Letzte Fristen & Vorbereitung Herbstabreise',
    focus_pillars: ['fristen_cta', 'tipps_tricks', 'erfahrungsberichte'],
    posting_intensity: 'medium',
    intensity_reason: 'Letzte Bewerbungsfristen + Pfingstferien + Vorbereitungs-Content',
    key_dates: [
      {
        day: 15,
        type: 'bewerbungsfrist',
        label: 'Bewerbungsfrist Irland',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Bewerbungsschluss fuer Irland-Programme (Herbstabreise)',
        country: 'IE',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Story',
          example_headline: 'Letzte Chance Irland! Bewerbung bis 15. Mai \u{1F1EE}\u{1F1EA}',
        },
      },
      {
        day: 26,
        type: 'feiertag',
        label: 'Memorial Day (USA)',
        icon: '\u{1F1FA}\u{1F1F8}',
        color: 'blue',
        description: 'Amerikanischer Gedenktag — Start der Sommerferien in den USA',
        country: 'US',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Reel',
          example_headline: 'Memorial Day Weekend: So feiern Amerikaner den Sommer-Start \u{1F1FA}\u{1F1F8}',
        },
      },
      {
        day: 27,
        type: 'schulferien',
        label: 'Pfingstferien-Start (BW)',
        icon: '\u{1F33B}',
        color: 'green',
        description: 'Pfingstferien — Vorbereitungszeit fuer Herbst-Abreisende',
        country: 'DE',
        content_recommendation: {
          pillar: 'tipps_tricks',
          post_type: 'Carousel',
          example_headline: 'Packliste Auslandsjahr: Das MUSS mit! \u{1F9F3}',
        },
      },
      {
        day: 31,
        type: 'bewerbungsfrist',
        label: 'Bewerbungsfrist Australien/Neuseeland',
        icon: '\u{1F4CB}',
        color: 'red',
        description: 'Bewerbungsschluss fuer Australien & Neuseeland (Januar-Abreise)',
        country: 'AU',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Single Image',
          example_headline: 'Down Under ruft! Australien & NZ Bewerbung bis 31. Mai \u{1F30F}',
        },
      },
    ],
  },

  // ─── JUNI ─────────────────────────────────────────
  {
    month: 6,
    theme: 'Rueckkehrer-Saison & Sommervorbereitung',
    focus_pillars: ['erfahrungsberichte', 'tipps_tricks', 'behind_the_scenes'],
    posting_intensity: 'high',
    intensity_reason: 'Rueckkehrer-Storys + Vorbereitung August-Abreise + Schuljahresende',
    key_dates: [
      {
        day: 1,
        type: 'rueckkehr',
        label: 'Rueckkehr Irland',
        icon: '\u{1F3E0}',
        color: 'purple',
        description: 'Rueckkehrzeitraum fuer Irland-Austauschschueler',
        country: 'IE',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Willkommen zurueck! So war mein Jahr in Irland \u{1F1EE}\u{1F1EA}',
        },
      },
      {
        day: 15,
        type: 'rueckkehr',
        label: 'Rueckkehr USA/Kanada',
        icon: '\u{1F3E0}',
        color: 'purple',
        description: 'Rueckkehrzeitraum fuer USA und Kanada Austauschschueler',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Nach 10 Monaten zurueck: Was hat sich veraendert?',
        },
      },
      {
        day: 20,
        type: 'content_highlight',
        label: 'Rueckkehrer-Interviews starten',
        icon: '\u{1F3A4}',
        color: 'teal',
        description: 'Beste Zeit fuer Rueckkehrer-Interviews und Erfahrungsberichte',
        country: 'ALL',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Carousel',
          example_headline: '10 Dinge die sich nach meinem Auslandsjahr veraendert haben',
        },
      },
    ],
  },

  // ─── JULI ─────────────────────────────────────────
  {
    month: 7,
    theme: 'Sommer-Fernweh & Abreise-Countdown',
    focus_pillars: ['erfahrungsberichte', 'laender_spotlight', 'tipps_tricks'],
    posting_intensity: 'high',
    intensity_reason: 'Sommerferien + Abreise AU/NZ Term 3 + Fernweh-Hochsaison + Canada Day',
    key_dates: [
      {
        day: 1,
        type: 'feiertag',
        label: 'Canada Day',
        icon: '\u{1F1E8}\u{1F1E6}',
        color: 'red',
        description: 'Kanadischer Nationalfeiertag — perfekt fuer Kanada-Spotlight',
        country: 'CA',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Reel',
          example_headline: 'Happy Canada Day! 7 Gruende warum Kanada das perfekte Ziel ist \u{1F1E8}\u{1F1E6}',
        },
      },
      {
        day: 4,
        type: 'feiertag',
        label: 'Independence Day (USA)',
        icon: '\u{1F386}',
        color: 'blue',
        description: 'Amerikanischer Unabhaengigkeitstag — Schueler erleben es hautnah',
        country: 'US',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Reel',
          example_headline: '4th of July in den USA: So haben unsere Schueler gefeiert \u{1F386}',
        },
      },
      {
        day: 10,
        type: 'abflugzeit',
        label: 'Abflug Australien (Term 3)',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Juli-Abreise fuer Australien Term 3',
        country: 'AU',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Auf nach Australien! Unsere Juli-Starter heben ab',
        },
      },
      {
        day: 15,
        type: 'abflugzeit',
        label: 'Abflug Neuseeland (Term 3)',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Juli-Abreise fuer Neuseeland Term 3',
        country: 'NZ',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Kiwi-Abenteuer startet! Live aus Neuseeland \u{1F1F3}\u{1F1FF}',
        },
      },
      {
        day: 25,
        type: 'schulferien',
        label: 'Sommerferien-Start (BW)',
        icon: '\u{2600}\u{FE0F}',
        color: 'amber',
        description: 'Beginn der Sommerferien — Hochsaison fuer Fernweh-Content',
        country: 'DE',
        content_recommendation: {
          pillar: 'laender_spotlight',
          post_type: 'Carousel',
          example_headline: 'Sommerferien und Fernweh? So findest du DEIN Traumland \u{1F30D}',
        },
      },
    ],
  },

  // ─── AUGUST ───────────────────────────────────────
  {
    month: 8,
    theme: 'Abreise-Saison & Emotionaler Content',
    focus_pillars: ['erfahrungsberichte', 'tipps_tricks', 'behind_the_scenes'],
    posting_intensity: 'high',
    intensity_reason: 'Hauptabreise USA/Kanada/Irland - emotionalste Phase des Jahres',
    key_dates: [
      {
        day: 1,
        type: 'content_highlight',
        label: 'Vorbereitungsseminar TREFF',
        icon: '\u{1F393}',
        color: 'teal',
        description: 'TREFF Vorbereitungsseminar fuer alle Herbst-Abreisenden',
        country: 'ALL',
        content_recommendation: {
          pillar: 'behind_the_scenes',
          post_type: 'Story-Serie',
          example_headline: 'Vorbereitungsseminar: So bereiten wir euch aufs Abenteuer vor!',
        },
      },
      {
        day: 15,
        type: 'abflugzeit',
        label: 'Abflug USA/Kanada/Irland',
        icon: '\u{2708}\u{FE0F}',
        color: 'blue',
        description: 'Hauptabreisezeitraum fuer USA, Kanada und Irland (Mitte August)',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Es geht los! Emotionale Abschiede am Flughafen \u{2708}\u{FE0F}\u{1F622}\u{2764}\u{FE0F}',
        },
      },
      {
        day: 20,
        type: 'content_highlight',
        label: 'Erste-Woche-Content',
        icon: '\u{1F4F1}',
        color: 'teal',
        description: 'Schueler berichten von ihrer ersten Woche im Ausland',
        country: 'ALL',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Woche 1 im Ausland: Jetlag, Gastfamilie und erste Eindruecke',
        },
      },
    ],
  },

  // ─── SEPTEMBER ────────────────────────────────────
  {
    month: 9,
    theme: 'Schulstart & Neue Runde Planung',
    focus_pillars: ['erfahrungsberichte', 'faq', 'tipps_tricks'],
    posting_intensity: 'medium',
    intensity_reason: 'Schulstart international + Erfahrungsberichte + neue Interessenten',
    key_dates: [
      {
        day: 1,
        type: 'schuljahresbeginn',
        label: 'Schulstart USA/Kanada/Irland',
        icon: '\u{1F3EB}',
        color: 'green',
        description: 'Schuljahresbeginn in den USA, Kanada und Irland',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Carousel',
          example_headline: 'Erster Schultag im Ausland: Aufregung, Nervositaet und neue Freunde!',
        },
      },
      {
        day: 9,
        type: 'schulferien',
        label: 'Sommerferien-Ende (BW)',
        icon: '\u{1F4DA}',
        color: 'amber',
        description: 'Ende der Sommerferien — neue Schueler starten Planung fuers Auslandsjahr',
        country: 'DE',
        content_recommendation: {
          pillar: 'faq',
          post_type: 'Carousel',
          example_headline: 'Du traemst vom Auslandsjahr? Hier sind Antworten auf deine Top-5-Fragen',
        },
      },
      {
        day: 15,
        type: 'content_highlight',
        label: 'Einleben-Phase Content',
        icon: '\u{1F3E0}',
        color: 'teal',
        description: 'Schueler haben sich eingelebt — erste tiefere Erfahrungsberichte',
        country: 'ALL',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Nach 4 Wochen: Mein Alltag an der Highschool \u{1F3EB}',
        },
      },
    ],
  },

  // ─── OKTOBER ──────────────────────────────────────
  {
    month: 10,
    theme: 'Herbst-Highlights & Stipendien',
    focus_pillars: ['erfahrungsberichte', 'fristen_cta', 'laender_spotlight'],
    posting_intensity: 'medium',
    intensity_reason: 'Stipendien-Deadline + Halloween + Herbstferien + Thanksgiving CA',
    key_dates: [
      {
        day: 3,
        type: 'feiertag',
        label: 'Tag der Deutschen Einheit',
        icon: '\u{1F1E9}\u{1F1EA}',
        color: 'indigo',
        description: 'Thema: Weltoffenheit und Voelkerverstaendigung durch Austausch',
        country: 'DE',
        content_recommendation: {
          pillar: 'infografiken',
          post_type: 'Carousel',
          example_headline: 'Grenzen ueberwinden: Warum ein Auslandsjahr Voelkerverstaendigung schafft',
        },
      },
      {
        day: 14,
        type: 'feiertag',
        label: 'Thanksgiving (Kanada)',
        icon: '\u{1F341}',
        color: 'orange',
        description: 'Kanadisches Erntedankfest — frueher als in den USA',
        country: 'CA',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Mein erstes Thanksgiving in Kanada: Turkey und Ahornsirup \u{1F341}',
        },
      },
      {
        day: 15,
        type: 'stipendium',
        label: 'Stipendien-Bewerbungsfrist',
        icon: '\u{1F393}',
        color: 'amber',
        description: 'Bewerbungsschluss fuer TREFF-Stipendien und Teilstipendien',
        country: 'ALL',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Carousel',
          example_headline: 'TREFF-Stipendium: So bewirbst du dich erfolgreich \u{1F393}\u{1F4B0}',
        },
      },
      {
        day: 28,
        type: 'schulferien',
        label: 'Herbstferien-Start (BW)',
        icon: '\u{1F342}',
        color: 'orange',
        description: 'Herbstferien — Schueler im Ausland berichten, Daheimgebliebene traumen',
        country: 'DE',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Herbstferien im Ausland: Was meine Freunde in der Gastfamilie machen',
        },
      },
      {
        day: 31,
        type: 'feiertag',
        label: 'Halloween (USA/CA/IE)',
        icon: '\u{1F383}',
        color: 'orange',
        description: 'Halloween — ein absolutes Highlight fuer Austauschschueler',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Halloween im Ausland: So gruselig war meine Trick-or-Treat-Nacht \u{1F383}',
        },
      },
    ],
  },

  // ─── NOVEMBER ─────────────────────────────────────
  {
    month: 11,
    theme: 'Messen & Thanksgiving-Stories',
    focus_pillars: ['erfahrungsberichte', 'behind_the_scenes', 'faq'],
    posting_intensity: 'medium',
    intensity_reason: 'JuBi Messe + Thanksgiving USA + Infoveranstaltungen',
    key_dates: [
      {
        day: 1,
        type: 'messe',
        label: 'JuBi Messe Herbst',
        icon: '\u{1F3AA}',
        color: 'teal',
        description: 'Jugendbildungsmesse (JuBi) — Herbsttermine fuer Highschool-Interessenten',
        country: 'DE',
        content_recommendation: {
          pillar: 'behind_the_scenes',
          post_type: 'Story-Serie',
          example_headline: 'JuBi Messe: Komm vorbei und lerne uns kennen! Stand-Nummer folgt \u{1F3AA}',
        },
      },
      {
        day: 15,
        type: 'content_highlight',
        label: 'Infoveranstaltung online',
        icon: '\u{1F4BB}',
        color: 'teal',
        description: 'Online-Infoveranstaltung fuer Eltern und Schueler',
        country: 'DE',
        content_recommendation: {
          pillar: 'fristen_cta',
          post_type: 'Story',
          example_headline: 'Fragen zum Auslandsjahr? Komm zu unserer Online-Info! Link in Bio',
        },
      },
      {
        day: 28,
        type: 'feiertag',
        label: 'Thanksgiving (USA)',
        icon: '\u{1F983}',
        color: 'orange',
        description: 'Amerikanisches Erntedankfest — DER Familienfeiertag in den USA',
        country: 'US',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Carousel',
          example_headline: 'Thanksgiving mit der Gastfamilie: Turkey, Pie und ganz viel Dankbarkeit \u{1F983}',
        },
      },
    ],
  },

  // ─── DEZEMBER ─────────────────────────────────────
  {
    month: 12,
    theme: 'Weihnachten weltweit & Jahresrueckblick',
    focus_pillars: ['erfahrungsberichte', 'laender_spotlight', 'infografiken'],
    posting_intensity: 'medium',
    intensity_reason: 'Weihnachten international + Rueckkehr AU/NZ + Jahresrueckblick',
    key_dates: [
      {
        day: 10,
        type: 'rueckkehr',
        label: 'Rueckkehr Australien/Neuseeland',
        icon: '\u{1F3E0}',
        color: 'purple',
        description: 'Rueckkehrzeitraum fuer Australien & Neuseeland Austauschschueler',
        country: 'AU',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Reel',
          example_headline: 'Von Sommer in den Winter: Unsere Australien-Rueckkehrer sind da! \u{1F1E6}\u{1F1FA}',
        },
      },
      {
        day: 23,
        type: 'schulferien',
        label: 'Weihnachtsferien-Start',
        icon: '\u{1F384}',
        color: 'red',
        description: 'Weihnachtsferien — Familienzeit und Auslandsjahr-Planung',
        country: 'DE',
        content_recommendation: {
          pillar: 'tipps_tricks',
          post_type: 'Carousel',
          example_headline: 'Auslandsjahr unter dem Weihnachtsbaum? So ueberzeugst du deine Eltern \u{1F384}',
        },
      },
      {
        day: 25,
        type: 'feiertag',
        label: 'Weihnachten',
        icon: '\u{1F384}',
        color: 'red',
        description: 'Weihnachten — Schueler im Ausland feiern mit Gastfamilien',
        country: 'ALL',
        content_recommendation: {
          pillar: 'erfahrungsberichte',
          post_type: 'Story-Serie',
          example_headline: 'Weihnachten in 5 Laendern: So feiern unsere Schueler weltweit \u{1F30D}\u{1F384}',
        },
      },
      {
        day: 31,
        type: 'content_highlight',
        label: 'Jahresrueckblick',
        icon: '\u{1F386}',
        color: 'amber',
        description: 'Silvester & Jahresrueckblick — die Highlights des TREFF-Jahres',
        country: 'ALL',
        content_recommendation: {
          pillar: 'infografiken',
          post_type: 'Carousel',
          example_headline: 'TREFF 2026 in Zahlen: X Schueler, 5 Laender, unzaehlige Abenteuer \u{1F389}',
        },
      },
    ],
  },
]

// ============================================================
// HELPER FUNCTIONS
// ============================================================

/**
 * Get the month config for a given month number (1-12).
 * @param {number} month - Month number (1-12)
 * @returns {MonthConfig|undefined}
 */
export function getMonthConfig(month) {
  return MONTHLY_CALENDAR.find(m => m.month === month)
}

/**
 * Get all key dates for a specific month.
 * @param {number} month - Month number (1-12)
 * @returns {KeyDate[]}
 */
export function getKeyDatesForMonth(month) {
  const config = getMonthConfig(month)
  return config ? config.key_dates : []
}

/**
 * Get all key dates across all months.
 * @returns {Array<KeyDate & { month: number }>}
 */
export function getAllKeyDates() {
  const dates = []
  for (const monthConfig of MONTHLY_CALENDAR) {
    for (const keyDate of monthConfig.key_dates) {
      dates.push({ ...keyDate, month: monthConfig.month })
    }
  }
  return dates
}

/**
 * Count total key dates in the calendar.
 * @returns {number}
 */
export function getTotalKeyDateCount() {
  return MONTHLY_CALENDAR.reduce((sum, m) => sum + m.key_dates.length, 0)
}

/**
 * Convert key dates for a specific month/year to the seasonalMarkers format
 * used by CalendarView.vue (compatible with the existing API response format).
 *
 * @param {number} month - Month number (1-12)
 * @param {number} year - Year (e.g. 2026)
 * @returns {Array<{ date: string, type: string, label: string, icon: string, color: string, description: string }>}
 */
export function toSeasonalMarkers(month, year) {
  const keyDates = getKeyDatesForMonth(month)
  return keyDates.map(kd => {
    // Ensure day is valid for the given month/year
    const lastDay = new Date(year, month, 0).getDate()
    const day = Math.min(kd.day, lastDay)
    // Use manual formatting to avoid UTC timezone shift from toISOString()
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`

    return {
      date: dateStr,
      type: kd.type,
      label: kd.label,
      icon: kd.icon,
      color: kd.color,
      description: kd.description,
    }
  })
}

/**
 * Get departure waves for a specific country.
 * @param {string} countryCode - Country code (US|CA|AU|NZ|IE)
 * @returns {DepartureWave|undefined}
 */
export function getDepartureWave(countryCode) {
  return DEPARTURE_WAVES.find(dw => dw.country_code === countryCode)
}

/**
 * Get all departure dates for a specific month.
 * @param {number} month - Month number (1-12)
 * @returns {Array<{ country: string, flag: string, departure: DeparturePeriod }>}
 */
export function getDeparturesForMonth(month) {
  const results = []
  for (const wave of DEPARTURE_WAVES) {
    for (const dep of wave.departures) {
      if (dep.month === month) {
        results.push({
          country: wave.country,
          flag: wave.flag,
          country_code: wave.country_code,
          departure: dep,
        })
      }
    }
  }
  return results
}

/**
 * Get international holidays for a specific month.
 * @param {number} month - Month number (1-12)
 * @returns {Array}
 */
export function getInternationalHolidaysForMonth(month) {
  return INTERNATIONAL_HOLIDAYS.filter(h => h.month === month)
}

/**
 * Get German holidays/school breaks for a specific month.
 * @param {number} month - Month number (1-12)
 * @returns {Array}
 */
export function getGermanHolidaysForMonth(month) {
  return GERMAN_HOLIDAYS.filter(h => h.month === month)
}

/**
 * Get content recommendation for a specific key date.
 * @param {number} month - Month number (1-12)
 * @param {number} day - Day of month
 * @returns {ContentRecommendation|null}
 */
export function getContentRecommendation(month, day) {
  const config = getMonthConfig(month)
  if (!config) return null
  const keyDate = config.key_dates.find(kd => kd.day === day)
  return keyDate ? keyDate.content_recommendation : null
}

/**
 * Get posting intensity for a specific month.
 * @param {number} month - Month number (1-12)
 * @returns {{ intensity: string, reason: string }|null}
 */
export function getPostingIntensity(month) {
  const config = getMonthConfig(month)
  if (!config) return null
  return {
    intensity: config.posting_intensity,
    reason: config.intensity_reason,
  }
}

/**
 * Get key dates filtered by country.
 * @param {string} countryCode - Country code (US|CA|AU|NZ|IE|DE|ALL)
 * @returns {Array<KeyDate & { month: number }>}
 */
export function getKeyDatesByCountry(countryCode) {
  return getAllKeyDates().filter(
    kd => kd.country === countryCode || kd.country === 'ALL'
  )
}

/**
 * Get key dates filtered by type.
 * @param {string} type - Date type (bewerbungsfrist|abflugzeit|rueckkehr|schuljahresbeginn|feiertag|schulferien|messe|stipendium|content_highlight)
 * @returns {Array<KeyDate & { month: number }>}
 */
export function getKeyDatesByType(type) {
  return getAllKeyDates().filter(kd => kd.type === type)
}
