import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
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
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
      },
      {
        path: 'create-post',
        name: 'CreatePost',
        component: () => import('@/views/CreatePostView.vue'),
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('@/views/TemplatesView.vue'),
      },
      {
        path: 'assets',
        name: 'Assets',
        component: () => import('@/views/AssetsView.vue'),
      },
      {
        path: 'calendar',
        name: 'Calendar',
        component: () => import('@/views/CalendarView.vue'),
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/HistoryView.vue'),
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/AnalyticsView.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
      },
      {
        path: 'posts/:id/edit',
        name: 'EditPost',
        component: () => import('@/views/EditPostView.vue'),
      },
      {
        path: 'students',
        name: 'Students',
        component: () => import('@/views/StudentsView.vue'),
      },
      {
        path: 'students/:id',
        name: 'StudentDetail',
        component: () => import('@/views/StudentDetailView.vue'),
      },
      {
        path: 'thumbnail-generator',
        name: 'ThumbnailGenerator',
        component: () => import('@/views/ThumbnailGeneratorView.vue'),
      },
      {
        path: 'week-planner',
        name: 'WeekPlanner',
        component: () => import('@/views/WeekPlannerView.vue'),
      },
      {
        path: 'video-overlays',
        name: 'VideoOverlays',
        component: () => import('@/views/VideoOverlayEditorView.vue'),
      },
      {
        path: 'video-composer',
        name: 'VideoComposer',
        component: () => import('@/views/VideoComposerView.vue'),
      },
      {
        path: 'video-templates',
        name: 'VideoTemplates',
        component: () => import('@/views/VideoTemplatesView.vue'),
      },
      {
        path: 'video-export',
        name: 'VideoExport',
        component: () => import('@/views/VideoExportView.vue'),
      },
      {
        path: 'audio-mixer',
        name: 'AudioMixer',
        component: () => import('@/views/AudioMixerView.vue'),
      },
      {
        path: 'story-arcs',
        name: 'StoryArcs',
        component: () => import('@/views/StoryArcsView.vue'),
      },
      {
        path: 'story-arcs/:id',
        name: 'StoryArcDetail',
        component: () => import('@/views/StoryArcDetailView.vue'),
      },
      {
        path: 'story-arc-wizard',
        name: 'StoryArcWizard',
        component: () => import('@/views/StoryArcWizardView.vue'),
      },
      {
        path: 'recurring-formats',
        name: 'RecurringFormats',
        component: () => import('@/views/RecurringFormatsView.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Initialize auth state on first navigation (fetches user data if tokens exist)
  await auth.initializeAuth()

  if (to.meta.requiresAuth !== false && !auth.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAuth === false && auth.isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
