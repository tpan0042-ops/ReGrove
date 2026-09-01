<script setup>
// This component contains the first step of the My Space assessment.
// It collects the user's space type and sunlight level before moving to the next step.

import { ref } from 'vue'

// Allow this component to tell the parent page when Step 1 is complete.
const emit = defineEmits(['next-step'])

// Store the user's selected space type and sunlight level.
const spaceType = ref('')
const sunlight = ref('')

// Check the user's selections before moving to the next assessment step.
const goNext = () => {
  // I think both questions should be answered before the user can continue.
  if (spaceType.value === '' || sunlight.value === '') {
    return
  }

  // Tell AssessmentView that the user can move to the next step.
  emit('next-step')
}
</script>

<template>
  <div class="assessment-form">

    <!-- First question: identify the type of outdoor space. -->
    <div class="form-question">
      <h3>What best describes your space?</h3>

      <div class="space-options">

        <!-- Store the selected option in spaceType using v-model. -->
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

    <!-- Second question: identify how much sunlight the space receives. -->
    <div class="form-question">
      <h3>How much sunlight does your space get?</h3>

      <div class="sunlight-options">

        <!-- Store the selected sunlight option in the sunlight variable. -->
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

    <!-- Check the answers and continue to Step 2 when the button is clicked. -->
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