<script setup>
import AppSidebar from '../components/AppSidebar.vue'
import AssessmentForm from '../components/AssessmentForm.vue'
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
          <span>Step 1 of 3</span>

          <div class="progress-line">
            <div class="progress-current"></div>
          </div>
        </div>
      </div>

      <div class="assessment-body">

        <AssessmentForm />

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