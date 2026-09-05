<script setup>
// This page shows the local biodiversity results for the postcode selected by the user.

import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ContextNotice from '../components/ContextNotice.vue'

const route = useRoute()

const areaData = ref(null)
const loading = ref(true)
const error = ref(null)

const API_BASE = 'https://c21wjdpl8f.execute-api.ap-southeast-2.amazonaws.com/default/regrove_api'

async function loadAreaData(postcode) {
  loading.value = true
  error.value = null
  areaData.value = null

  try {
    const response = await fetch(`${API_BASE}/api/area/${postcode}`)
    const data = await response.json()

    if (!data.supported) {
      error.value = `We do not have data for postcode ${postcode} yet.`
    } else {
      areaData.value = data
    }
  } catch (err) {
    error.value = 'Something went wrong loading this area. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAreaData(route.params.postcode)
})

watch(() => route.params.postcode, (newPostcode) => {
  loadAreaData(newPostcode)
})
</script>

<template>
  <section class="area-result-page">
    <img
      class="area-result-page-image"
      src="../assets/postcode_ResultPage.png"
      alt="A meadow of native wildflowers"
    />

    <div class="area-result-page-tint"></div>

    <div class="area-result-page-overlay">

      <div v-if="loading">
        <p>Loading area data...</p>
      </div>

      <div v-else-if="error">
        <p>{{ error }}</p>
      </div>

      <div v-else-if="areaData">

        <div class="area-result-heading">

          <RouterLink class="back-area-link" to="/explore">
            Back to Explore Area
          </RouterLink>

          <h1>Postcode {{ areaData.postcode }}</h1>

          <h3>Local biodiversity snapshot</h3>

          <p>
            Explore local species records, vegetation context and available data.
          </p>

        </div>

        <ContextNotice :suburb="areaData.postcode" />

        <section class="species-timeline">

          <h2 class="timeline-heading">Historical</h2>

          <div class="timeline-cards">
            <div
              v-for="species in areaData.historical_species"
              :key="species.scientific_name"
              class="timeline-card"
            >
              <div class="species-result-text">
                <strong>{{ species.common_name || species.scientific_name }}</strong>
                <span>Confidence: {{ species.confidence }}</span>
              </div>
            </div>
          </div>

          <p v-if="areaData.historical_species.length === 0">
            No historical species evidence found for this area.
          </p>

          <h2 class="timeline-heading">Current</h2>

          <div class="timeline-cards">
            <div
              v-for="species in areaData.current_species"
              :key="species.scientific_name"
              class="timeline-card timeline-card-current"
            >
              <div class="species-result-text">
                <strong>{{ species.common_name || species.scientific_name }}</strong>
                <span>Confidence: {{ species.confidence }}</span>
              </div>
            </div>
          </div>

          <p v-if="areaData.current_species.length === 0">
            No current species evidence found for this area.
          </p>

          <h2 class="timeline-heading">Vegetation context</h2>

          <div
            v-for="evc in areaData.vegetation_retained"
            :key="evc.evc_code"
            class="vegetation-row"
          >
            <span>{{ evc.evc_name }}</span>

            <div class="vegetation-bar">
              <div
                class="vegetation-fill"
                :style="{ width: evc.overlap_percent + '%' }"
              ></div>
            </div>
          </div>

          <p class="vegetation-note">
            {{ areaData.limitation_note }}
          </p>

          <div class="timeline-actions">
            <RouterLink
              class="next-button"
              to="/assessment"
            >
              Next ->
            </RouterLink>
          </div>

        </section>

      </div>

    </div>
  </section>
</template>