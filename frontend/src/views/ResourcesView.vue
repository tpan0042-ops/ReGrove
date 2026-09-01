<script setup>
import AppSidebar from '../components/AppSidebar.vue'
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <!-- Top two-column section -->
      <div class="resources-top">

        <!-- Left side -->
        <div class="resources-left">

          <div class="resources-heading">
            <h1>Your local biodiversity context</h1>
            <h3>Clayton, Victoria</h3>

            <p>
              A simple view of the kinds of environmental information ReGrove can bring together.
            </p>
          </div>

          <div class="context-card">
            <h2>What is recorded around here?</h2>

            <div class="context-highlight">
              <strong>Local species observations</strong>

              <p>
                ReGrove can summarise nearby biodiversity records from open datasets
                and group them into simple categories such as birds, pollinators and other fauna.
              </p>
            </div>

            <p class="data-source-link">
              View data source
            </p>
          </div>

        </div>

        <!-- Right side -->
        <div class="resources-right">

          <div class="garden-placeholder">
            Garden image
          </div>

          <div class="important-card">
            <strong>Important</strong>

            <p>
              Fewer records do not automatically mean that biodiversity has disappeared.
              Observation effort can vary by area.
            </p>
          </div>

        </div>

      </div>

      <!-- Bottom section -->
      <h2 class="context-action-title">
        From local context to action
      </h2>

      <div class="context-action">

        <div>
          <span>Next step</span>

          <p>
            Use your space profile + local context to explore suitable planting ideas.
          </p>
        </div>

        <button type="button">
          See planting ideas →
        </button>

      </div>

    </main>

  </div>
</template>