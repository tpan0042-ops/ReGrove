<script setup>
// This page shows the local biodiversity context for the postcode (or
// suburb text) selected by the user, matching the "Local Insight" design.
//
// It still requests species data from the FastAPI backend in the
// background, same as before, so that data is ready once this page is
// connected to a more detailed species view. The current design does not
// render a species list yet, so loading/error states are not shown.

import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Read the postcode (or suburb text) from the current URL.
const postcode = ref(route.params.postcode)

// Store the species returned by the FastAPI backend. Kept for later use,
// not rendered by the current design.
const species = ref([])

// Store the loading and error states for this page. Also kept for later
// use, not rendered by the current design.
const loading = ref(true)
const errorMessage = ref('')

// Request locally relevant species from the backend.
const loadLocalSpecies = async () => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/local-species/${postcode.value}`
    )

    // I think the page should treat an unsuccessful response as an error
    // instead of trying to display incomplete data.
    if (!response.ok) {
      throw new Error('Failed to load local species')
    }

    const data = await response.json()

    // Save the species from the JSON response for when this page's cards
    // are connected to real species data.
    species.value = data.species
  } catch (error) {
    console.error(error)

    errorMessage.value = 'Unable to load local biodiversity data.'
  } finally {
    loading.value = false
  }
}

// Load the local biodiversity data when this page first opens.
onMounted(() => {
  loadLocalSpecies()
})

// Move on to the Planting Ideas page.
const goToPlantingIdeas = () => {
  router.push('/planting')
}
</script>

<template>
  <!-- This page keeps the same full background photo pattern as the
       other main pages (My Space, Explore Area, Planting Ideas). -->
  <section class="area-result-page">
    <img
      class="area-result-page-image"
      src="../assets/postcode_ResultPage.png"
      alt="A meadow of native wildflowers"
    />

    <!-- Same light tint layer as the other full-photo pages. -->
    <div class="area-result-page-tint"></div>

    <div class="area-result-page-overlay">

      <RouterLink class="back-area-link" to="/explore">
        Back to Explore Area
      </RouterLink>

      <!-- Introduce the local biodiversity context for this area. -->
      <div class="insight-heading">
        <h1>Your local biodiversity context</h1>

        <p class="insight-location">{{ postcode }}</p>

        <p class="insight-intro">
          A simple view of the kinds of environmental information ReGrove can bring together.
        </p>
      </div>

      <!-- Main content: what is recorded, plus a garden image and an
           important note about how to read the data. -->
      <div class="insight-layout">

        <div class="insight-card">
          <h3>What is recorded around here?</h3>

          <div class="insight-species-box">
            <strong>Local species observations</strong>

            <p>
              ReGrove can summarise nearby biodiversity records
              from open datasets and group them into simple categories
              such as birds, pollinators and other fauna.
            </p>
          </div>

          <a
            class="insight-data-link"
            href="https://www.ala.org.au/"
            target="_blank"
            rel="noopener"
          >
            View data source
          </a>
        </div>

        <div class="insight-side">

          <!-- Placeholder for a garden photo for this area, to be added later. -->
          <div class="insight-image-placeholder">
            Garden image
          </div>

          <div class="insight-important">
            <strong>Important</strong>

            <p>
              Fewer records do not automatically mean
              that biodiversity has disappeared.
              Observation effort can vary by area.
            </p>
          </div>

        </div>

      </div>

      <!-- Send the user on to Planting Ideas next. -->
      <h2 class="insight-action-title">From local context to action</h2>

      <div class="insight-action">
        <div>
          <span>Next step</span>

          <p>
            Use your space profile + local context to explore suitable planting ideas.
          </p>
        </div>

        <button
          type="button"
          class="next-button"
          @click="goToPlantingIdeas"
        >
          See planting ideas →
        </button>
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
