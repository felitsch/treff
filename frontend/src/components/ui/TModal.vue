<script setup>
/**
 * TModal.vue — TREFF Design System Modal/Dialog Component.
 *
 * A modal dialog with backdrop overlay, multiple size presets, focus trapping,
 * and accessible keyboard navigation. Uses Teleport to render at body level.
 *
 * Props:
 *   modelValue (Boolean) — v-model for open/close state
 *   size       (String)  — 'sm' | 'md' | 'lg' | 'full' (default: 'md')
 *   title      (String)  — Modal title text
 *   closable   (Boolean) — Show close button and allow backdrop/Escape close (default: true)
 *   persistent (Boolean) — Prevent closing by backdrop click (only close button/Escape)
 *
 * Slots:
 *   header   — Custom header content (replaces title)
 *   default  — Modal body content
 *   footer   — Modal footer (action buttons area)
 *
 * Events:
 *   update:modelValue — v-model emission
 *   close — Emitted when modal closes
 *
 * @see useFocusTrap.js
 */
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useFocusTrap } from '@/composables/useFocusTrap'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'full'].includes(v),
  },
  title: {
    type: String,
    default: '',
  },
  closable: {
    type: Boolean,
    default: true,
  },
  persistent: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'close'])

const modalRef = ref(null)
const { activate: activateTrap, deactivate: deactivateTrap } = useFocusTrap(modalRef)

// Size classes for the dialog panel
const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-3xl',
  full: 'max-w-[calc(100vw-2rem)] max-h-[calc(100vh-2rem)]',
}

function close() {
  if (!props.closable) return
  emit('update:modelValue', false)
  emit('close')
}

function onBackdropClick() {
  if (props.persistent) return
  close()
}

function onKeydown(e) {
  if (e.key === 'Escape' && props.closable) {
    e.stopPropagation()
    close()
  }
}

// Watch for open/close to manage focus trap and body scroll
watch(
  () => props.modelValue,
  async (isOpen) => {
    if (isOpen) {
      // Prevent body scroll
      document.body.style.overflow = 'hidden'
      await nextTick()
      activateTrap()
    } else {
      document.body.style.overflow = ''
      deactivateTrap()
    }
  },
)

// Clean up on unmount
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  deactivateTrap()
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-modal flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        :aria-label="title || 'Dialog'"
        @keydown="onKeydown"
        data-testid="t-modal"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm"
          @click="onBackdropClick"
          aria-hidden="true"
        />

        <!-- Dialog panel -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 scale-95 translate-y-2"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-2"
        >
          <div
            v-if="modelValue"
            ref="modalRef"
            :class="[
              'relative w-full rounded-xl shadow-modal',
              'bg-white dark:bg-gray-800',
              'border border-gray-200 dark:border-gray-700',
              'flex flex-col',
              size === 'full' ? 'h-[calc(100vh-2rem)]' : 'max-h-[85vh]',
              sizeClasses[size],
            ]"
          >
            <!-- Header -->
            <div
              v-if="$slots.header || title || closable"
              class="flex items-center justify-between gap-3 px-6 py-4 border-b border-gray-100 dark:border-gray-700 shrink-0"
            >
              <slot name="header">
                <h2
                  v-if="title"
                  class="text-lg font-semibold text-gray-900 dark:text-white leading-tight"
                >
                  {{ title }}
                </h2>
                <span v-else />
              </slot>

              <!-- Close button -->
              <button
                v-if="closable"
                type="button"
                class="shrink-0 p-1 -mr-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors duration-150"
                aria-label="Schließen"
                @click="close"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 overflow-y-auto px-6 py-4">
              <slot />
            </div>

            <!-- Footer -->
            <div
              v-if="$slots.footer"
              class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 dark:border-gray-700 shrink-0"
            >
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
