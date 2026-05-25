<!-- =============================================================
  TeamMemberCard.vue — Developer profile card for the About page.
  Shows avatar initials, name, and role with hover elevation.
  ============================================================= -->
<template>
  <article
    class="member-card"
    :aria-label="`Team member: ${name}`"
  >
    <!-- Avatar / initials placeholder -->
    <div class="member-avatar" :style="{ background: avatarGradient }" aria-hidden="true">
      <span class="member-initials">{{ initials }}</span>
    </div>

    <!-- Info -->
    <div class="member-info">
      <p class="member-name">{{ name }}</p>
      <p class="member-role">{{ role }}</p>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Full display name */
  name: { type: String, required: true },
  /** Role / position label */
  role: { type: String, required: true },
  /**
   * Optional avatar gradient index (0–3) for color variety.
   * Each member gets a visually distinct but restrained tone.
   */
  colorIndex: { type: Number, default: 0 }
})

/** Derive initials from the first two words of the name */
const initials = computed(() => {
  const parts = props.name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
})

/** Subtle navy-tone gradients — stays within the design palette */
const GRADIENTS = [
  'linear-gradient(135deg, #0f2340 0%, #163356 100%)',  // slate-navy
  'linear-gradient(135deg, #0d1e35 0%, #1e3554 100%)',  // deep-card
  'linear-gradient(135deg, #0f2340 0%, #122a4a 100%)',  // navy-dark
  'linear-gradient(135deg, #0a1628 0%, #163356 100%)',  // navy-deep
]

const avatarGradient = computed(() => GRADIENTS[props.colorIndex % GRADIENTS.length])
</script>

<style scoped>
.member-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.5rem 1.25rem;
  background-color: #0e1c2f;
  border: 1px solid #1e3554;
  border-radius: 0.5rem;
  gap: 1rem;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  cursor: default;
}

.member-card:hover {
  border-color: rgba(56, 189, 248, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
}

/* Avatar circle */
.member-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 1px solid #1e3554;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-initials {
  font-size: 1.125rem;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: -0.02em;
}

/* Text */
.member-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.member-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f4f8;
  margin: 0;
  line-height: 1.3;
}

.member-role {
  font-size: 0.75rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.03em;
}
</style>
