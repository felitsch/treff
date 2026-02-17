/**
 * Hook-Formeln-Konfiguration fuer den KI-Text-Generator
 *
 * Bewiesene Hook-Formeln fuer die TREFF-Zielgruppe (deutsche Teenager 14-18).
 * Hooks sind die ersten 1-3 Sekunden (Video) oder die erste Zeile (Caption),
 * die zum Weiterlesen/Weiterschauen animieren.
 *
 * Jede Formel enthaelt:
 * - id: Eindeutiger Bezeichner
 * - name: Anzeigename (deutsch)
 * - template: Vorlage mit Platzhaltern
 * - examples: 3+ Beispiele fuer TREFF-Kontext
 * - platforms: Fuer welche Plattformen geeignet
 * - effectiveness: Bewertung 1-10 (basierend auf Social-Media-Studien)
 * - category: Hook-Kategorie (curiosity|emotion|urgency|comparison|list)
 * - tip: Anwendungs-Tipp fuer den User
 *
 * Integration:
 * - AITextGenerator.vue (Hook-Vorschlaege beim Generieren)
 * - CreatePostView.vue (Hook-Auswahl in Step 4)
 * - backend/app/core/strategy_loader.py (AI Prompt-Erweiterung)
 *
 * @module hookFormulas
 * @see frontend/src/components/common/AITextGenerator.vue
 * @see frontend/src/config/social-content.json - Quell-Daten
 * @see backend/app/core/strategy_loader.py - Backend-Integration
 */

// ═══════════════════════════════════════════════════════════════════
// HOOK FORMULAS
// ═══════════════════════════════════════════════════════════════════

