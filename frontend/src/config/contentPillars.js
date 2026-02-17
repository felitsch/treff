/**
 * Content Pillars Configuration
 *
 * TypeScript-like interface definition and static configuration for the
 * TREFF Sprachreisen Content Pillars. These are the thematic categories
 * that structure all social media content.
 *
 * Interface ContentPillar {
 *   id: string                    // Unique pillar identifier
 *   name: string                  // Display name
 *   description: string           // Detailed description
 *   targetPercentage: number      // Target distribution percentage (should sum to 100)
 *   color: string                 // Brand color for UI display
 *   icon: string                  // Emoji icon
 *   buyerJourneyStage: string[]   // Which buyer journey stages this pillar serves
 *   platforms: string[]           // Recommended platforms
 *   formats: string[]             // Recommended content formats
 *   exampleTopics: string[]       // Example topic ideas
 *   kpis: string[]                // Key performance indicators to track
 * }
 */

export const CONTENT_PILLARS = [
  {
    id: 'erfahrungsberichte',
    name: 'Erfahrungsberichte & Testimonials',
    description: 'Echte Geschichten von TREFF-Teilnehmern: Vor, waehrend und nach dem Auslandsjahr. Der emotionale Kern unserer Strategie.',
    targetPercentage: 30,
    color: '#E74C3C',
    icon: '📝',
    buyerJourneyStage: ['awareness', 'consideration'],
    platforms: ['instagram_feed', 'instagram_story', 'tiktok'],
    formats: ['Carousel', 'Reel', 'Story-Serie', 'Interview-Clip'],
    exampleTopics: [
      'Mein erster Tag an der High School',
      'Gastfamilie: Erwartung vs. Realitaet',
      'Was ich nach 3 Monaten gelernt habe',
      'Abschied nehmen — und warum es sich lohnt',
      '5 Dinge die ich vermisse (und 5 die ich liebe)',
      'Rueckkehrer-Interview: Ein Jahr spaeter',
    ],
    kpis: ['Saves', 'Shares', 'Comments', 'Story Replies'],
  },
  {
    id: 'laender_spotlight',
    name: 'Laender-Spotlights & Destination Content',
    description: 'Informative und inspirierende Inhalte ueber unsere 5 Ziellaender. Fakten, Highlights, Vergleiche.',
    targetPercentage: 20,
    color: '#3498DB',
    icon: '🌍',
    buyerJourneyStage: ['awareness', 'consideration'],
    platforms: ['instagram_feed', 'instagram_story', 'tiktok'],
    formats: ['Carousel', 'Infografik', 'Reel', 'Quiz-Story'],
    exampleTopics: [
      'USA vs. Kanada: Welches Land passt zu dir?',
      '10 Fakten ueber Australien die du nicht wusstest',
      'So sieht ein typischer Schultag in Neuseeland aus',
      'Irland: Mehr als nur Regen und Kobolde',
      'Kanada-Special: Englisch ODER Franzoesisch?',
      'Die schoensten Highschool-Campusse der Welt',
    ],
    kpis: ['Reach', 'Saves', 'Profile Visits'],
  },
  {
    id: 'tipps_tricks',
    name: 'Tipps, Tricks & Guides',
    description: 'Praktische Ratschlaege fuer Bewerbung, Vorbereitung, Packliste, Alltag im Ausland. Mehrwert-Content der geteilt wird.',
    targetPercentage: 20,
    color: '#F39C12',
    icon: '💡',
    buyerJourneyStage: ['consideration', 'decision'],
    platforms: ['instagram_feed', 'instagram_story', 'tiktok'],
    formats: ['Carousel', 'Listicle', 'How-To Reel', 'Checklisten-Story'],
    exampleTopics: [
      'Packliste Auslandsjahr: Das muss mit!',
      'Bewerbung Schritt fuer Schritt erklaert',
      'So findest du die perfekte Gastfamilie',
      'Heimweh? 5 Tipps die wirklich helfen',
      'Schule im Ausland: So funktioniert die Anerkennung',
      'Budget-Guide: So viel Taschengeld brauchst du',
    ],
    kpis: ['Saves', 'Shares', 'Website Clicks'],
  },
  {
    id: 'fristen_cta',
    name: 'Fristen, CTAs & Conversion',
    description: 'Bewerbungsfristen, Stipendien-Infos, direkte Handlungsaufforderungen. Conversion-optimiert aber nicht aufdringlich.',
    targetPercentage: 10,
    color: '#E67E22',
    icon: '⏰',
    buyerJourneyStage: ['decision'],
    platforms: ['instagram_feed', 'instagram_story'],
    formats: ['Single Image', 'Story mit Countdown', 'Reel'],
    exampleTopics: [
      'Bewerbungsfrist USA Classic: Noch 30 Tage!',
      'Stipendium sichern — jetzt bewerben',
      'Platze fuer Kanada 2027 fast vergeben',
      'Infoveranstaltung: Komm vorbei!',
      'Elternabend online: Alle Fragen beantwortet',
    ],
    kpis: ['Website Clicks', 'Link Taps', 'DM Inquiries'],
  },
  {
    id: 'faq',
    name: 'FAQ & Wissenswertes',
    description: 'Haeufig gestellte Fragen beantwortet. Baut Vertrauen auf und reduziert Hemmschwelle zur Kontaktaufnahme.',
    targetPercentage: 10,
    color: '#9B59B6',
    icon: '❓',
    buyerJourneyStage: ['consideration', 'decision'],
    platforms: ['instagram_feed', 'instagram_story', 'tiktok'],
    formats: ['Carousel', 'Story-Highlight', 'Reel'],
    exampleTopics: [
      'Wie viel kostet ein Auslandsjahr?',
      'Brauche ich ein Visum?',
      'Was passiert wenn ich krank werde?',
      'Kann ich mir die Gastfamilie aussuchen?',
      'Werde ich die Klasse wiederholen muessen?',
      'Ab welchem Alter kann ich teilnehmen?',
    ],
    kpis: ['Saves', 'DM Inquiries', 'Website Clicks'],
  },
  {
    id: 'behind_the_scenes',
    name: 'Behind the Scenes & Team',
    description: 'Einblicke ins TREFF-Team, Bueroalltag, Events, Messen. Macht die Marke menschlich und nahbar.',
    targetPercentage: 5,
    color: '#1ABC9C',
    icon: '🎬',
    buyerJourneyStage: ['awareness', 'consideration'],
    platforms: ['instagram_story', 'instagram_feed', 'tiktok'],
    formats: ['Story', 'Reel', 'Foto-Post'],
    exampleTopics: [
      'Ein Tag im TREFF-Buero',
      'Wir auf der JuBi Messe',
      'Team-Vorstellung: Wer steckt hinter TREFF?',
      'So bereiten wir eure Unterlagen vor',
      'Unser Lieblingsland (Team-Voting)',
    ],
    kpis: ['Engagement Rate', 'Follower Growth', 'Story Views'],
  },
  {
    id: 'infografiken',
    name: 'Infografiken & Daten',
    description: 'Visuelle Aufbereitung von Statistiken, Vergleichen, Prozessen. Hochgradig teilbar und speicherbar.',
    targetPercentage: 5,
    color: '#2ECC71',
    icon: '📊',
    buyerJourneyStage: ['awareness', 'consideration'],
    platforms: ['instagram_feed', 'instagram_story'],
    formats: ['Carousel', 'Single Image', 'Story'],
    exampleTopics: [
      'Highschool-Aufenthalt in Zahlen',
      'Kostenvergleich: 5 Laender im Ueberblick',
      'Timeline: Vom Traum zum Abflug',
      'Sprachfortschritt-Kurve: Monat 1-10',
    ],
    kpis: ['Saves', 'Shares', 'Reach'],
  },
]

