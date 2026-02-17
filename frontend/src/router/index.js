import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// ─── Route definitions ──────────────────────────────────────────────
// Organized into 7 sections: home, create, calendar, library, students, analytics, settings
// All views use lazy loading (dynamic imports) for code-splitting.

const routes = [
  // ─── Public routes (no auth required) ─────────────────────
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { requiresAuth: false },
  },

  // ─── Authenticated app shell ──────────────────────────────
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Root redirect
      {
        path: '',
        redirect: '/home',
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 1: HOME
      // ═══════════════════════════════════════════════════════
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 2: CREATE (Content-Erstellung)
      // ═══════════════════════════════════════════════════════
      {
        path: 'create',
        name: 'CreateHub',
        component: () => import('@/views/CreateHubView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }, { label: 'Erstellen', path: '/create' }],
        },
      },
      {
        path: 'create/quick',
        name: 'CreateQuick',
        component: () => import('@/views/PostCreatorView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Quick Post', path: '/create/quick' },
          ],
        },
      },
      {
        path: 'create/smart',
        name: 'CreateSmart',
        component: () => import('@/views/create/SmartCreateView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Smart Create',
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Smart Create', path: '/create/smart' },
          ],
        },
      },
      {
        path: 'create/advanced',
        name: 'CreateAdvanced',
        component: () => import('@/views/CreatePostView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Erweiterter Modus', path: '/create/advanced' },
          ],
        },
      },
      {
        path: 'create/video',
        name: 'CreateVideo',
        component: () => import('@/views/create/VideoCreateView.vue'),
        meta: {
          requiresAuth: true,
          title: 'Brand This Video',
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Brand This Video', path: '/create/video' },
          ],
        },
      },
      {
        path: 'create/campaign',
        name: 'CreateCampaign',
        component: () => import('@/views/WeekPlannerView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Kampagne', path: '/create/campaign' },
          ],
        },
      },
      {
        path: 'create/post/:id/edit',
        name: 'EditPost',
        component: () => import('@/views/EditPostView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Bearbeiten', path: '' },
          ],
        },
      },

      {
        path: 'create/drafts',
        name: 'DraftsList',
        component: () => import('@/views/DraftsListView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Erstellen', path: '/create' },
            { label: 'Entwuerfe', path: '/create/drafts' },
          ],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 3: CALENDAR (Planung)
      // ═══════════════════════════════════════════════════════
      {
        path: 'calendar',
        name: 'Calendar',
        component: () => import('@/views/CalendarView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }, { label: 'Kalender', path: '/calendar' }],
        },
      },
      {
        path: 'calendar/week-planner',
        name: 'WeekPlanner',
        component: () => import('@/views/WeekPlannerView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Kalender', path: '/calendar' },
            { label: 'Wochenplaner', path: '/calendar/week-planner' },
          ],
        },
      },
      {
        path: 'calendar/story-arcs',
        name: 'StoryArcs',
        component: () => import('@/views/StoryArcsView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Kalender', path: '/calendar' },
            { label: 'Story-Arcs', path: '/calendar/story-arcs' },
          ],
        },
      },
      {
        path: 'calendar/story-arcs/:id',
        name: 'StoryArcDetail',
        component: () => import('@/views/StoryArcDetailView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Kalender', path: '/calendar' },
            { label: 'Story-Arcs', path: '/calendar/story-arcs' },
            { label: 'Detail', path: '' },
          ],
        },
      },
      {
        path: 'calendar/story-arc-wizard',
        name: 'StoryArcWizard',
        component: () => import('@/views/StoryArcWizardView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Kalender', path: '/calendar' },
            { label: 'Story-Arcs', path: '/calendar/story-arcs' },
            { label: 'Wizard', path: '' },
          ],
        },
      },
      {
        path: 'calendar/recurring-formats',
        name: 'RecurringFormats',
        component: () => import('@/views/RecurringFormatsView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Kalender', path: '/calendar' },
            { label: 'Formate', path: '/calendar/recurring-formats' },
          ],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 4: LIBRARY (Bibliothek)
      // ═══════════════════════════════════════════════════════
      {
        path: 'library',
        component: () => import('@/views/LibraryView.vue'),
        meta: {
          requiresAuth: true,
        },
        children: [
          {
            path: '',
            redirect: '/library/assets',
          },
          {
            path: 'templates',
            name: 'Templates',
            component: () => import('@/views/TemplatesView.vue'),
            meta: {
              requiresAuth: true,
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Bibliothek', path: '/library' },
                { label: 'Templates', path: '/library/templates' },
              ],
            },
          },
          {
            path: 'template-gallery',
            name: 'TemplateGallery',
            component: () => import('@/views/TemplateGalleryView.vue'),
            meta: {
              requiresAuth: true,
              title: 'Template-Galerie',
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Bibliothek', path: '/library' },
                { label: 'Template-Galerie', path: '/library/template-gallery' },
              ],
            },
          },
          {
            path: 'template-editor',
            name: 'TemplateEditor',
            component: () => import('@/views/TemplateEditorView.vue'),
            meta: {
              requiresAuth: true,
              title: 'Template-Editor',
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Bibliothek', path: '/library' },
                { label: 'Template-Editor', path: '/library/template-editor' },
              ],
            },
          },
          {
            path: 'assets',
            name: 'Assets',
            component: () => import('@/views/AssetsView.vue'),
            meta: {
              requiresAuth: true,
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Bibliothek', path: '/library' },
                { label: 'Assets', path: '/library/assets' },
              ],
            },
          },
          {
            path: 'history',
            name: 'History',
            component: () => import('@/views/HistoryView.vue'),
            meta: {
              requiresAuth: true,
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Bibliothek', path: '/library' },
                { label: 'History', path: '/library/history' },
              ],
            },
          },
        ],
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 5: STUDENTS (Schueler)
      // ═══════════════════════════════════════════════════════
      {
        path: 'students',
        component: () => import('@/views/StudentsHubView.vue'),
        meta: {
          requiresAuth: true,
        },
        children: [
          {
            path: '',
            name: 'Students',
            component: () => import('@/views/StudentsView.vue'),
            meta: {
              requiresAuth: true,
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Schueler', path: '/students' },
              ],
            },
          },
          {
            path: ':id',
            name: 'StudentDetail',
            component: () => import('@/views/StudentDetailView.vue'),
            meta: {
              requiresAuth: true,
              breadcrumb: [
                { label: 'Home', path: '/home' },
                { label: 'Schueler', path: '/students' },
                { label: 'Detail', path: '' },
              ],
            },
          },
        ],
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 6: ANALYTICS
      // ═══════════════════════════════════════════════════════
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/AnalyticsView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }, { label: 'Analytics', path: '/analytics' }],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 6b: KI-TOOLS
      // ═══════════════════════════════════════════════════════
      {
        path: 'ai/prompt-history',
        name: 'PromptHistory',
        component: () => import('@/views/PromptHistoryView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'KI-History', path: '/ai/prompt-history' },
          ],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 7: SETTINGS
      // ═══════════════════════════════════════════════════════
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }, { label: 'Einstellungen', path: '/settings' }],
        },
      },

      // ═══════════════════════════════════════════════════════
      // SECTION 8: DESIGN SYSTEM (Design-Token Referenz)
      // ═══════════════════════════════════════════════════════
      {
        path: 'design-system',
        name: 'DesignSystem',
        component: () => import('@/views/DesignSystemView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [{ label: 'Home', path: '/home' }, { label: 'Design-System', path: '/design-system' }],
        },
      },

      // ═══════════════════════════════════════════════════════
      // VIDEO TOOLS (sub-section of create, but top-level for direct access)
      // ═══════════════════════════════════════════════════════
      {
        path: 'video/thumbnails',
        name: 'ThumbnailGenerator',
        component: () => import('@/views/ThumbnailGeneratorView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Thumbnails', path: '/video/thumbnails' },
          ],
        },
      },
      {
        path: 'video/overlays',
        name: 'VideoOverlays',
        component: () => import('@/views/VideoOverlayEditorView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Overlays', path: '/video/overlays' },
          ],
        },
      },
      {
        path: 'video/composer',
        name: 'VideoComposer',
        component: () => import('@/views/VideoComposerView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Schnitt', path: '/video/composer' },
          ],
        },
      },
      {
        path: 'video/templates',
        name: 'VideoTemplates',
        component: () => import('@/views/VideoTemplatesView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Branding', path: '/video/templates' },
          ],
        },
      },
      {
        path: 'video/export',
        name: 'VideoExport',
        component: () => import('@/views/VideoExportView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Export', path: '/video/export' },
          ],
        },
      },
      {
        path: 'video/audio-mixer',
        name: 'AudioMixer',
        component: () => import('@/views/AudioMixerView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Audio-Mixer', path: '/video/audio-mixer' },
          ],
        },
      },
      {
        path: 'video/script-generator',
        name: 'VideoScriptGenerator',
        component: () => import('@/views/VideoScriptView.vue'),
        meta: {
          requiresAuth: true,
          breadcrumb: [
            { label: 'Home', path: '/home' },
            { label: 'Video-Tools', path: '/create/video' },
            { label: 'Script-Generator', path: '/video/script-generator' },
          ],
        },
      },

      // ═══════════════════════════════════════════════════════
      // REDIRECTS: Old routes → new equivalents (no 404s)
      // ═══════════════════════════════════════════════════════
      { path: 'dashboard', redirect: '/home' },
      { path: 'create-post', redirect: '/create/quick' },
      { path: 'posts/:id/edit', redirect: to => `/create/post/${to.params.id}/edit` },
      { path: 'templates', redirect: '/library/templates' },
      { path: 'assets', redirect: '/library/assets' },
      { path: 'history', redirect: '/library/history' },
      { path: 'week-planner', redirect: '/calendar/week-planner' },
      { path: 'story-arcs', redirect: '/calendar/story-arcs' },
      { path: 'story-arcs/:id', redirect: to => `/calendar/story-arcs/${to.params.id}` },
      { path: 'story-arc-wizard', redirect: '/calendar/story-arc-wizard' },
      { path: 'recurring-formats', redirect: '/calendar/recurring-formats' },
      { path: 'thumbnail-generator', redirect: '/video/thumbnails' },
      { path: 'video-overlays', redirect: '/video/overlays' },
      { path: 'video-composer', redirect: '/video/composer' },
      { path: 'video-templates', redirect: '/video/templates' },
      { path: 'video-export', redirect: '/video/export' },
      { path: 'audio-mixer', redirect: '/video/audio-mixer' },
    ],
  },

  // ─── 404 catch-all ────────────────────────────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

// ─── Navigation direction tracking ──────────────────────────
// Tracks whether the user navigated forward (deeper) or backward (up)
// so that page transitions can slide in the appropriate direction.
router.transitionDirection = 'forward'

router.beforeResolve((to, from) => {
  const toDepth = to.path.split('/').filter(Boolean).length
  const fromDepth = from.path.split('/').filter(Boolean).length
  router.transitionDirection = toDepth >= fromDepth ? 'forward' : 'backward'
})

// ─── Navigation guard ───────────────────────────────────────
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Initialize auth state on first navigation (fetches user data if tokens exist)
  await auth.initializeAuth()

  // Check requiresAuth: walk up the matched route hierarchy
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth !== false)
  const isPublic = to.matched.some((record) => record.meta.requiresAuth === false)

  if (requiresAuth && !auth.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (isPublic && auth.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
