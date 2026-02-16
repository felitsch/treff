<script setup>
/**
 * BaseCard.vue — Reusable card component for the TREFF Design System.
 *
 * Props:
 *   title       (String)  — Card title text (optional, rendered as h3)
 *   subtitle    (String)  — Subtitle text below title (optional)
 *   padding     (String)  — Body padding size: 'none' | 'sm' | 'md' | 'lg' (default: 'md')
 *   hoverable   (Boolean) — Adds hover shadow elevation + slight translate
 *   clickable   (Boolean) — Adds cursor-pointer and click emission
 *   flat        (Boolean) — Uses flat style (no border, subtle bg) for nested cards
 *   noBorder    (Boolean) — Removes border (useful for custom styled cards)
 *   headerDivider (Boolean) — Shows border-b between header and body (default: true when header present)
 *
 * Slots:
 *   header       — Replaces the default title/subtitle in the header area
 *   headerAction — Right-aligned action area in header (button, link, badge)
 *   default      — Card body content
 *   footer       — Card footer (rendered with top border separator)
 *
 * Events:
 *   click        — Emitted when clickable card is clicked
 */

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  padding: {
    type: String,
    default: 'md',
    validator: (v) => ['none', 'sm', 'md', 'lg'].includes(v),
  },
  hoverable: {
    type: Boolean,
    default: false,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
  flat: {
    type: Boolean,
    default: false,
  },
  noBorder: {
    type: Boolean,
    default: false,
  },
  headerDivider: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['click'])

function handleClick(e) {
  if (props.clickable) {
    emit('click', e)
  }
}

// Body padding classes
const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

// Header always uses p-5 for section-style cards; for compact cards it matches body padding
const headerPaddingClasses = {
  none: 'p-5',
  sm: 'px-3 pt-3',
  md: 'px-4 pt-4',
  lg: 'px-6 pt-6',
}

const footerPaddingClasses = {
  none: 'p-5',
  sm: 'px-3 pb-3 pt-3',
  md: 'px-4 pb-4 pt-3',
  lg: 'px-6 pb-6 pt-4',
}
</script>

<template>
  <div
    :class="[
      'rounded-xl overflow-hidden transition-all duration-200',
      // Background & border
      flat
        ? 'bg-gray-50 dark:bg-gray-800/50'
        : 'bg-white dark:bg-gray-800',
      !flat && !noBorder ? 'border border-gray-200 dark:border-gray-700' : '',
      // Shadow
      flat ? '' : 'shadow-sm',
      // Hover effect
      hoverable ? 'hover:shadow-md hover:-translate-y-0.5' : '',
      // Clickable
      clickable ? 'cursor-pointer' : '',
    ]"
    :role="clickable ? 'button' : undefined"
    :tabindex="clickable ? 0 : undefined"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
    data-testid="base-card"
  >
    <!-- Header (only rendered when title, subtitle, header slot, or headerAction slot is used) -->
    <div
      v-if="$slots.header || title || subtitle || $slots.headerAction"
      :class="[
        'flex items-center justify-between gap-3',
        headerPaddingClasses[padding],
        headerDivider ? 'border-b border-gray-100 dark:border-gray-700 pb-4' : '',
      ]"
    >
      <slot name="header">
        <div class="min-w-0 flex-1">
          <h3
            v-if="title"
            class="text-lg font-semibold text-gray-900 dark:text-white leading-tight"
          >
            {{ title }}
          </h3>
          <p
            v-if="subtitle"
            class="mt-0.5 text-sm text-gray-500 dark:text-gray-400"
          >
            {{ subtitle }}
          </p>
        </div>
      </slot>
      <div v-if="$slots.headerAction" class="flex-shrink-0">
        <slot name="headerAction" />
      </div>
    </div>

    <!-- Body -->
    <div :class="[paddingClasses[padding]]">
      <slot />
    </div>

    <!-- Footer -->
    <div
      v-if="$slots.footer"
      :class="[
        'border-t border-gray-100 dark:border-gray-700',
        footerPaddingClasses[padding],
      ]"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
