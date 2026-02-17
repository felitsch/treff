/**
 * Emoji-to-Heroicon name mapping utility.
 *
 * Maps emoji characters (previously used as icons) to their AppIcon name equivalents.
 * Used for dynamic icon rendering where emoji strings were stored in data.
 *
 * Usage:
 *   import { emojiToIcon } from '@/utils/emojiToIcon'
 *   const iconName = emojiToIcon('📊') // returns 'chart-bar'
 */

const emojiMap = {
  // Navigation & Dashboard
  '📊': 'chart-bar',
  '✏️': 'pencil-square',
  '⚡': 'bolt',
  '💾': 'document',
  '📅': 'calendar',
  '🗓️': 'calendar-days',
  '📖': 'book-open',
  '🔄': 'arrow-path',
  '🖼️': 'photo',
  '📄': 'document-text',
  '📋': 'clipboard-list',
  '🎓': 'academic-cap',
  '🎬': 'film',
  '🎞️': 'video-camera',
  '✂️': 'scissors',
  '🏷️': 'tag',
  '📤': 'export',
  '🎵': 'musical-note',
  '📝': 'document-text',
  '🧠': 'sparkles',
  '📈': 'analytics',
  '⚙️': 'settings',
  '🎨': 'paint-brush',

  // Content Types
  '📸': 'camera',
  '📱': 'device-mobile',
  '📷': 'camera',

  // Content Pillars
  '🌍': 'globe',
  '💡': 'light-bulb',
  '❓': 'question-mark-circle',
  '💬': 'chat-bubble',
  '👀': 'eye',
  '⏰': 'clock',
  '📚': 'book-open',
  '🎪': 'star',
  '📢': 'megaphone',

  // Tone Styles
  '🎯': 'fire',
  '😂': 'face-smile',
  '🥺': 'heart',
  '💪': 'rocket',
  '🥰': 'heart',
  '🔥': 'fire',
  '🎭': 'user',

  // Status & Feedback
  '✅': 'check-circle',
  '❌': 'x-circle',
  '✕': 'x-mark',
  '⏳': 'clock',
  '🔔': 'bell',
  '📦': 'archive',
  '✨': 'sparkles',
  '⭐': 'star',
  '🌟': 'star',
  '💫': 'sparkles',

  // Security
  '🔐': 'lock',
  '🔒': 'lock',
  '🔑': 'key',

  // Celebration
  '🎊': 'trophy',
  '🎉': 'trophy',
  '🏆': 'trophy',
  '🤓': 'academic-cap',

  // Travel & Misc
  '✈️': 'paper-airplane',

  // Music categories
  '💝': 'heart',
  '🎈': 'star',

  // Animation
  '🌅': 'sparkles',

  // Media
  '🎚️': 'adjustments-vertical',
  '🎤': 'microphone',

  // Generic
  '→': 'chevron-right',
  '←': 'chevron-left',
}

/**
 * Convert an emoji character to its Heroicon name equivalent.
 * @param {string} emoji - The emoji character to convert
 * @param {string} fallback - Fallback icon name if emoji not found (default: 'question-mark-circle')
 * @returns {string} The icon name for use with AppIcon component
 */
export function emojiToIcon(emoji, fallback = 'question-mark-circle') {
  if (!emoji) return fallback
  return emojiMap[emoji.trim()] || fallback
}

/**
 * Check if a string contains emoji characters.
 * @param {string} str - String to check
 * @returns {boolean}
 */
export function containsEmoji(str) {
  if (!str) return false
  const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FEFF}\u{1F000}-\u{1F02F}\u{1F0A0}-\u{1F0FF}\u{1F100}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{200D}\u{FE0F}]/u
  return emojiRegex.test(str)
}

export default emojiMap