export const HOOK_FORMULAS = [
  {
    id: 'knowledge_gap',
    name: 'Wissensluecke',
    template: 'Was ich gerne VOR meinem Auslandsjahr gewusst haette...',
    examples: [
      'Was ich gerne VOR meinem Auslandsjahr in den USA gewusst haette...',
      '3 Dinge, die mir NIEMAND ueber Kanada gesagt hat',
      'Das hat mir keiner ueber Gastfamilien erzaehlt...',
    ],
    platforms: ['instagram_feed', 'instagram_reels', 'tiktok'],
    effectiveness: 9,
    category: 'curiosity',
    tip: 'Funktioniert besonders gut mit Erfahrungsberichten und Rueckkehrer-Content',
  },
  {
    id: 'comparison',
    name: 'Vergleich',
    template: '{Land A} vs. {Land B}: Welches Land passt zu dir?',
    examples: [
      'USA vs. Kanada: Welches Land passt zu dir?',
      'Australien vs. Neuseeland: Der ultimative Vergleich',
      'Irland oder USA? Die ehrliche Wahrheit',
    ],
    platforms: ['instagram_feed', 'instagram_reels', 'tiktok'],
    effectiveness: 8,
    category: 'comparison',
    tip: 'Ideal fuer Laender-Spotlights und Entscheidungshilfe-Content',
  },
  {
    id: 'myth_buster',
    name: 'Mythos-Entlarvung',
    template: 'MYTHOS: {Verbreitete Annahme}. Die Wahrheit ist...',
    examples: [
      'MYTHOS: Ein Auslandsjahr ist nur was fuer Reiche. Die Wahrheit...',
      'MYTHOS: Du musst perfekt Englisch koennen. Falsch!',
      '3 Luegen ueber Gastfamilien, die du nicht glauben solltest',
    ],
    platforms: ['instagram_feed', 'instagram_reels', 'tiktok'],
    effectiveness: 9,
    category: 'curiosity',
    tip: 'Raeumt mit Vorurteilen auf — baut Vertrauen bei Eltern und Schuelern',
  },
  {
    id: 'pov',
    name: 'POV (Point of View)',
    template: 'POV: {Situation aus der Ich-Perspektive}',
    examples: [
      'POV: Dein erster Tag an einer amerikanischen High School',
      'POV: Du oeffnest den Brief mit deiner Gastfamilien-Zuteilung',
      'POV: Dein letzter Tag im Auslandsjahr und du musst dich verabschieden',
    ],
    platforms: ['instagram_reels', 'tiktok'],
    effectiveness: 8,
    category: 'emotion',
    tip: 'Perfekt fuer Video-Content — versetzt den Zuschauer direkt in die Situation',
  },
  {
    id: 'list',
    name: 'Nummerierte Liste',
    template: '{Zahl} Dinge/Gruende/Tipps fuer {Thema}',
    examples: [
      '5 Gruende, warum DU ein Auslandsjahr machen solltest',
      '7 Dinge, die in deine Auslandsjahr-Packliste muessen',
      '3 Fehler, die JEDER Austauschschueler macht',
    ],
    platforms: ['instagram_feed', 'instagram_reels', 'tiktok'],
    effectiveness: 8,
    category: 'list',
    tip: 'Hohe Save-Rate — Nutzer speichern Listen fuer spaeter',
  },
  {
    id: 'question',
    name: 'Direkte Frage',
    template: '{Provokante oder neugierig machende Frage}?',
    examples: [
      'Wuerdest du fuer 10 Monate bei einer fremden Familie leben?',
      'Was wuerdest du tun, wenn du ploetzlich an einer US-High School aufwachst?',
      'Wie fuehlt es sich an, 10.000 km von zuhause entfernt zu sein?',
    ],
    platforms: ['instagram_feed', 'instagram_stories', 'tiktok'],
    effectiveness: 7,
    category: 'curiosity',
    tip: 'Steigert Kommentar-Rate — User wollen antworten',
  },
  {
    id: 'expectation_reality',
    name: 'Erwartung vs. Realitaet',
    template: 'Erwartung: {Was man denkt} vs. Realitaet: {Wie es wirklich ist}',
    examples: [
      'Erwartung: Amerikanische High Schools sind wie in den Filmen. Realitaet: ...',
      'Was meine Eltern dachten vs. Was wirklich passiert ist',
      'Instagram vs. Realitaet: Mein Auslandsjahr',
    ],
    platforms: ['instagram_reels', 'tiktok'],
    effectiveness: 9,
    category: 'comparison',
    tip: 'Viral-Format — hohes Share-Potenzial wegen Relatable-Faktor',
  },
  {
    id: 'emotional_opener',
    name: 'Emotionaler Einstieg',
    template: '{Emotionale Aussage, die Empathie weckt}',
    examples: [
      'Der Moment, in dem ich am Flughafen stand und realisiert habe: Jetzt bin ich wirklich alleine.',
      'Ich hab in meinem Auslandsjahr mehr ueber mich gelernt als in 16 Jahren zuhause.',
      'Die schwerste und gleichzeitig beste Entscheidung meines Lebens.',
    ],
    platforms: ['instagram_feed', 'instagram_reels', 'tiktok'],
    effectiveness: 8,
    category: 'emotion',
    tip: 'Erzeugt tiefe Verbindung — ideal fuer Rueckkehrer-Stories und Abschieds-Content',
  },
  {
    id: 'countdown_urgency',
    name: 'Countdown/Dringlichkeit',
    template: 'Nur noch {Zeitraum} bis {Deadline/Event}!',
    examples: [
      'Nur noch 30 Tage bis Bewerbungsschluss!',
      'LETZTE CHANCE: Plaetze fuer USA 2027 fast ausgebucht!',
      'In 6 Monaten koenntest du HIER sein. Aber nur, wenn du dich JETZT bewirbst.',
    ],
    platforms: ['instagram_feed', 'instagram_stories', 'tiktok'],
    effectiveness: 7,
    category: 'urgency',
    tip: 'Conversion-stark — nur bei echten Fristen einsetzen, sonst verliert es Glaubwuerdigkeit',
  },
  {
    id: 'behind_scenes',
    name: 'Behind the Scenes',
    template: 'So sieht {Thema} WIRKLICH aus / Was {Person} WIRKLICH macht',
    examples: [
      'So sieht ein normaler Schultag in den USA WIRKLICH aus',
      'Behind the Scenes: So bereiten wir euch auf das Auslandsjahr vor',
      'Was deine Gastfamilie WIRKLICH ueber dich denkt',
    ],
    platforms: ['instagram_stories', 'instagram_reels', 'tiktok'],
    effectiveness: 7,
    category: 'curiosity',
    tip: 'Authentizitaet und Transparenz — staerkt das Vertrauen in die Marke',
  },
]

