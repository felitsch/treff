<script setup>
/**
 * UIShowcaseView.vue — Component showcase for TREFF Design System UI library.
 * Displays all TButton, TBadge, TInput, TModal, TEmptyState, TCountryAccent
 * variants in a single scrollable page for visual verification.
 */
import { ref } from 'vue'
import {
  TButton,
  TBadge,
  TInput,
  TModal,
  TEmptyState,
  TCountryAccent,
  TCountryThemeProvider,
} from '@/components/ui'

// Input states
const inputValue = ref('')
const textareaValue = ref('')

// Modal states
const showSmModal = ref(false)
const showMdModal = ref(false)
const showLgModal = ref(false)
const showFullModal = ref(false)

// Loading button state
const isLoading = ref(false)
function simulateLoading() {
  isLoading.value = true
  setTimeout(() => { isLoading.value = false }, 2000)
}
</script>

<template>
  <div class="max-w-5xl mx-auto py-8 px-4 space-y-12">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
      UI Component Showcase
    </h1>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TButton -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TButton</h2>

      <!-- Variants -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Variants</h3>
        <div class="flex flex-wrap gap-3">
          <TButton variant="primary">Primary</TButton>
          <TButton variant="secondary">Secondary</TButton>
          <TButton variant="ghost">Ghost</TButton>
          <TButton variant="danger">Danger</TButton>
        </div>
      </div>

      <!-- Sizes -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Sizes</h3>
        <div class="flex flex-wrap items-center gap-3">
          <TButton size="sm">Small</TButton>
          <TButton size="md">Medium</TButton>
          <TButton size="lg">Large</TButton>
        </div>
      </div>

      <!-- States -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">States</h3>
        <div class="flex flex-wrap items-center gap-3">
          <TButton :loading="isLoading" @click="simulateLoading">
            {{ isLoading ? 'Laden...' : 'Click to Load' }}
          </TButton>
          <TButton disabled>Disabled</TButton>
          <TButton variant="danger" :loading="true">Deleting...</TButton>
        </div>
      </div>

      <!-- With Icons -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">With Icons</h3>
        <div class="flex flex-wrap items-center gap-3">
          <TButton variant="primary">
            <template #icon-left>
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </template>
            Erstellen
          </TButton>
          <TButton variant="secondary">
            Download
            <template #icon-right>
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </template>
          </TButton>
        </div>
      </div>

      <!-- Block -->
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Block (Full Width)</h3>
        <div class="max-w-md">
          <TButton block>Full Width Button</TButton>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TBadge -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TBadge</h2>

      <!-- Variants -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Status Variants</h3>
        <div class="flex flex-wrap gap-2">
          <TBadge variant="draft">Entwurf</TBadge>
          <TBadge variant="scheduled">Geplant</TBadge>
          <TBadge variant="exported">Exportiert</TBadge>
          <TBadge variant="posted">Gepostet</TBadge>
          <TBadge variant="error">Fehler</TBadge>
          <TBadge variant="info">Info</TBadge>
          <TBadge variant="warning">Warnung</TBadge>
        </div>
      </div>

      <!-- With Dot -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">With Dot Indicator</h3>
        <div class="flex flex-wrap gap-2">
          <TBadge variant="draft" dot>Entwurf</TBadge>
          <TBadge variant="scheduled" dot>Geplant</TBadge>
          <TBadge variant="posted" dot>Gepostet</TBadge>
          <TBadge variant="error" dot>Fehler</TBadge>
        </div>
      </div>

      <!-- Sizes -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Sizes</h3>
        <div class="flex flex-wrap items-center gap-2">
          <TBadge variant="info" size="sm">Small</TBadge>
          <TBadge variant="info" size="md">Medium</TBadge>
        </div>
      </div>

      <!-- Removable -->
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Removable</h3>
        <div class="flex flex-wrap gap-2">
          <TBadge variant="info" removable>Hashtag</TBadge>
          <TBadge variant="posted" removable dot>Active Tag</TBadge>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TInput -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TInput</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
        <!-- Default -->
        <TInput
          v-model="inputValue"
          label="Post-Titel"
          placeholder="z.B. Mein Auslandsjahr in Kanada"
          helper-text="Maximal 100 Zeichen"
        />

        <!-- Required -->
        <TInput
          label="Pflichtfeld"
          placeholder="Dieses Feld ist erforderlich"
          required
        />

        <!-- Error state -->
        <TInput
          label="E-Mail"
          placeholder="name@example.com"
          type="email"
          error="Bitte gib eine gueltige E-Mail-Adresse ein."
          model-value="ungueltig"
        />

        <!-- Disabled -->
        <TInput
          label="Deaktiviert"
          placeholder="Nicht bearbeitbar"
          disabled
          model-value="Fester Wert"
        />

        <!-- Sizes -->
        <TInput
          label="Kleine Eingabe"
          size="sm"
          placeholder="Klein..."
        />

        <TInput
          label="Grosse Eingabe"
          size="lg"
          placeholder="Gross..."
        />

        <!-- With prefix/suffix -->
        <TInput
          label="Mit Prefix-Icon"
          placeholder="Suchen..."
        >
          <template #prefix>
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </template>
        </TInput>

        <!-- Textarea -->
        <TInput
          v-model="textareaValue"
          label="Beschreibung"
          placeholder="Erzaehle von deinem Erlebnis..."
          textarea
          :rows="4"
        />
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TModal -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TModal</h2>

      <div class="flex flex-wrap gap-3">
        <TButton variant="secondary" @click="showSmModal = true">Small Modal</TButton>
        <TButton variant="secondary" @click="showMdModal = true">Medium Modal</TButton>
        <TButton variant="secondary" @click="showLgModal = true">Large Modal</TButton>
        <TButton variant="secondary" @click="showFullModal = true">Full Modal</TButton>
      </div>

      <!-- Small Modal -->
      <TModal v-model="showSmModal" size="sm" title="Bestaetigung">
        <p class="text-gray-600 dark:text-gray-400">
          Moechtest du diesen Post wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden.
        </p>
        <template #footer>
          <TButton variant="ghost" @click="showSmModal = false">Abbrechen</TButton>
          <TButton variant="danger" @click="showSmModal = false">Loeschen</TButton>
        </template>
      </TModal>

      <!-- Medium Modal -->
      <TModal v-model="showMdModal" size="md" title="Post bearbeiten">
        <div class="space-y-4">
          <TInput label="Titel" placeholder="Post-Titel eingeben..." model-value="Mein Auslandsjahr" />
          <TInput label="Beschreibung" textarea placeholder="Was moechtest du erzaehlen?" />
        </div>
        <template #footer>
          <TButton variant="ghost" @click="showMdModal = false">Abbrechen</TButton>
          <TButton variant="primary" @click="showMdModal = false">Speichern</TButton>
        </template>
      </TModal>

      <!-- Large Modal -->
      <TModal v-model="showLgModal" size="lg" title="Template-Vorschau">
        <div class="text-gray-600 dark:text-gray-400">
          <p class="mb-4">Dies ist ein großes Modal für umfangreichere Inhalte wie Template-Vorschauen oder Detailansichten.</p>
          <div class="grid grid-cols-3 gap-4">
            <div v-for="i in 6" :key="i" class="aspect-square rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400">
              {{ i }}
            </div>
          </div>
        </div>
        <template #footer>
          <TButton variant="ghost" @click="showLgModal = false">Schließen</TButton>
        </template>
      </TModal>

      <!-- Full Modal -->
      <TModal v-model="showFullModal" size="full" title="Vollbild-Editor">
        <div class="text-gray-600 dark:text-gray-400 h-full flex items-center justify-center">
          <TEmptyState
            icon="photo"
            title="Vollbild-Modus"
            description="Dieses Modal nutzt den gesamten Bildschirm für maximalen Arbeitsbereich."
          />
        </div>
        <template #footer>
          <TButton variant="ghost" @click="showFullModal = false">Schließen</TButton>
        </template>
      </TModal>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TEmptyState -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TEmptyState</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="border border-gray-200 dark:border-gray-700 rounded-xl">
          <TEmptyState
            icon="inbox"
            title="Keine Posts vorhanden"
            description="Erstelle deinen ersten Post, um loszulegen."
            action-label="Post erstellen"
            action-route="/create"
          />
        </div>

        <div class="border border-gray-200 dark:border-gray-700 rounded-xl">
          <TEmptyState
            icon="search"
            title="Keine Ergebnisse"
            description="Versuche einen anderen Suchbegriff."
            compact
          />
        </div>

        <div class="border border-gray-200 dark:border-gray-700 rounded-xl">
          <TEmptyState
            icon="calendar"
            title="Kalender ist leer"
            description="Plane deine ersten Posts für die nächste Woche."
            action-label="Zum Kalender"
            action-route="/calendar"
          />
        </div>

        <div class="border border-gray-200 dark:border-gray-700 rounded-xl">
          <TEmptyState
            icon="users"
            title="Keine Schüler"
            description="Schüler-Profile werden hier angezeigt."
            compact
          />
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: TCountryAccent -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section>
      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">TCountryAccent</h2>

      <!-- Border Left -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Border Left</h3>
        <div class="space-y-3">
          <TCountryAccent country="usa" mode="border-left" v-slot="{ emoji, label }">
            <div class="pl-3 py-2">{{ emoji }} {{ label }} — Highschool-Aufenthalt</div>
          </TCountryAccent>
          <TCountryAccent country="canada" mode="border-left" v-slot="{ emoji, label }">
            <div class="pl-3 py-2">{{ emoji }} {{ label }} — Highschool-Aufenthalt</div>
          </TCountryAccent>
          <TCountryAccent country="australia" mode="border-left" v-slot="{ emoji, label }">
            <div class="pl-3 py-2">{{ emoji }} {{ label }} — Highschool-Aufenthalt</div>
          </TCountryAccent>
          <TCountryAccent country="newzealand" mode="border-left" v-slot="{ emoji, label }">
            <div class="pl-3 py-2">{{ emoji }} {{ label }} — Highschool-Aufenthalt</div>
          </TCountryAccent>
          <TCountryAccent country="ireland" mode="border-left" v-slot="{ emoji, label }">
            <div class="pl-3 py-2">{{ emoji }} {{ label }} — Highschool-Aufenthalt</div>
          </TCountryAccent>
        </div>
      </div>

      <!-- Border Top -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Border Top</h3>
        <div class="grid grid-cols-5 gap-3">
          <TCountryAccent v-for="c in ['usa', 'canada', 'australia', 'newzealand', 'ireland']" :key="c" :country="c" mode="border-top" v-slot="{ emoji, label }">
            <div class="pt-3 pb-2 text-center text-sm">
              <div class="text-lg">{{ emoji }}</div>
              <div class="text-gray-600 dark:text-gray-400">{{ label }}</div>
            </div>
          </TCountryAccent>
        </div>
      </div>

      <!-- Gradient Bar -->
      <div class="mb-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Gradient Bar</h3>
        <div class="space-y-3">
          <TCountryAccent v-for="c in ['usa', 'canada', 'australia', 'newzealand', 'ireland']" :key="c" :country="c" mode="gradient-bar" rounded v-slot="{ emoji, label }">
            <div class="p-3 text-sm text-gray-700 dark:text-gray-300">{{ emoji }} {{ label }}</div>
          </TCountryAccent>
        </div>
      </div>

      <!-- Background Mode -->
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">Background</h3>
        <div class="grid grid-cols-5 gap-3">
          <TCountryAccent v-for="c in ['usa', 'canada', 'australia', 'newzealand', 'ireland']" :key="c" :country="c" mode="bg" rounded v-slot="{ emoji, label }">
            <div class="p-4 text-center text-sm rounded-lg">
              <div class="text-2xl mb-1">{{ emoji }}</div>
              <div class="font-medium text-gray-700 dark:text-gray-300">{{ label }}</div>
            </div>
          </TCountryAccent>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- SECTION: Dark Mode Toggle Hint -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <section class="pb-12">
      <div class="text-center text-sm text-gray-400 dark:text-gray-500">
        Alle Komponenten unterstuetzen Dark Mode — Toggle via Einstellungen.
      </div>
    </section>
  </div>
</template>
