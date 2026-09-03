<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'
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
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

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

          <h1>{{ areaData.postcode }}</h1>
          <h3>Local biodiversity snapshot</h3>

          <p>
            Explore local species records, vegetation context and available data.
          </p>

        </div>

        <ContextNotice :suburb="areaData.postcode" />

        <section class="area-summary">

          <div class="summary-item">
            <span>Vegetation retained</span>
            <strong>{{ areaData.vegetation_retained.length }} type(s)</strong>
          </div>

          <div class="summary-item">
            <span>Vegetation lost</span>
            <strong>{{ areaData.vegetation_lost.length }} type(s)</strong>
          </div>

          <div class="summary-item">
            <span>Current species evidence</span>
            <strong>{{ areaData.current_species.length }} found</strong>
          </div>

          <div class="summary-item">
            <span>Historical species evidence</span>
            <strong>{{ areaData.historical_species.length }} found</strong>
          </div>

        </section>

        <section class="result-details">

          <div class="wildlife-card">

            <h2>What lives here now?</h2>

            <p class="wildlife-note">
              Species with current occurrence evidence
            </p>

            <div
              v-for="species in areaData.current_species"
              :key="species.scientific_name"
              class="species-row"
            >
              <strong>{{ species.common_name || species.scientific_name }}</strong>
              <span>Confidence: {{ species.confidence }}</span>
            </div>

            <p v-if="areaData.current_species.length === 0">
              No current species evidence found for this area.
            </p>

          </div>

          <div class="vegetation-card">

            <h2>Vegetation context</h2>

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

          </div>

        </section>

      </div>

    </main>

  </div>
</template>
