<script setup>
// This page shows the local biodiversity results for the postcode selected by the user.
// It gets species data from the FastAPI backend and shows different states based on the result.

import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// Read the postcode from the current URL.
const postcode = ref(route.params.postcode)

// Store the species returned by the FastAPI backend.
const species = ref([])

// Store the loading and error states for this page.
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

    // Save the species from the JSON response so the template can display them.
    species.value = data.species
  } catch (error) {
    console.error(error)

    // I think showing a clear message is better than leaving the result area empty
    // when the backend cannot return the local biodiversity data.
    errorMessage.value = 'Unable to load local biodiversity data.'
  } finally {
    // Stop the loading state whether the request succeeds or fails.
    loading.value = false
  }
}

// Load the local biodiversity data when this page first opens.
onMounted(() => {
  loadLocalSpecies()
})
</script>

<template>
  <!-- This page does not use AppSidebar anymore, same as My Space and
       Explore Area. It is now a full background photo with the result
       cards floating on top of it. -->
  <section class="area-result-page">
    <img
      class="area-result-page-image"
      src="../assets/postcode_ResultPage.png"
      alt="A meadow of native wildflowers"
    />

    <!-- Same light tint layer as the other full-photo pages. -->
    <div class="area-result-page-tint"></div>

    <div class="area-result-page-overlay">

      <!-- Show the postcode and introduce the local biodiversity result. -->
      <div class="area-result-heading">

        <RouterLink class="back-area-link" to="/explore">
          Back to Explore Area
        </RouterLink>

        <h1>Postcode {{ postcode }}</h1>

        <h3>Local biodiversity snapshot</h3>

        <p>
          Explore local species records, vegetation context and available data.
        </p>

      </div>

      <!-- Give the user a quick summary of what information is currently available. -->
      <section class="area-summary">

        <div class="summary-item">
          <span>Species evidence</span>

          <!-- Species evidence is available when the backend returns at least one species. -->
          <strong v-if="species.length > 0">
            Available
          </strong>

          <strong v-else>
            To assess
          </strong>
        </div>

        <div class="summary-item">
          <span>Vegetation survival</span>
          <strong>Available</strong>
        </div>

        <div class="summary-item">
          <span>Habitat potential</span>
          <strong>To assess</strong>
        </div>

        <div class="summary-item">
          <span>Data confidence</span>
          <strong>To assess</strong>
        </div>

      </section>

      <!-- Show a simple loading state while waiting for the API response. -->
      <section
        v-if="loading"
        class="result-details"
      >
        <div class="wildlife-card">
          <h2>What lives here?</h2>

          <p>
            Loading local species...
          </p>
        </div>

        <!-- Keep the current prototype vegetation layout while species are loading. -->
        <div class="vegetation-card">

          <h2>Vegetation context</h2>

          <div class="vegetation-row">
            <span>Plains Grassy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-1"></div>
            </div>
          </div>

          <div class="vegetation-row">
            <span>Swamp Scrub Wetland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-2"></div>
            </div>
          </div>

          <div class="vegetation-row">
            <span>Heathy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-3"></div>
            </div>
          </div>

          <p class="vegetation-note">
            No percentages shown until validated.
          </p>

        </div>
      </section>

      <!-- Show an error state if the API request cannot be completed. -->
      <section
        v-else-if="errorMessage"
        class="result-details"
      >

        <div class="wildlife-card">

          <h2>What lives here?</h2>

          <p class="wildlife-note">
            Groups spotted in local records
          </p>

          <!-- I think a clear error message is more useful than a blank result card. -->
          <div class="insufficient-species-message">
            <strong>Unable to load local data</strong>

            <p>
              {{ errorMessage }}
            </p>
          </div>

        </div>

        <!-- Keep the current prototype vegetation layout if the species request fails. -->
        <div class="vegetation-card">

          <h2>Vegetation context</h2>

          <div class="vegetation-row">
            <span>Plains Grassy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-1"></div>
            </div>
          </div>

          <div class="vegetation-row">
            <span>Swamp Scrub Wetland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-2"></div>
            </div>
          </div>

          <div class="vegetation-row">
            <span>Heathy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-3"></div>
            </div>
          </div>

          <p class="vegetation-note">
            No percentages shown until validated.
          </p>

        </div>

      </section>

      <!-- Show the main result layout after the API request is complete. -->
      <section
        v-else
        class="result-details"
      >

        <!-- Display locally relevant species returned from the database through FastAPI. -->
        <div class="wildlife-card">

          <h2>What lives here?</h2>

          <p class="wildlife-note">
            Groups spotted in local records
          </p>

          <!-- Create one visual item for each species returned by the API. -->
          <div
            v-if="species.length > 0"
            class="wildlife-groups"
          >

            <div
              v-for="(plant, index) in species"
              :key="plant.plant_species_id"
              class="wildlife-item"
            >

              <!-- Alternate the circle style so neighbouring species are easier to separate. -->
              <div
                :class="[
                  'wildlife-circle',
                  index % 2 === 0
                    ? 'circle-yellow'
                    : 'circle-green'
                ]"
              ></div>

              <strong>
                {{ plant.common_name }}
              </strong>

              <span class="species-scientific-name">
                {{ plant.scientific_name }}
              </span>

              <small class="species-native-status">
                {{ plant.native_status }}
              </small>

            </div>

          </div>

          <!-- I think users should get an honest fallback message when this postcode has no species data. -->
          <div
            v-else
            class="insufficient-species-message"
          >

            <strong>Insufficient local data</strong>

            <p>
              There is currently not enough local species information
              available for postcode {{ postcode }}.
            </p>

          </div>

        </div>

        <!-- This vegetation section is still using the current prototype content. -->
        <div class="vegetation-card">

          <h2>Vegetation context</h2>

          <div class="vegetation-row">

            <span>Plains Grassy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-1"></div>
            </div>

          </div>

          <div class="vegetation-row">

            <span>Swamp Scrub Wetland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-2"></div>
            </div>

          </div>

          <div class="vegetation-row">

            <span>Heathy Woodland</span>

            <div class="vegetation-bar">
              <div class="vegetation-fill vegetation-fill-3"></div>
            </div>

          </div>

          <p class="vegetation-note">
            No percentages shown until validated.
          </p>

        </div>

      </section>

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