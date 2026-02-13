/**
 * Page-level tour configurations.
 *
 * Each key corresponds to a route name (matching Vue Router name) or a custom
 * page key.  The value is an object with:
 *   - title:       Human-readable tour title (shown in header)
 *   - steps[]:     Array of { target, title, description, position }
 *
 * target uses CSS selectors – preferably [data-tour="..."] attributes that we
 * add to the relevant page elements.
 *
 * position: 'top' | 'bottom' | 'left' | 'right'
 */

const tourConfigs = {
  // ─── Dashboard ───────────────────────────────────────────
  dashboard: {
    title: 'Dashboard Tour',
    steps: [
      {
        target: '[data-tour="sidebar"]',
        title: 'Navigation',
        description:
          'Hier findest du alle Bereiche der App: Dashboard, Posts erstellen, Vorlagen, Assets, Kalender und mehr.',
        position: 'right',
      },
      {
        target: '[data-tour="create-post"]',
        title: 'Post erstellen',
        description:
          'Erstelle neue Social-Media-Posts mit KI-gestuetzter Textgenerierung und professionellen Vorlagen.',
        position: 'right',
      },
      {
        target: '[data-tour="templates"]',
        title: 'Vorlagen',
        description:
          'Waehle aus vorgefertigten Templates fuer Instagram und TikTok, die du individuell anpassen kannst.',
        position: 'right',
      },
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Dein Dashboard',
        description:
          'Behalte den Ueberblick ueber deine Posts, geplante Inhalte und Assets auf einen Blick.',
        position: 'bottom',
      },
      {
        target: '[data-tour="quick-actions"]',
        title: 'Schnellzugriff',
        description:
          'Starte direkt mit dem Erstellen eines Posts oder oeffne den Kalender fuer die Planung.',
        position: 'bottom',
      },
    ],
  },

  // ─── Create Post ─────────────────────────────────────────
  'create-post': {
    title: 'Post erstellen Tour',
    steps: [
      {
        target: '[data-tour="cp-stepper"]',
        title: 'Schritt-fuer-Schritt',
        description:
          'Der Post-Ersteller fuehrt dich in 8 Schritten durch den Prozess: Typ, Land, Vorlage, Text, Bild, Vorschau, Bearbeiten und Veroeffentlichen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-content"]',
        title: 'Inhalt bearbeiten',
        description:
          'In jedem Schritt kannst du Inhalte auswaehlen und anpassen. Die Live-Vorschau zeigt dir sofort, wie dein Post aussehen wird.',
        position: 'bottom',
      },
    ],
  },

  // ─── Templates ───────────────────────────────────────────
  templates: {
    title: 'Vorlagen Tour',
    steps: [
      {
        target: '[data-tour="tpl-header"]',
        title: 'Template-Uebersicht',
        description:
          'Hier siehst du alle verfuegbaren Vorlagen. Filtere nach Kategorie oder Plattform, um schnell die passende Vorlage zu finden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-filters"]',
        title: 'Filter & Suche',
        description:
          'Nutze die Filter, um Vorlagen nach Kategorie (z.B. Laender, FAQs, Motivation) oder Plattform (Instagram Feed, Story, TikTok) einzugrenzen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-grid"]',
        title: 'Vorlagen-Galerie',
        description:
          'Klicke auf eine Vorlage, um sie in der Vorschau zu oeffnen, anzupassen oder als Basis fuer einen neuen Post zu verwenden.',
        position: 'top',
      },
    ],
  },

  // ─── Assets ──────────────────────────────────────────────
  assets: {
    title: 'Assets Tour',
    steps: [
      {
        target: '[data-tour="assets-tabs"]',
        title: 'Bibliothek & Stockfotos',
        description:
          'Wechsle zwischen deiner eigenen Medienbibliothek und der Stockfoto-Suche (Unsplash/Pexels).',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-upload"]',
        title: 'Dateien hochladen',
        description:
          'Ziehe Bilder oder Videos per Drag & Drop hierher, oder klicke zum Auswaehlen. Unterstuetzte Formate: JPG, PNG, GIF, MP4, WebM.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-filters"]',
        title: 'Filter & Suche',
        description:
          'Durchsuche deine Assets nach Name, filtere nach Typ (Bild/Video), Kategorie oder Land.',
        position: 'bottom',
      },
    ],
  },

  // ─── Calendar ────────────────────────────────────────────
  calendar: {
    title: 'Kalender Tour',
    steps: [
      {
        target: '[data-tour="cal-toolbar"]',
        title: 'Kalender-Navigation',
        description:
          'Navigiere zwischen Monaten, wechsle zwischen Monats-, Wochen- und Warteschlangen-Ansicht, und filtere nach Plattform.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-grid"]',
        title: 'Kalender-Uebersicht',
        description:
          'Ziehe unveroffentlichte Posts per Drag & Drop auf einen Tag, um sie zu planen. Luecken werden automatisch hervorgehoben.',
        position: 'top',
      },
      {
        target: '[data-tour="cal-sidebar"]',
        title: 'Unveroffentlichte Entwuerfe',
        description:
          'Hier siehst du alle Entwuerfe, die noch keinem Datum zugeordnet sind. Ziehe sie einfach in den Kalender.',
        position: 'left',
      },
    ],
  },

  // ─── History ─────────────────────────────────────────────
  history: {
    title: 'Post-Verlauf Tour',
    steps: [
      {
        target: '[data-tour="history-filters"]',
        title: 'Filter & Suche',
        description:
          'Durchsuche deine Posts nach Titel, filtere nach Kategorie, Plattform, Status, Land oder Datum.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-list"]',
        title: 'Post-Liste',
        description:
          'Hier siehst du alle erstellten Posts mit Vorschaubild, Titel, Status und Aktionen (Bearbeiten, Duplizieren, Loeschen).',
        position: 'top',
      },
    ],
  },

  // ─── Analytics ───────────────────────────────────────────
  analytics: {
    title: 'Analytics Tour',
    steps: [
      {
        target: '[data-tour="analytics-header"]',
        title: 'Dein Content-Dashboard',
        description:
          'Behalte den Ueberblick ueber deine Posting-Aktivitaet, Ziel-Erreichung und Content-Mix.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-charts"]',
        title: 'Charts & Statistiken',
        description:
          'Visualisiere deine Posting-Frequenz, Kategorie-Verteilung und Plattform-Aufteilung ueber verschiedene Zeitraeume.',
        position: 'top',
      },
    ],
  },

  // ─── Settings ────────────────────────────────────────────
  settings: {
    title: 'Einstellungen Tour',
    steps: [
      {
        target: '[data-tour="settings-sections"]',
        title: 'Einstellungen verwalten',
        description:
          'Passe dein Profil, Branding-Farben, API-Schluessel, Posting-Ziele, Hashtag-Strategien und Tour-Einstellungen an.',
        position: 'bottom',
      },
    ],
  },

  // ─── Students ────────────────────────────────────────────
  students: {
    title: 'Schueler Tour',
    steps: [
      {
        target: '[data-tour="students-header"]',
        title: 'Schueler-Verwaltung',
        description:
          'Erstelle und verwalte Schueler-Profile. Jeder Schueler kann einem Post zugeordnet werden und bekommt ein eigenes Persoenlichkeits-Preset fuer die KI-Textgenerierung.',
        position: 'bottom',
      },
      {
        target: '[data-tour="students-list"]',
        title: 'Schueler-Karten',
        description:
          'Klicke auf einen Schueler, um sein Profil und verknuepfte Posts zu sehen. Bearbeite Name, Land, Schule und Persoenlichkeit.',
        position: 'top',
      },
    ],
  },

  // ─── Story Arcs ──────────────────────────────────────────
  'story-arcs': {
    title: 'Story-Arcs Tour',
    steps: [
      {
        target: '[data-tour="arcs-header"]',
        title: 'Serien-Management',
        description:
          'Story-Arcs sind mehrteilige Content-Serien. Erstelle zusammenhaengende Episoden, die eine Geschichte ueber mehrere Posts erzaehlen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-list"]',
        title: 'Deine Serien',
        description:
          'Hier siehst du alle Serien mit Fortschrittsanzeige, Episoden-Anzahl und Status. Klicke auf eine Serie fuer Details.',
        position: 'top',
      },
    ],
  },

  // ─── Week Planner ────────────────────────────────────────
  'week-planner': {
    title: 'Wochenplaner Tour',
    steps: [
      {
        target: '[data-tour="wp-controls"]',
        title: 'Planungs-Optionen',
        description:
          'Waehle die Woche, Anzahl Posts pro Woche, und ob wiederkehrende Formate und Story-Serien beruecksichtigt werden sollen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-grid"]',
        title: 'Wochen-Raster',
        description:
          'Die KI schlaegt Posts fuer jeden Tag vor. Verschiebe sie per Drag & Drop, entferne ungewollte, und uebernimm den Plan mit einem Klick.',
        position: 'top',
      },
    ],
  },

  // ─── Recurring Formats ───────────────────────────────────
  'recurring-formats': {
    title: 'Wiederkehrende Formate Tour',
    steps: [
      {
        target: '[data-tour="formats-header"]',
        title: 'Running Gags & Formate',
        description:
          'Definiere wiederkehrende Content-Formate wie "Motivation Monday" oder "Freitags-Fail", die automatisch im Wochenplaner vorgeschlagen werden.',
        position: 'bottom',
      },
    ],
  },

  // ─── Video Export ────────────────────────────────────────
  'video-export': {
    title: 'Video-Export Tour',
    steps: [
      {
        target: '[data-tour="ve-header"]',
        title: 'Video-Export',
        description:
          'Exportiere deine Videos in verschiedenen Seitenverhaeltnissen (9:16, 1:1, 4:5) fuer Instagram Reels, Feed und TikTok.',
        position: 'bottom',
      },
    ],
  },

  // ─── Audio Mixer ─────────────────────────────────────────
  'audio-mixer': {
    title: 'Audio-Mixer Tour',
    steps: [
      {
        target: '[data-tour="am-header"]',
        title: 'Audio-Mixer',
        description:
          'Fuege Hintergrundmusik und Audio-Layer zu deinen Videos hinzu. Waehle aus der Musik-Bibliothek oder lade eigene Tracks hoch.',
        position: 'bottom',
      },
    ],
  },

  // ─── Thumbnail Generator ─────────────────────────────────
  'thumbnail-generator': {
    title: 'Thumbnail-Generator Tour',
    steps: [
      {
        target: '[data-tour="tg-header"]',
        title: 'Thumbnails erstellen',
        description:
          'Erstelle ansprechende Thumbnails fuer deine Videos und Reels mit Text-Overlays, TREFF-Branding und verschiedenen Layouts.',
        position: 'bottom',
      },
    ],
  },
}

export default tourConfigs
