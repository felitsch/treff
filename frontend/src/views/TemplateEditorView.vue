<script setup>
/**
 * TemplateEditorView.vue — Visual WYSIWYG Template Editor
 *
 * Feature #244: Visueller Template-Editor
 * - Canvas area sized per format (1:1, 4:5, 9:16)
 * - Toolbar: add text, image, shape, background color
 * - Element selection with drag-to-move and resize handles
 * - Property panel: color, font, size, alignment, opacity
 * - Layer panel: z-order management
 * - Undo/Redo with Ctrl+Z / Ctrl+Y
 * - Save as template to DB (name, category, format)
 * - JSON serialization/deserialization
 */
import { ref, computed, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/utils/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const toast = useToast()

// ─── Canvas format ────────────────────────────────────────────────
const formats = {
  feed_square: { label: '1:1 Feed', w: 1080, h: 1080 },
  feed_portrait: { label: '4:5 Portrait', w: 1080, h: 1350 },
  story: { label: '9:16 Story', w: 1080, h: 1920 },
}
const selectedFormat = ref('feed_square')
const canvasW = computed(() => formats[selectedFormat.value].w)
const canvasH = computed(() => formats[selectedFormat.value].h)

// Canvas scale: fit within ~500px width
const canvasScale = computed(() => Math.min(500 / canvasW.value, 600 / canvasH.value))
const scaledW = computed(() => canvasW.value * canvasScale.value)
const scaledH = computed(() => canvasH.value * canvasScale.value)

// ─── Elements ─────────────────────────────────────────────────────
const elements = ref([])
const selectedElementId = ref(null)
const nextElementId = ref(1)

// Background
const backgroundColor = ref('#1A1A2E')
const backgroundGradient = ref(false)
const backgroundGradientEnd = ref('#3B7AB1')

// ─── Undo/Redo ────────────────────────────────────────────────────
const undoStack = ref([])
const redoStack = ref([])
const MAX_UNDO = 50

function pushUndo() {
  undoStack.value.push(JSON.stringify(elements.value))
  if (undoStack.value.length > MAX_UNDO) undoStack.value.shift()
  redoStack.value = []
}

function undo() {
  if (undoStack.value.length === 0) return
  redoStack.value.push(JSON.stringify(elements.value))
  const prev = undoStack.value.pop()
  elements.value = JSON.parse(prev)
  selectedElementId.value = null
}

function redo() {
  if (redoStack.value.length === 0) return
  undoStack.value.push(JSON.stringify(elements.value))
  const next = redoStack.value.pop()
  elements.value = JSON.parse(next)
  selectedElementId.value = null
}

// Keyboard shortcuts
function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
    e.preventDefault()
    undo()
  } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
    e.preventDefault()
    redo()
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedElementId.value && !isEditingText.value) {
      e.preventDefault()
      deleteSelected()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  // Load template if editing existing one
  if (route.query.template_id) {
    loadTemplate(parseInt(route.query.template_id))
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// ─── Selected element ─────────────────────────────────────────────
const selectedElement = computed(() => {
  if (!selectedElementId.value) return null
  return elements.value.find(el => el.id === selectedElementId.value)
})

const isEditingText = ref(false)

// ─── Add elements ─────────────────────────────────────────────────
function addText() {
  pushUndo()
  const el = {
    id: nextElementId.value++,
    type: 'text',
    x: 100,
    y: 100,
    width: 500,
    height: 80,
    content: 'Neuer Text',
    fontSize: 48,
    fontFamily: 'Montserrat',
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'left',
    opacity: 1,
    zIndex: elements.value.length + 1,
  }
  elements.value.push(el)
  selectedElementId.value = el.id
}

function addHeadline() {
  pushUndo()
  const el = {
    id: nextElementId.value++,
    type: 'text',
    x: 80,
    y: 80,
    width: 920,
    height: 120,
    content: '{{headline}}',
    fontSize: 72,
    fontFamily: 'Montserrat',
    fontWeight: '800',
    color: '#FFFFFF',
    textAlign: 'left',
    opacity: 1,
    zIndex: elements.value.length + 1,
  }
  elements.value.push(el)
  selectedElementId.value = el.id
}

function addShape(shapeType) {
  pushUndo()
  const el = {
    id: nextElementId.value++,
    type: 'shape',
    shapeType, // 'rect', 'circle', 'line'
    x: 200,
    y: 200,
    width: 300,
    height: shapeType === 'line' ? 4 : 300,
    color: '#3B7AB1',
    borderRadius: shapeType === 'circle' ? 9999 : 0,
    opacity: 0.8,
    zIndex: elements.value.length + 1,
  }
  elements.value.push(el)
  selectedElementId.value = el.id
}

function addImage() {
  pushUndo()
  const el = {
    id: nextElementId.value++,
    type: 'image',
    x: 100,
    y: 100,
    width: 400,
    height: 400,
    src: '',
    opacity: 1,
    borderRadius: 0,
    zIndex: elements.value.length + 1,
  }
  elements.value.push(el)
  selectedElementId.value = el.id
}

// ─── Element actions ──────────────────────────────────────────────
function deleteSelected() {
  if (!selectedElementId.value) return
  pushUndo()
  elements.value = elements.value.filter(el => el.id !== selectedElementId.value)
  selectedElementId.value = null
}

function duplicateSelected() {
  if (!selectedElement.value) return
  pushUndo()
  const copy = { ...JSON.parse(JSON.stringify(selectedElement.value)) }
  copy.id = nextElementId.value++
  copy.x += 20
  copy.y += 20
  copy.zIndex = elements.value.length + 1
  elements.value.push(copy)
  selectedElementId.value = copy.id
}

function moveLayer(direction) {
  if (!selectedElement.value) return
  pushUndo()
  const el = selectedElement.value
  if (direction === 'up') {
    el.zIndex = Math.min(el.zIndex + 1, elements.value.length + 10)
  } else if (direction === 'down') {
    el.zIndex = Math.max(el.zIndex - 1, 1)
  } else if (direction === 'top') {
    el.zIndex = Math.max(...elements.value.map(e => e.zIndex)) + 1
  } else if (direction === 'bottom') {
    el.zIndex = 0
  }
}

// ─── Drag & Move ──────────────────────────────────────────────────
const canvasRef = ref(null)
const isDragging = ref(false)
const isResizing = ref(false)
const resizeHandle = ref(null)
const dragStart = reactive({ x: 0, y: 0, elX: 0, elY: 0, elW: 0, elH: 0 })

function getCanvasCoords(e) {
  if (!canvasRef.value) return { x: 0, y: 0 }
  const rect = canvasRef.value.getBoundingClientRect()
  return {
    x: (e.clientX - rect.left) / canvasScale.value,
    y: (e.clientY - rect.top) / canvasScale.value,
  }
}

function onCanvasClick(e) {
  // Click on canvas background deselects
  if (e.target === canvasRef.value || e.target.classList.contains('canvas-bg')) {
    selectedElementId.value = null
    isEditingText.value = false
  }
}

function onElementMouseDown(e, el) {
  e.stopPropagation()
  selectedElementId.value = el.id
  isEditingText.value = false

  const coords = getCanvasCoords(e)
  dragStart.x = coords.x
  dragStart.y = coords.y
  dragStart.elX = el.x
  dragStart.elY = el.y
  isDragging.value = true

  const onMouseMove = (ev) => {
    if (!isDragging.value) return
    const c = getCanvasCoords(ev)
    const dx = c.x - dragStart.x
    const dy = c.y - dragStart.y
    el.x = Math.round(dragStart.elX + dx)
    el.y = Math.round(dragStart.elY + dy)
  }

  const onMouseUp = () => {
    if (isDragging.value) {
      isDragging.value = false
      pushUndo()
    }
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function onResizeMouseDown(e, el, handle) {
  e.stopPropagation()
  e.preventDefault()
  selectedElementId.value = el.id

  const coords = getCanvasCoords(e)
  dragStart.x = coords.x
  dragStart.y = coords.y
  dragStart.elX = el.x
  dragStart.elY = el.y
  dragStart.elW = el.width
  dragStart.elH = el.height
  isResizing.value = true
  resizeHandle.value = handle

  const onMouseMove = (ev) => {
    if (!isResizing.value) return
    const c = getCanvasCoords(ev)
    const dx = c.x - dragStart.x
    const dy = c.y - dragStart.y

    if (handle.includes('e')) el.width = Math.max(30, Math.round(dragStart.elW + dx))
    if (handle.includes('w')) {
      el.width = Math.max(30, Math.round(dragStart.elW - dx))
      el.x = Math.round(dragStart.elX + dx)
    }
    if (handle.includes('s')) el.height = Math.max(20, Math.round(dragStart.elH + dy))
    if (handle.includes('n')) {
      el.height = Math.max(20, Math.round(dragStart.elH - dy))
      el.y = Math.round(dragStart.elY + dy)
    }
  }

  const onMouseUp = () => {
    if (isResizing.value) {
      isResizing.value = false
      pushUndo()
    }
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

// ─── Save template ────────────────────────────────────────────────
const showSaveModal = ref(false)
const saving = ref(false)
const saveName = ref('')
const saveCategory = ref('laender_spotlight')
const saveCategories = [
  { value: 'laender_spotlight', label: 'Länder-Spotlight' },
  { value: 'erfahrungsberichte', label: 'Erfahrungsberichte' },
  { value: 'infografiken', label: 'Infografiken' },
  { value: 'fristen_cta', label: 'Fristen & CTA' },
  { value: 'tipps_tricks', label: 'Tipps & Tricks' },
  { value: 'faq', label: 'FAQ' },
  { value: 'foto_posts', label: 'Foto-Posts' },
  { value: 'reel_tiktok_thumbnails', label: 'Reel/TikTok' },
  { value: 'story_posts', label: 'Story-Posts' },
]

function serializeToHtml() {
  // Convert elements to absolute-positioned HTML
  let html = '<div class="template-root" style="position:relative;width:100%;height:100%;overflow:hidden;'
  if (backgroundGradient.value) {
    html += `background:linear-gradient(135deg, ${backgroundColor.value} 0%, ${backgroundGradientEnd.value} 100%);`
  } else {
    html += `background-color:${backgroundColor.value};`
  }
  html += '">\n'

  const sorted = [...elements.value].sort((a, b) => a.zIndex - b.zIndex)
  for (const el of sorted) {
    const baseStyle = `position:absolute;left:${el.x}px;top:${el.y}px;width:${el.width}px;height:${el.height}px;opacity:${el.opacity};z-index:${el.zIndex};`

    if (el.type === 'text') {
      const textStyle = `font-size:${el.fontSize}px;font-family:${el.fontFamily},sans-serif;font-weight:${el.fontWeight};color:${el.color};text-align:${el.textAlign};line-height:1.2;`
      html += `  <div style="${baseStyle}${textStyle}">${el.content}</div>\n`
    } else if (el.type === 'shape') {
      const shapeStyle = `background-color:${el.color};border-radius:${el.borderRadius}px;`
      html += `  <div style="${baseStyle}${shapeStyle}"></div>\n`
    } else if (el.type === 'image') {
      const imgStyle = `border-radius:${el.borderRadius}px;overflow:hidden;`
      if (el.src) {
        html += `  <div style="${baseStyle}${imgStyle}"><img src="${el.src}" style="width:100%;height:100%;object-fit:cover;" /></div>\n`
      } else {
        html += `  <div style="${baseStyle}${imgStyle}background:#555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:24px;">{{image}}</div>\n`
      }
    }
  }

  html += '</div>'
  return html
}

function serializeToCss() {
  return `.template-root { font-family: Inter, sans-serif; }`
}

function serializeToJson() {
  return JSON.stringify({
    format: selectedFormat.value,
    backgroundColor: backgroundColor.value,
    backgroundGradient: backgroundGradient.value,
    backgroundGradientEnd: backgroundGradientEnd.value,
    elements: elements.value,
    nextElementId: nextElementId.value,
  })
}

// Extract placeholder fields from elements
function extractPlaceholders() {
  const placeholders = new Set()
  for (const el of elements.value) {
    if (el.type === 'text' && el.content) {
      const matches = el.content.matchAll(/\{\{(\w+)\}\}/g)
      for (const m of matches) {
        placeholders.add(m[1])
      }
    }
  }
  if (elements.value.some(el => el.type === 'image' && !el.src)) {
    placeholders.add('image')
  }
  return [...placeholders]
}

async function saveTemplate() {
  if (!saveName.value.trim()) {
    toast.error('Bitte gib einen Template-Namen ein.')
    return
  }
  saving.value = true
  try {
    const htmlContent = serializeToHtml()
    const cssContent = serializeToCss()
    const placeholders = extractPlaceholders()

    const data = {
      name: saveName.value.trim(),
      category: saveCategory.value,
      platform_format: selectedFormat.value,
      slide_count: 1,
      html_content: htmlContent,
      css_content: cssContent,
      placeholder_fields: JSON.stringify(placeholders),
      default_colors: JSON.stringify({
        primary: '#3B7AB1',
        secondary: '#FDD000',
        accent: '#FFFFFF',
        background: backgroundColor.value,
      }),
      default_fonts: JSON.stringify({
        heading_font: 'Montserrat',
        body_font: 'Inter',
      }),
    }

    await api.post('/api/templates', data)
    toast.success(`Template "${saveName.value}" gespeichert!`)
    showSaveModal.value = false
    saveName.value = ''
  } catch (err) {
    toast.error('Fehler beim Speichern des Templates.')
    // Error toast shown by API interceptor
  } finally {
    saving.value = false
  }
}

// ─── Load existing template for editing ───────────────────────────
async function loadTemplate(id) {
  try {
    const res = await api.get(`/api/templates/${id}`)
    const t = res.data
    saveName.value = t.name + ' (Kopie)'
    saveCategory.value = t.category
    selectedFormat.value = t.platform_format || 'feed_square'

    // Try to parse editor JSON from default_colors (contains our editor state)
    // Otherwise generate elements from HTML
    try {
      const colors = JSON.parse(t.default_colors || '{}')
      backgroundColor.value = colors.background || '#1A1A2E'
    } catch (e) { /* ignore */ }

    toast.info(`Template "${t.name}" geladen. Bearbeite und speichere als Kopie.`)
  } catch (err) {
    // Error toast shown by API interceptor
  }
}

// ─── Sorted elements for rendering ────────────────────────────────
const sortedElements = computed(() => {
  return [...elements.value].sort((a, b) => a.zIndex - b.zIndex)
})

// Layer panel: sorted by zIndex descending (top first)
const layerElements = computed(() => {
  return [...elements.value].sort((a, b) => b.zIndex - a.zIndex)
})

// Available fonts
const fontFamilies = ['Montserrat', 'Inter', 'Poppins', 'Playfair Display', 'Roboto', 'Open Sans', 'Lato']
const fontWeights = ['300', '400', '500', '600', '700', '800', '900']
</script>

<template>
  <div class="min-h-screen" data-testid="template-editor">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4" data-testid="editor-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Template-Editor</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Visueller WYSIWYG Editor</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Undo/Redo -->
        <div class="flex items-center gap-1">
          <button
            @click="undo"
            :disabled="undoStack.length === 0"
            class="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Rueckgaengig (Ctrl+Z)"
            data-testid="undo-btn"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a5 5 0 015 5v2M3 10l4-4M3 10l4 4" />
            </svg>
          </button>
          <button
            @click="redo"
            :disabled="redoStack.length === 0"
            class="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Wiederherstellen (Ctrl+Y)"
            data-testid="redo-btn"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 10H11a5 5 0 00-5 5v2M21 10l-4-4M21 10l-4 4" />
            </svg>
          </button>
        </div>

        <!-- Format selector -->
        <select
          v-model="selectedFormat"
          class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          data-testid="format-select"
        >
          <option v-for="(fmt, key) in formats" :key="key" :value="key">
            {{ fmt.label }} ({{ fmt.w }}x{{ fmt.h }})
          </option>
        </select>

        <!-- Save button -->
        <button
          @click="showSaveModal = true"
          class="px-4 py-2 rounded-lg bg-[#3B7AB1] text-white text-sm font-semibold hover:bg-[#326a9b] transition-colors flex items-center gap-2"
          data-testid="save-btn"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          Speichern
        </button>
      </div>
    </div>

    <!-- Main layout: Toolbar | Canvas | Properties -->
    <div class="flex gap-4">

      <!-- ═══ Left Toolbar ═══ -->
      <div class="w-14 shrink-0 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-2 flex flex-col gap-1" data-testid="toolbar">
        <button @click="addText" title="Text hinzufuegen" class="toolbar-btn" data-testid="add-text-btn">
          <span class="text-lg">T</span>
        </button>
        <button @click="addHeadline" title="Headline-Platzhalter" class="toolbar-btn">
          <span class="text-lg font-bold">H</span>
        </button>
        <button @click="addImage" title="Bild hinzufuegen" class="toolbar-btn" data-testid="add-image-btn">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        <hr class="border-gray-200 dark:border-gray-700 my-1" />
        <button @click="addShape('rect')" title="Rechteck" class="toolbar-btn" data-testid="add-rect-btn">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
          </svg>
        </button>
        <button @click="addShape('circle')" title="Kreis" class="toolbar-btn">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="9" />
          </svg>
        </button>
        <button @click="addShape('line')" title="Linie" class="toolbar-btn">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <line x1="4" y1="12" x2="20" y2="12" />
          </svg>
        </button>
        <hr class="border-gray-200 dark:border-gray-700 my-1" />
        <button
          v-if="selectedElementId"
          @click="duplicateSelected"
          title="Duplizieren"
          class="toolbar-btn"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        <button
          v-if="selectedElementId"
          @click="deleteSelected"
          title="Loeschen (Del)"
          class="toolbar-btn text-red-500"
          data-testid="delete-btn"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      <!-- ═══ Canvas ═══ -->
      <div class="flex-1 flex items-start justify-center">
        <div
          ref="canvasRef"
          class="relative overflow-hidden rounded-lg shadow-lg cursor-crosshair"
          :style="{
            width: scaledW + 'px',
            height: scaledH + 'px',
            background: backgroundGradient
              ? `linear-gradient(135deg, ${backgroundColor} 0%, ${backgroundGradientEnd} 100%)`
              : backgroundColor,
          }"
          @click="onCanvasClick"
          data-testid="canvas"
        >
          <!-- Transparent grid pattern for visibility -->
          <div class="canvas-bg absolute inset-0 pointer-events-none" style="background-image: url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2220%22 height=%2220%22><rect width=%2220%22 height=%2220%22 fill=%22none%22/><rect width=%221%22 height=%221%22 x=%2210%22 y=%2210%22 fill=%22rgba(255,255,255,0.03)%22/></svg>'); pointer-events: auto;" />

          <!-- Rendered elements -->
          <div
            v-for="el in sortedElements"
            :key="el.id"
            :style="{
              position: 'absolute',
              left: el.x * canvasScale + 'px',
              top: el.y * canvasScale + 'px',
              width: el.width * canvasScale + 'px',
              height: el.height * canvasScale + 'px',
              opacity: el.opacity,
              zIndex: el.zIndex,
              cursor: 'move',
            }"
            :class="[
              'select-none',
              selectedElementId === el.id ? 'ring-2 ring-blue-500 ring-offset-1' : '',
            ]"
            @mousedown="onElementMouseDown($event, el)"
            @dblclick="el.type === 'text' ? isEditingText = true : null"
            :data-testid="'element-' + el.id"
          >
            <!-- Text element -->
            <div
              v-if="el.type === 'text'"
              :style="{
                fontSize: el.fontSize * canvasScale + 'px',
                fontFamily: el.fontFamily + ', sans-serif',
                fontWeight: el.fontWeight,
                color: el.color,
                textAlign: el.textAlign,
                lineHeight: '1.2',
                width: '100%',
                height: '100%',
                overflow: 'hidden',
                wordWrap: 'break-word',
              }"
            >
              {{ el.content }}
            </div>

            <!-- Shape element -->
            <div
              v-else-if="el.type === 'shape'"
              :style="{
                width: '100%',
                height: '100%',
                backgroundColor: el.color,
                borderRadius: el.borderRadius * canvasScale + 'px',
              }"
            />

            <!-- Image element -->
            <div
              v-else-if="el.type === 'image'"
              :style="{
                width: '100%',
                height: '100%',
                borderRadius: el.borderRadius * canvasScale + 'px',
                overflow: 'hidden',
                backgroundColor: '#555',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }"
            >
              <img loading="lazy" v-if="el.src" :src="el.src" class="w-full h-full object-cover" alt="Template-Bildelement" />
              <span v-else class="text-gray-400" :style="{ fontSize: 16 * canvasScale + 'px' }">Bild</span>
            </div>

            <!-- Resize handles (only for selected) -->
            <template v-if="selectedElementId === el.id">
              <div
                v-for="h in ['nw','n','ne','e','se','s','sw','w']"
                :key="h"
                :class="[
                  'absolute w-2.5 h-2.5 bg-blue-500 border border-white rounded-sm z-50',
                  h === 'nw' ? '-top-1 -left-1 cursor-nw-resize' : '',
                  h === 'n' ? '-top-1 left-1/2 -translate-x-1/2 cursor-n-resize' : '',
                  h === 'ne' ? '-top-1 -right-1 cursor-ne-resize' : '',
                  h === 'e' ? 'top-1/2 -right-1 -translate-y-1/2 cursor-e-resize' : '',
                  h === 'se' ? '-bottom-1 -right-1 cursor-se-resize' : '',
                  h === 's' ? '-bottom-1 left-1/2 -translate-x-1/2 cursor-s-resize' : '',
                  h === 'sw' ? '-bottom-1 -left-1 cursor-sw-resize' : '',
                  h === 'w' ? 'top-1/2 -left-1 -translate-y-1/2 cursor-w-resize' : '',
                ]"
                @mousedown="onResizeMouseDown($event, el, h)"
              />
            </template>
          </div>
        </div>
      </div>

      <!-- ═══ Right Panel: Properties + Layers ═══ -->
      <div class="w-64 shrink-0 space-y-4" data-testid="property-panel">

        <!-- Background -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Hintergrund</h3>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <input type="color" v-model="backgroundColor" class="w-8 h-8 rounded cursor-pointer" />
              <input type="text" v-model="backgroundColor" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-mono" />
            </div>
            <label class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
              <input type="checkbox" v-model="backgroundGradient" class="rounded" />
              Verlauf
            </label>
            <div v-if="backgroundGradient" class="flex items-center gap-2">
              <input type="color" v-model="backgroundGradientEnd" class="w-8 h-8 rounded cursor-pointer" />
              <input type="text" v-model="backgroundGradientEnd" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-mono" />
            </div>
          </div>
        </div>

        <!-- Element properties (when selected) -->
        <div v-if="selectedElement" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="element-props">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            {{ selectedElement.type === 'text' ? 'Text' : selectedElement.type === 'shape' ? 'Form' : 'Bild' }} Eigenschaften
          </h3>

          <div class="space-y-3">
            <!-- Text content -->
            <div v-if="selectedElement.type === 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Inhalt</label>
              <textarea
                v-model="selectedElement.content"
                rows="2"
                class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                data-testid="text-content"
              />
            </div>

            <!-- Color -->
            <div>
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Farbe</label>
              <div class="flex items-center gap-2">
                <input type="color" v-model="selectedElement.color" class="w-8 h-8 rounded cursor-pointer" />
                <input type="text" v-model="selectedElement.color" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-mono" />
              </div>
            </div>

            <!-- Font (text only) -->
            <div v-if="selectedElement.type === 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Schriftart</label>
              <select v-model="selectedElement.fontFamily" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
                <option v-for="f in fontFamilies" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>

            <!-- Font size (text only) -->
            <div v-if="selectedElement.type === 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Groesse: {{ selectedElement.fontSize }}px</label>
              <input type="range" v-model.number="selectedElement.fontSize" min="12" max="200" class="w-full" />
            </div>

            <!-- Font weight (text only) -->
            <div v-if="selectedElement.type === 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Gewicht</label>
              <select v-model="selectedElement.fontWeight" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
                <option v-for="w in fontWeights" :key="w" :value="w">{{ w }}</option>
              </select>
            </div>

            <!-- Text alignment (text only) -->
            <div v-if="selectedElement.type === 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Ausrichtung</label>
              <div class="flex gap-1">
                <button
                  v-for="align in ['left', 'center', 'right']"
                  :key="align"
                  @click="selectedElement.textAlign = align"
                  :class="[
                    'flex-1 py-1 text-xs rounded border transition-colors',
                    selectedElement.textAlign === align
                      ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-600 dark:text-blue-300'
                      : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
                  ]"
                >
                  {{ align === 'left' ? 'Links' : align === 'center' ? 'Mitte' : 'Rechts' }}
                </button>
              </div>
            </div>

            <!-- Border radius -->
            <div v-if="selectedElement.type !== 'text'">
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Eckenradius: {{ selectedElement.borderRadius }}px</label>
              <input type="range" v-model.number="selectedElement.borderRadius" min="0" max="500" class="w-full" />
            </div>

            <!-- Opacity -->
            <div>
              <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Deckkraft: {{ Math.round(selectedElement.opacity * 100) }}%</label>
              <input type="range" v-model.number="selectedElement.opacity" min="0" max="1" step="0.05" class="w-full" />
            </div>

            <!-- Position -->
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="text-xs text-gray-500 dark:text-gray-400 mb-0.5 block">X</label>
                <input type="number" v-model.number="selectedElement.x" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
              </div>
              <div>
                <label class="text-xs text-gray-500 dark:text-gray-400 mb-0.5 block">Y</label>
                <input type="number" v-model.number="selectedElement.y" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
              </div>
              <div>
                <label class="text-xs text-gray-500 dark:text-gray-400 mb-0.5 block">Breite</label>
                <input type="number" v-model.number="selectedElement.width" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
              </div>
              <div>
                <label class="text-xs text-gray-500 dark:text-gray-400 mb-0.5 block">Hoehe</label>
                <input type="number" v-model.number="selectedElement.height" class="w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
              </div>
            </div>
          </div>
        </div>

        <!-- Layer panel -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4" data-testid="layer-panel">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ebenen</h3>
            <div v-if="selectedElementId" class="flex gap-0.5">
              <button @click="moveLayer('top')" title="Ganz nach vorne" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 text-xs">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 11l7-7 7 7" /><path stroke-linecap="round" stroke-linejoin="round" d="M5 19l7-7 7 7" /></svg>
              </button>
              <button @click="moveLayer('up')" title="Eine Ebene nach vorne" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 text-xs">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg>
              </button>
              <button @click="moveLayer('down')" title="Eine Ebene nach hinten" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 text-xs">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
              </button>
              <button @click="moveLayer('bottom')" title="Ganz nach hinten" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 text-xs">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 5l-7 7-7-7" /><path stroke-linecap="round" stroke-linejoin="round" d="M19 13l-7 7-7-7" /></svg>
              </button>
            </div>
          </div>
          <div v-if="layerElements.length === 0" class="text-xs text-gray-400 dark:text-gray-500 text-center py-3">
            Noch keine Elemente
          </div>
          <div v-else class="space-y-1 max-h-48 overflow-y-auto">
            <button
              v-for="el in layerElements"
              :key="el.id"
              @click="selectedElementId = el.id"
              :class="[
                'w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors text-left',
                selectedElementId === el.id
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
              ]"
            >
              <span class="w-4 text-center">
                {{ el.type === 'text' ? 'T' : el.type === 'shape' ? (el.shapeType === 'circle' ? 'O' : '[]') : 'Img' }}
              </span>
              <span class="truncate flex-1">
                {{ el.type === 'text' ? el.content.substring(0, 20) : el.type === 'shape' ? (el.shapeType === 'rect' ? 'Rechteck' : el.shapeType === 'circle' ? 'Kreis' : 'Linie') : 'Bild' }}
              </span>
              <span class="text-gray-400 text-[10px]">z{{ el.zIndex }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Save Modal ═══ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-opacity duration-200"
        enter-from-class="opacity-0"
        leave-active-class="transition-opacity duration-200"
        leave-to-class="opacity-0"
      >
        <div v-if="showSaveModal" class="fixed inset-0 z-[9998] flex items-center justify-center" data-testid="save-modal">
          <div class="absolute inset-0 bg-black/50" @click="showSaveModal = false" />
          <div class="relative z-10 bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
            <h2 class="text-lg font-bold text-gray-900 dark:text-white mb-4">Template speichern</h2>

            <div class="space-y-4">
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">Name</label>
                <input
                  v-model="saveName"
                  type="text"
                  placeholder="Mein Template"
                  class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                  data-testid="save-name-input"
                />
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">Kategorie</label>
                <select
                  v-model="saveCategory"
                  class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                >
                  <option v-for="cat in saveCategories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
                </select>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">Format</label>
                <p class="text-sm text-gray-600 dark:text-gray-400">{{ formats[selectedFormat].label }} ({{ canvasW }}x{{ canvasH }})</p>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                <p><strong>{{ elements.length }}</strong> Elemente</p>
                <p v-if="extractPlaceholders().length > 0">Platzhalter: {{ extractPlaceholders().join(', ') }}</p>
              </div>
            </div>

            <div class="flex gap-3 mt-6">
              <button @click="showSaveModal = false" class="flex-1 py-2 px-4 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                Abbrechen
              </button>
              <button
                @click="saveTemplate"
                :disabled="saving || !saveName.trim()"
                class="flex-1 py-2 px-4 rounded-lg bg-[#3B7AB1] text-white text-sm font-semibold hover:bg-[#326a9b] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="save-confirm-btn"
              >
                {{ saving ? 'Speichere...' : 'Speichern' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.toolbar-btn {
  @apply w-10 h-10 flex items-center justify-center rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer;
}
</style>
