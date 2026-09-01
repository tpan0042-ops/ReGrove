<script setup>
// This page controls the three-step My Space assessment.
// It shows the current step and uses AssessmentForm for the first set of questions.

import { ref } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import AssessmentForm from '../components/AssessmentForm.vue'

// Store the current assessment step.
const currentStep = ref(1)

// Move to the next assessment step.
const nextStep = () => {
  // I think the step number should stop at 3 because this page
  // currently only has three assessment stages.
  if (currentStep.value < 3) {
    currentStep.value = currentStep.value + 1
  }
}
</script>

<template>
  <div class="page-layout">

    <!-- Reuse the main sidebar for navigation. -->
    <AppSidebar />

    <main class="page-content">

      <!-- Show the assessment title and current progress. -->
      <div class="assessment-heading">
        <div>
          <h1>My Space</h1>
          <p>Tell us about your outdoor space</p>
          <small>
            This helps us understand your space and shape locally relevant guidance.
          </small>
        </div>

        <!-- Update the step number and progress line with currentStep. -->
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

      <!-- Show the content for the current assessment step. -->
      <div class="assessment-body">

        <!-- Step 1 uses the separate AssessmentForm component. -->
        <AssessmentForm
          v-if="currentStep === 1"
          @next-step="nextStep"
        />

        <!-- Step 2 is currently a placeholder for later questions. -->
        <div
          v-if="currentStep === 2"
          class="assessment-form"
        >
          <h2>Step 2</h2>
          <p>The next assessment questions will go here.</p>
        </div>

        <!-- Step 3 is currently a placeholder for the final questions. -->
        <div
          v-if="currentStep === 3"
          class="assessment-form"
        >
          <h2>Step 3</h2>
          <p>The final assessment questions will go here.</p>
        </div>

        <!-- Keep the supporting image beside the assessment form. -->
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