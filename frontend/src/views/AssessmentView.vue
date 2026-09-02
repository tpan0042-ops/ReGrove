<script setup>
// This page controls the three-step My Space assessment.
// It shows the current step and uses AssessmentForm for the first set of questions.

import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AssessmentForm from '../components/AssessmentForm.vue'

const router = useRouter()

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

// Step 3 is the last step, so finishing it sends the user to Planting Ideas
// instead of moving to another step.
const goToPlanting = () => {
  router.push('/planting')
}
</script>

<template>
  <!-- This page does not use AppSidebar anymore. It is now one big
       background photo with the form and other pieces on top of it. -->
  <section class="myspace-page">
    <img
      class="myspace-page-image"
      src="../assets/MySpace.png"
      alt="A cozy balcony garden with a rattan chair and potted plants"
    />

    <!-- Gray tint sitting on top of the photo, matching the design. -->
    <div class="myspace-page-tint"></div>

    <div class="myspace-page-overlay">

      <!-- Heading and the form share this column so they always line up
           at the same left position and center width, matching the design. -->
      <div class="myspace-column">

        <!-- Show the assessment title, centered above the card. -->
        <div class="assessment-heading">
          <h1>My Space</h1>
          <p>Tell us about your space</p>
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

            <div class="form-actions">
              <button
                class="next-button"
                @click="nextStep"
              >
                Next →
              </button>
            </div>
          </div>

          <!-- Step 3 is currently a placeholder for the final questions.
               Finishing this step sends the user to Planting Ideas. -->
          <div
            v-if="currentStep === 3"
            class="assessment-form"
          >
            <h2>Step 3</h2>
            <p>The final assessment questions will go here.</p>

            <div class="form-actions">
              <button
                class="next-button"
                @click="goToPlanting"
              >
                Finish →
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Step counter and progress bar, now floating over the photo. -->
      <div class="myspace-progress">
        <span>{{ currentStep }} of 3</span>

        <div class="progress-line">
          <div v-if="currentStep === 1" class="progress-step-1"></div>
          <div v-if="currentStep === 2" class="progress-step-2"></div>
          <div v-if="currentStep === 3" class="progress-step-3"></div>
        </div>

        <small>Garden image</small>
      </div>

      <!-- Short note that used to sit on the separate image card. -->
      <div class="myspace-image-text">
        <strong>Small spaces matter.</strong>
        <p>Even a balcony can support local biodiversity.</p>
      </div>

      <!-- "Your impact" used to live in the sidebar. Show it here now
           since this page does not have a sidebar anymore. -->
      <div class="impact-box floating-impact">
        <strong>Your impact</strong>
        <h3>0</h3>
        <p>Actions completed</p>
        <p>Prototype</p>
      </div>

    </div>
  </section>
</template>