// ═══════════════════════════════════════════════════════════════════
// HOOK CATEGORIES
// ═══════════════════════════════════════════════════════════════════

export const HOOK_CATEGORIES = {
  curiosity: {
    id: 'curiosity',
    name: 'Neugier wecken',
    description: 'Erzeugt eine Wissenslucke, die den User zum Weiterlesen motiviert',
    icon: '🔍',
    color: '#3B82F6',
  },
  emotion: {
    id: 'emotion',
    name: 'Emotion ausloesen',
    description: 'Spricht Gefuehle an — Fernweh, Aufregung, Nostalgie',
    icon: '💛',
    color: '#EF4444',
  },
  urgency: {
    id: 'urgency',
    name: 'Dringlichkeit',
    description: 'FOMO und Zeitdruck — motiviert zur sofortigen Handlung',
    icon: '⏰',
    color: '#F59E0B',
  },
  comparison: {
    id: 'comparison',
    name: 'Vergleich',
    description: 'Stellt zwei Optionen gegeneinander — regt zur Diskussion an',
    icon: '⚖️',
    color: '#8B5CF6',
  },
  list: {
    id: 'list',
    name: 'Liste/Aufzaehlung',
    description: 'Nummerierte Inhalte — hohe Save-Rate und Shareability',
    icon: '📝',
    color: '#10B981',
  },
}

// ═══════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

/**
 * Get a hook formula by ID.
 * @param {string} id - Hook formula ID
 * @returns {object|undefined}
 */
export function getHookById(id) {
  return HOOK_FORMULAS.find(h => h.id === id)
}

/**
 * Get hook formulas filtered by platform.
 * @param {string} platformId - Platform ID (e.g., 'instagram_feed')
 * @returns {object[]}
 */
export function getHooksForPlatform(platformId) {
  return HOOK_FORMULAS.filter(h => h.platforms.includes(platformId))
}

/**
 * Get hook formulas filtered by category.
 * @param {string} categoryId - Category ID (curiosity|emotion|urgency|comparison|list)
 * @returns {object[]}
 */
export function getHooksByCategory(categoryId) {
  return HOOK_FORMULAS.filter(h => h.category === categoryId)
}

/**
 * Get hooks sorted by effectiveness (highest first).
 * @param {string} [platformId] - Optional platform filter
 * @returns {object[]}
 */
export function getHooksSortedByEffectiveness(platformId) {
  let hooks = [...HOOK_FORMULAS]
  if (platformId) {
    hooks = hooks.filter(h => h.platforms.includes(platformId))
  }
  return hooks.sort((a, b) => b.effectiveness - a.effectiveness)
}

/**
 * Get a random weighted hook (higher effectiveness = higher chance).
 * @param {string} [platformId] - Optional platform filter
 * @returns {object}
 */
export function getRandomWeightedHook(platformId) {
  let hooks = HOOK_FORMULAS
  if (platformId) {
    hooks = hooks.filter(h => h.platforms.includes(platformId))
  }
  if (hooks.length === 0) return HOOK_FORMULAS[0]

  const totalWeight = hooks.reduce((sum, h) => sum + h.effectiveness, 0)
  let random = Math.random() * totalWeight
  for (const hook of hooks) {
    random -= hook.effectiveness
    if (random <= 0) return hook
  }
  return hooks[hooks.length - 1]
}

/**
 * Get all unique hook categories used in formulas.
 * @returns {Array<{ id: string, name: string, count: number }>}
 */
export function getHookCategorySummary() {
  const counts = {}
  for (const hook of HOOK_FORMULAS) {
    counts[hook.category] = (counts[hook.category] || 0) + 1
  }
  return Object.entries(HOOK_CATEGORIES).map(([id, cat]) => ({
    ...cat,
    count: counts[id] || 0,
  }))
}

/**
 * Format a hook template with provided values.
 * @param {string} template - Template string with {placeholders}
 * @param {Record<string, string>} values - Values to replace placeholders
 * @returns {string}
 */
export function formatHookTemplate(template, values = {}) {
  let result = template
  for (const [key, value] of Object.entries(values)) {
    result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), value)
  }
  return result
}
