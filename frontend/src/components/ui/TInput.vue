<script setup>
/**
 * TInput.vue — TREFF Design System Input Component.
 *
 * A form input with built-in label, error state, helper text, and v-model support.
 * Follows the TREFF design system's spacing, typography, and color tokens.
 *
 * Props:
 *   modelValue  — v-model binding value
 *   label       (String)  — Input label text
 *   placeholder (String)  — Placeholder text
 *   error       (String)  — Error message (shows red border + error text)
 *   helperText  (String)  — Helper text below input
 *   type        (String)  — HTML input type (default: 'text')
 *   disabled    (Boolean) — Disables the input
 *   required    (Boolean) — Marks as required (adds asterisk)
 *   id          (String)  — Explicit input ID (auto-generated if not provided)
 *   size        (String)  — 'sm' | 'md' | 'lg' (default: 'md')
 *   textarea    (Boolean) — Render as textarea instead of input
 *   rows        (Number)  — Textarea rows (default: 3)
 *
 * Slots:
 *   prefix — Content inside the input, before the value (e.g. icon)
 *   suffix — Content inside the input, after the value (e.g. icon, button)
 *
 * Events:
 *   update:modelValue — v-model emission
 *   focus
 *   blur
 */
import { computed, ref, useId } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  error: {
    type: String,
    default: '',
  },
  helperText: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  id: {
    type: String,
    default: null,
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  textarea: {
    type: Boolean,
    default: false,
  },
  rows: {
    type: Number,
    default: 3,
  },
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])

const isFocused = ref(false)

// Auto-generate input ID if not provided
const inputId = computed(() => props.id || `t-input-${Math.random().toString(36).slice(2, 9)}`)
const errorId = computed(() => `${inputId.value}-error`)
const helperId = computed(() => `${inputId.value}-helper`)

// The component to render
const inputComponent = computed(() => props.textarea ? 'textarea' : 'input')

// Size classes for the input element
const sizeClasses = {
  sm: 'px-2.5 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-3 text-base',
}

const labelSizeClasses = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-sm',
}

// Input wrapper classes
const inputClasses = computed(() => [
  // Base
  'block w-full rounded-lg transition-all duration-200',
  'bg-white dark:bg-gray-800',
  'text-gray-900 dark:text-white',
  'placeholder-gray-400 dark:placeholder-gray-500',
  // Size
  sizeClasses[props.size],
  // Border states
  props.error
    ? 'border-2 border-red-500 dark:border-red-400 focus:ring-2 focus:ring-red-200 dark:focus:ring-red-800'
    : [
        'border border-gray-300 dark:border-gray-600',
        'focus:border-primary-500 dark:focus:border-primary-400',
        'focus:ring-2 focus:ring-primary-100 dark:focus:ring-primary-900',
      ].join(' '),
  // Disabled
  props.disabled
    ? 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-900'
    : '',
  // Has prefix/suffix adjustments
  'outline-none',
])

function onInput(e) {
  emit('update:modelValue', e.target.value)
}

function onFocus(e) {
  isFocused.value = true
  emit('focus', e)
}

function onBlur(e) {
  isFocused.value = false
  emit('blur', e)
}
</script>

<template>
  <div class="w-full" data-testid="t-input">
    <!-- Label -->
    <label
      v-if="label"
      :for="inputId"
      :class="[
        'block font-medium mb-1.5',
        labelSizeClasses[size],
        error ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300',
      ]"
    >
      {{ label }}
      <span v-if="required" class="text-red-500 ml-0.5" aria-hidden="true">*</span>
    </label>

    <!-- Input wrapper (for prefix/suffix slots) -->
    <div class="relative">
      <!-- Prefix -->
      <div
        v-if="$slots.prefix"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 dark:text-gray-500"
      >
        <slot name="prefix" />
      </div>

      <!-- Input / Textarea -->
      <component
        :is="inputComponent"
        :id="inputId"
        :value="modelValue"
        :type="!textarea ? type : undefined"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :rows="textarea ? rows : undefined"
        :class="[
          inputClasses,
          $slots.prefix ? 'pl-10' : '',
          $slots.suffix ? 'pr-10' : '',
        ]"
        :aria-invalid="!!error"
        :aria-describedby="error ? errorId : helperText ? helperId : undefined"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
      />

      <!-- Suffix -->
      <div
        v-if="$slots.suffix"
        class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 dark:text-gray-500"
      >
        <slot name="suffix" />
      </div>
    </div>

    <!-- Error message -->
    <p
      v-if="error"
      :id="errorId"
      class="mt-1.5 text-xs text-red-600 dark:text-red-400 flex items-center gap-1"
      role="alert"
    >
      <svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
      {{ error }}
    </p>

    <!-- Helper text -->
    <p
      v-else-if="helperText"
      :id="helperId"
      class="mt-1.5 text-xs text-gray-500 dark:text-gray-400"
    >
      {{ helperText }}
    </p>
  </div>
</template>
