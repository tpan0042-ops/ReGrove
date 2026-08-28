<script setup>
import { ref } from 'vue'

const emit = defineEmits(['next-step'])

// Store the user's selections.
const spaceType = ref('')
const sunlight = ref('')

// Check the first step before continuing.
const goNext = () => {
  if (spaceType.value === '' || sunlight.value === '') {
    return
  }

  emit('next-step')
}
</script>

<template>
  <div class="assessment-form">

    <div class="form-question">
      <h3>What best describes your space?</h3>

      <div class="space-options">

        <label class="space-option">
          <input
            type="radio"
            value="House"
            v-model="spaceType"
          >
          <strong>HOUSE</strong>
          <span>Backyard</span>
        </label>

        <label class="space-option">
          <input
            type="radio"
            value="Balcony"
            v-model="spaceType"
          >
          <strong>BALCONY</strong>
          <span>Balcony / Terrace</span>
        </label>

        <label class="space-option">
          <input
            type="radio"
            value="Courtyard"
            v-model="spaceType"
          >
          <strong>COURT</strong>
          <span>Courtyard</span>
        </label>

      </div>
    </div>

    <div class="form-question">
      <h3>How much sunlight does your space get?</h3>

      <div class="sunlight-options">

        <label>
          <input
            type="radio"
            value="Mostly shade"
            v-model="sunlight"
          >
          Mostly shade
        </label>

        <label>
          <input
            type="radio"
            value="Part shade"
            v-model="sunlight"
          >
          Part shade
        </label>

        <label>
          <input
            type="radio"
            value="Part sun"
            v-model="sunlight"
          >
          Part sun
        </label>

        <label>
          <input
            type="radio"
            value="Mostly sun"
            v-model="sunlight"
          >
          Mostly sun
        </label>

      </div>
    </div>

    <div class="form-actions">
      <button
        class="next-button"
        @click="goNext"
      >
        Next →
      </button>
    </div>

  </div>
</template>