/**
 * Get a pillar by ID
 * @param {string} id - Pillar ID
 * @returns {object|undefined}
 */
export function getPillarById(id) {
  return CONTENT_PILLARS.find(p => p.id === id)
}

/**
 * Get all pillar IDs
 * @returns {string[]}
 */
export function getPillarIds() {
  return CONTENT_PILLARS.map(p => p.id)
}

/**
 * Map a post category to its corresponding content pillar ID.
 * Categories like 'foto_posts', 'reel_tiktok_thumbnails', 'story_posts' etc.
 * are post formats, not pillars — they map to the closest pillar.
 */
export const CATEGORY_TO_PILLAR = {
  laender_spotlight: 'laender_spotlight',
  erfahrungsberichte: 'erfahrungsberichte',
  infografiken: 'infografiken',
  fristen_cta: 'fristen_cta',
  tipps_tricks: 'tipps_tricks',
  faq: 'faq',
  foto_posts: 'behind_the_scenes',
  reel_tiktok_thumbnails: 'erfahrungsberichte',
  story_posts: 'behind_the_scenes',
  story_teaser: 'erfahrungsberichte',
  story_series: 'erfahrungsberichte',
  behind_the_scenes: 'behind_the_scenes',
}

/**
 * Get the pillar for a given category
 * @param {string} category - Post category ID
 * @returns {object|undefined}
 */
export function getPillarForCategory(category) {
  const pillarId = CATEGORY_TO_PILLAR[category] || category
  return getPillarById(pillarId)
}
