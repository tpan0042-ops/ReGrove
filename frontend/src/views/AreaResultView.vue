<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'

const route = useRoute()

// Get the postcode from the URL.
const postcode = ref(route.params.postcode)

// Store species returned by FastAPI.
const species = ref([])

// Page states.
const loading = ref(true)
const errorMessage = ref('')

// Load locally relevant species from the backend.
const loadLocalSpecies = async () => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/local-species/${postcode.value}`
    )

    if (!response.ok) {
      throw new Error('Failed to load local species')
    }

    const data = await response.json()

    species.value = data.species
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Unable to load local biodiversity data.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLocalSpecies()
})
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <!-- Area heading -->
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

      <!-- Area data summary -->
      <section class="area-summary">

        <div class="summary-item">
          <span>Species evidence</span>

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

      <!-- Loading state -->
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

        <!-- Keep original vegetation layout -->
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

      <!-- Error state -->
      <section
        v-else-if="errorMessage"
        class="result-details"
      >

        <div class="wildlife-card">

          <h2>What lives here?</h2>

          <p class="wildlife-note">
            Groups spotted in local records
          </p>

          <div class="insufficient-species-message">
            <strong>Unable to load local data</strong>

            <p>
              {{ errorMessage }}
            </p>
          </div>

        </div>

        <!-- Keep original vegetation layout -->
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

      <!-- Main results -->
      <section
        v-else
        class="result-details"
      >

        <!-- Wildlife / species card -->
        <div class="wildlife-card">

          <h2>What lives here?</h2>

          <p class="wildlife-note">
            Groups spotted in local records
          </p>

          <!-- Database species -->
          <div
            v-if="species.length > 0"
            class="wildlife-groups"
          >

            <div
              v-for="(plant, index) in species"
              :key="plant.plant_species_id"
              class="wildlife-item"
            >

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

          <!-- Insufficient data -->
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

        <!-- Original vegetation context -->
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

    </main>
  </div>
</template>