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
    title: 'Dashboard Tour – Deine Content-Zentrale',
    steps: [
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Willkommen im Dashboard!',
        description:
          'Das Dashboard ist deine Zentrale fuer alles rund um Social-Media-Content. Von hier aus startest du alle Workflows: Posts erstellen, planen, analysieren und optimieren. Lass uns die einzelnen Bereiche kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Quick-Stats: Dein Ueberblick',
        description:
          'Diese Karten zeigen dir auf einen Blick: "Posts diese Woche" zaehlt alle Posts der aktuellen Woche, "Geplante Posts" zeigt vorbereitete Inhalte im Kalender, und "Gesamt Assets" zaehlt deine hochgeladenen Bilder und Videos.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-calendar"]',
        title: 'Mini-Kalender: Naechste 7 Tage',
        description:
          'Der Mini-Kalender zeigt die kommende Woche mit blauen Punkten fuer geplante Posts. So erkennst du auf einen Blick, an welchen Tagen Content ansteht – und wo noch Luecken sind. Fuer die volle Kalender-Ansicht nutze den Kalender-Button.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-recent-posts"]',
        title: 'Letzte Posts',
        description:
          'Hier siehst du deine neuesten Posts mit Plattform-Icon, Titel, Kategorie und Status (Entwurf, Geplant, Veroeffentlicht). Klicke auf einen Post, um ihn direkt zu bearbeiten. "Alle anzeigen" fuehrt zum vollstaendigen Post-Verlauf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-suggestions"]',
        title: 'KI Content-Vorschlaege',
        description:
          'Die KI analysiert deinen bisherigen Content und schlaegt passende neue Themen vor – basierend auf Saison, Laender-Rotation, Kategorie-Balance und Content-Luecken. Klicke "Annehmen" um einen Vorschlag direkt als Post zu erstellen, oder "Generieren" fuer neue Ideen.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-recycling"]',
        title: 'Content-Recycling',
        description:
          'Posts aelter als 90 Tage erscheinen hier als Recycling-Vorschlaege. Statt neuen Content zu erstellen, kannst du erfolgreiche alte Posts auffrischen und wiederverwenden. Evergreen-Posts eignen sich besonders gut dafuer.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-series-status"]',
        title: 'Serien-Status',
        description:
          'Verfolge den Fortschritt deiner Story-Arcs (mehrteilige Content-Serien). Du siehst den Status jeder Serie, die aktuelle Episode, einen Fortschrittsbalken und wann die naechste Episode faellig ist. So verpasst du keine Fortsetzung!',
        position: 'top',
      },
      {
        target: '[data-tour="quick-actions"]',
        title: 'Quick-Actions: Deine Shortcuts',
        description:
          'Mit diesen Buttons startest du direkt die wichtigsten Aktionen: "Post erstellen" fuehrt zum Post-Editor mit KI-Unterstuetzung, "Kalender anzeigen" oeffnet die volle Kalender-Ansicht zum Planen und Terminieren. Das Dashboard ist dein Startpunkt fuer jeden Workflow!',
        position: 'bottom',
      },
    ],
  },

  // ─── Create Post (Ausfuehrliche Wizard-Tour) ─────────────
  'create-post': {
    title: 'Post-Wizard Tour',
    steps: [
      // Tour-Step 1: Ueberblick ueber den 9-Schritt-Wizard
      {
        target: '[data-tour="cp-content"]',
        title: 'Willkommen im Post-Wizard!',
        description:
          'Der Post-Ersteller fuehrt dich in 9 Schritten durch den kompletten Prozess: Von der Kategorie-Auswahl ueber KI-Textgenerierung bis zum fertigen Export. Jeder Schritt baut auf dem vorherigen auf — so entsteht in Minuten ein professioneller Social-Media-Post mit konsistentem TREFF-Branding. Die Schritt-Anzeige oben hilft dir, den Ueberblick zu behalten.',
        position: 'bottom',
      },
      // Tour-Step 2: Kategorie-Auswahl erklaeren
      {
        target: '[data-tour="cp-step-1"]',
        title: 'Schritt 1: Kategorie waehlen',
        description:
          'Im ersten Schritt waehlst du die Art deines Posts: Laender-Spotlight fuer Zielland-Infos, Erfahrungsberichte fuer Alumni-Stories, Tipps & Tricks fuer praktische Ratschlaege, Fristen & CTA fuer Bewerbungsfristen, oder FAQ fuer haeufige Fragen. WARUM? Die Kategorie bestimmt, welche Templates und KI-Texte vorgeschlagen werden — so passt alles perfekt zusammen und dein Content-Mix bleibt ausgewogen.',
        position: 'bottom',
      },
      // Tour-Step 3: Template-Auswahl erklaeren
      {
        target: '[data-tour="cp-step-2"]',
        title: 'Schritt 2: Template waehlen',
        description:
          'Templates sind vorgefertigte Design-Vorlagen mit TREFF-Branding. Jedes Template hat ein festes Layout (Headline, Body, CTA-Button) und bestimmt, wie viele Slides dein Post hat. WARUM? Unterschiedliche Templates betonen verschiedene Aspekte — ein "Laender-Spotlight" zeigt Fakten mit Flagge, ein "Erfahrungsbericht" betont den Schueler-Stil. Die richtige Vorlage spart Design-Arbeit und schafft Wiedererkennungswert.',
        position: 'bottom',
      },
      // Tour-Step 4: AI Textgenerierung erklaeren — was Gemini macht und wie man Ergebnisse anpassen kann
      {
        target: '[data-tour="cp-step-5"]',
        title: 'Schritt 5: KI-Textgenerierung (Gemini AI)',
        description:
          'Hier generiert Google Gemini AI automatisch alle Texte: Headlines, Body-Texte, Captions und Hashtags — basierend auf Kategorie, Land, Thema und Tonalitaet. WARUM KI? Du sparst Stunden an Copywriting und erhaelst sofort professionelle Texte im richtigen Stil. Ergebnisse anpassen: In Schritt 7 kannst du jedes einzelne Feld manuell bearbeiten oder per "Neu generieren"-Button von der KI ueberarbeiten lassen.',
        position: 'bottom',
      },
      // Tour-Step 5: Slide-Editor erklaeren (Drag-and-Drop, Bilder einfuegen, Text anpassen)
      {
        target: '[data-tour="cp-step-7"]',
        title: 'Schritt 7: Slide-Editor (Drag & Drop)',
        description:
          'Der Slide-Editor ist das Herzstuck des Wizards: Ordne deine Slides per Drag & Drop in die optimale Reihenfolge, bearbeite Headlines, Subheadlines und Body-Texte direkt, und fuege neue Slides hinzu oder entferne sie. WARUM? Die Reihenfolge der Slides bestimmt die Story deines Posts — der erste Slide muss fesseln (Hook), der letzte soll zum Handeln auffordern (CTA). Jedes Textfeld hat ein Zeichenlimit mit farbiger Warnung.',
        position: 'bottom',
      },
      // Tour-Step 6: Caption und Hashtags erklaeren (warum wichtig fuer Reichweite)
      {
        target: '[data-tour="cp-step-6"]',
        title: 'Captions & Hashtags (Reichweiten-Turbo)',
        description:
          'In Schritt 7 bearbeitest du Instagram- und TikTok-Captions getrennt voneinander, denn jede Plattform hat eigene Regeln (Instagram: max 2.200 Zeichen, TikTok: kuerzer und knackiger). WARUM? Gute Captions und Hashtags steigern die Reichweite enorm — der Algorithmus zeigt deinen Post mehr Menschen. Nutze den gruenen Sparkle-Button fuer KI-optimierte Hashtag-Vorschlaege und die Emoji-Strategie-Engine.',
        position: 'bottom',
      },
      // Tour-Step 7: CTA erklaeren (Call-to-Action fuer mehr Interaktion)
      {
        target: '[data-tour="cp-step-8"]',
        title: 'CTA: Call-to-Action (Warum unverzichtbar)',
        description:
          'Ein Call-to-Action fordert den Betrachter zum Handeln auf — z.B. "Jetzt bewerben!", "Link in Bio" oder "Speichern fuer spaeter". WARUM? Ohne CTA scrollen Nutzer einfach weiter, MIT CTA steigt die Interaktionsrate um bis zu 300%! In Schritt 7 findest du die CTA-Bibliothek mit 35 vorgefertigten CTAs in 4 Kategorien (Engagement, Conversion, Awareness, Traffic) — kontextbasiert vorgeschlagen fuer maximale Wirkung.',
        position: 'bottom',
      },
      // Tour-Step 8: Hook erklaeren (erster Satz/Slide der Aufmerksamkeit erregt)
      {
        target: '[data-tour="cp-step-9"]',
        title: 'Hook: Die ersten 2 Sekunden entscheiden',
        description:
          'Der Hook ist der allererste Satz oder die erste Slide deines Posts — er entscheidet in 1-2 Sekunden, ob jemand weiterliest oder weiterscrollt! WARUM? Instagram und TikTok zeigen deinen Post zunaechst nur kurz — nur ein fesselnder Hook stoppt den Daumen. Beispiele: "Wusstest du, dass...?", "Die 3 groessten Fehler beim Auslandsjahr" oder "Unpopular Opinion:...". Den Hook-Selector findest du in Schritt 5 nach der Textgenerierung.',
        position: 'bottom',
      },
      // Tour-Step 9: Interaktive Elemente und Engagement-Boost erklaeren
      {
        target: '[data-tour="cp-navigation"]',
        title: 'Interaktive Elemente & Engagement-Boost',
        description:
          'Interaktive Sticker wie Umfragen, Quizze, Slider und Frage-Sticker machen deine Instagram Stories lebendig. WARUM? Sie steigern die Verweildauer und werden vom Algorithmus bevorzugt — dein Post wird MEHR Menschen gezeigt! Der Engagement-Boost-Panel in der Vorschau analysiert deinen Post und schlaegt konkrete Verbesserungen vor: z.B. eine Frage am Ende, einen kontroversen Aufhaenger oder einen Countdown fuer Bewerbungsfristen.',
        position: 'top',
      },
      // Tour-Step 10: Multi-Plattform Anpassung erklaeren (Instagram vs TikTok)
      {
        target: '[data-tour="cp-step-3"]',
        title: 'Multi-Plattform: Instagram vs TikTok',
        description:
          'In Schritt 3 waehlst du eine oder mehrere Plattformen gleichzeitig. WARUM Multi-Plattform? Instagram Feed nutzt 1:1 oder 4:5-Format, Instagram Stories und TikTok nutzen 9:16 (Hochformat). Captions, Hashtags und Bild-Formate werden automatisch fuer jede Plattform angepasst — beim Export erhaelst du separate, optimierte Dateien. So erreichst du mit einem Workflow Teenager auf TikTok UND Eltern auf Instagram!',
        position: 'bottom',
      },
      // Tour-Step 11: Preview und Export erklaeren
      {
        target: '[data-tour="cp-tour-btn"]',
        title: 'Vorschau, Export & Speichern',
        description:
          'In Schritt 6 siehst du eine Live-Vorschau deines Posts mit Plattform-Wechsel. In Schritt 8 waehlst du optional ein Hintergrundbild aus der Asset-Bibliothek oder laesst die KI eines generieren. In Schritt 9 exportierst du den fertigen Post als PNG oder ZIP (bei Multi-Slides), speicherst ihn als Entwurf oder planst ihn direkt im Kalender. Tipp: Du kannst diese Tour jederzeit ueber diesen Button erneut starten!',
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
        title: 'Was sind Templates?',
        description:
          'Templates sind vorgefertigte Design-Vorlagen fuer deine Social-Media-Posts. Sie sorgen fuer ein konsistentes TREFF-Branding und sparen dir Zeit bei der Erstellung — jeder Post sieht professionell aus, ohne dass du jedes Mal bei null anfangen musst.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-filters"]',
        title: 'Template-Galerie filtern',
        description:
          'Nutze die Filter, um Vorlagen nach Kategorie (z.B. Laender-Spotlight, FAQ, Erfahrungsberichte) oder Plattform-Format (Instagram Feed, Story, TikTok) einzugrenzen. Die Galerie zeigt dir die Anzahl der Treffer und gruppiert Templates nach Kategorie.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-grid"]',
        title: 'Live-Preview-Editor',
        description:
          'Klicke auf ein Template, um den Live-Preview-Editor zu oeffnen. Dort siehst du in Echtzeit, wie dein Post mit dem gewaehlten Template aussehen wird. Du kannst Texte, Farben und Schriftarten direkt anpassen — jede Aenderung wird sofort in der Vorschau sichtbar.',
        position: 'top',
      },
      {
        target: '[data-tour="tpl-create-btn"]',
        title: 'Farben, Fonts & Brand-Identitaet',
        description:
          'Im Anpassungs-Panel des Editors kannst du Primaer-, Sekundaer- und Hintergrundfarben aendern, Ueberschrift- und Fliesstext-Schriftarten waehlen und alle Texte bearbeiten. Erstelle mit dem "+"-Button auch komplett eigene Templates mit eigenem HTML/CSS-Code.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-video-hint"]',
        title: 'Video-Templates',
        description:
          'Neben Post-Templates gibt es auch spezielle Video-Templates fuer Reels und TikToks. Diese findest du auf einer separaten Seite unter "Video-Branding" in der Seitenleiste — dort kannst du Intros, Outros, Lower Thirds und Overlay-Vorlagen verwalten.',
        position: 'top',
      },
    ],
  },

  // ─── Assets ──────────────────────────────────────────────
  assets: {
    title: 'Assets Tour – Deine Medienverwaltung',
    steps: [
      {
        target: '[data-tour="assets-header"]',
        title: 'Willkommen in der Asset-Bibliothek!',
        description:
          'Die Asset-Bibliothek ist deine zentrale Medienverwaltung. Hier lagerst du alle Bilder, Videos und Audio-Dateien, die du fuer deine Social-Media-Posts brauchst. Von hier aus kannst du Dateien hochladen, organisieren, bearbeiten und in Posts einbinden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-upload"]',
        title: 'Dateien hochladen – Drag & Drop',
        description:
          'Ziehe Bilder, Videos oder Audio-Dateien einfach per Drag & Drop in diesen Bereich — oder klicke zum Auswaehlen. Unterstuetzte Formate: JPG, PNG, WebP (bis 20 MB), MP4, MOV, WebM (bis 500 MB) und MP3, WAV, AAC (bis 50 MB). Unter dem Upload-Bereich kannst du direkt Kategorie, Land und Tags vergeben.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-grid"]',
        title: 'Crop-Tool & Video-Trimmer',
        description:
          'Bewege die Maus ueber ein Asset, um die Bearbeitungs-Buttons zu sehen: Bei Bildern erscheint ein Crop-Button zum Zuschneiden (z.B. auf Instagram-Formate 1:1, 4:5, 9:16). Bei Videos gibt es einen Trim-Button zum Kuerzen und einen Audio-Mix-Button. So bereitest du Medien direkt hier fuer Social Media vor — ohne externe Tools.',
        position: 'top',
      },
      {
        target: '[data-tour="assets-filters"]',
        title: 'Kategorisierung, Tagging & Suche',
        description:
          'Nutze die Filter, um deine Assets schnell zu finden: Suche nach Dateiname oder Tags, filtere nach Kategorie (Logo, Hintergrund, Foto, Icon, Laenderbild, Video), nach Land (USA, Kanada, Australien, Neuseeland, Irland) oder nach Dateityp (JPG, PNG, WebP, Video, Audio). Aktive Filter werden als Chips angezeigt und lassen sich einzeln entfernen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-tabs"]',
        title: 'Stock-Foto-Integration (Unsplash & Pexels)',
        description:
          'Klicke auf den Tab "Stock Fotos", um kostenlose Stock-Fotos von Unsplash oder Pexels zu durchsuchen. Gib einen englischen Suchbegriff ein (z.B. "highschool campus", "australia landscape") und importiere passende Fotos direkt in deine Bibliothek. So findest du schnell professionelle Bilder fuer deine Posts.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-usage-hint"]',
        title: 'Assets in Posts & Videos verwenden',
        description:
          'Deine Assets werden automatisch im Post-Editor (Schritt 5: Bild) zur Auswahl angeboten. Auch im Video-Composer, Video-Export und Thumbnail-Generator kannst du auf deine Bibliothek zugreifen. Tipp: Tagge deine Assets mit dem passenden Land und der Kategorie — so werden sie beim Erstellen eines Posts automatisch vorgefiltert!',
        position: 'top',
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
