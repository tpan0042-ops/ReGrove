<script setup>
import { ref } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import AssessmentForm from '../components/AssessmentForm.vue'

const currentStep = ref(1)

// Move to the next assessment step.
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value = currentStep.value + 1
  }
}
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <div class="assessment-heading">
        <div>
          <h1>My Space</h1>
          <p>Tell us about your outdoor space</p>
          <small>
            This helps us understand your space and shape locally relevant guidance.
          </small>
        </div>

        <div class="step-info">
          <span>Step {{ currentStep }} of 3</span>

          <div class="progress-line">
            <div
              v-if="currentStep === 1"
              class="progress-step-1"
            ></div>

            <div
              v-if="currentStep === 2"
              class="progress-step-2"
            ></div>

            <div
              v-if="currentStep === 3"
              class="progress-step-3"
            ></div>
          </div>
        </div>
      </div>

      <div class="assessment-body">

        <AssessmentForm
          v-if="currentStep === 1"
          @next-step="nextStep"
        />

        <div
          v-if="currentStep === 2"
          class="assessment-form"
        >
          <h2>Step 2</h2>
          <p>The next assessment questions will go here.</p>
        </div>

        <div
          v-if="currentStep === 3"
          class="assessment-form"
        >
          <h2>Step 3</h2>
          <p>The final assessment questions will go here.</p>
        </div>

        <div class="myspace-image-card">
          <div class="myspace-image-text">
            <strong>Small spaces matter</strong>
            <p>Local biodiversity can support your community.</p>
          </div>
        </div>

      </div>

    </main>

  </div>
</template>