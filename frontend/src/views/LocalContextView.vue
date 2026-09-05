<script setup>
// This page lets the user search for a local area by suburb or postcode.
// It then sends the user to the matching biodiversity result page.

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ContextNotice from '../components/ContextNotice.vue'

const router = useRouter()
const searchArea = ref('')

// Search the entered area and open its result page.
const searchLocalArea = () => {
  const value = searchArea.value.trim()

  if (!value) {
    return
  }

  const postcodeMatch = value.match(/\b\d{4}\b/)

  if (postcodeMatch) {
    router.push(`/area/${postcodeMatch[0]}`)
  } else {
    router.push(`/area/${encodeURIComponent(value)}`)
  }
}
</script>

<template>
  <section class="explore-page">
    <img
      class="explore-page-image"
      src="../assets/EA_background.png"
      alt="A garden path lined with native flowers and trees"
    />

    <div class="explore-page-tint"></div>

    <div class="explore-page-overlay">

      <div class="explore-layout">

        <div class="explore-main">
          <h1>Explore Area</h1>
          <h3>Discover biodiversity in your local area</h3>

          <p class="explore-description">
            Search by suburb or postcode to explore open-data-backed local context.
          </p>

          <ContextNotice suburb="your selected area" />

          <div class="explore-message">
            <h2>
              The more we know,<br>
              the more we can grow.
            </h2>
          </div>

          <div class="area-search">
            <input
              type="text"
              v-model="searchArea"
              placeholder="Search suburb or postcode"
              @keyup.enter="searchLocalArea"
            >

            <button
              type="button"
              @click="searchLocalArea"
            >
              Explore
            </button>
          </div>

          <p class="popular-title">Popular searches</p>

          <div class="popular-searches">
            <RouterLink to="/area/3168">
              Clayton 3168
            </RouterLink>

            <RouterLink to="/area/3175">
              Dandenong 3175
            </RouterLink>

            <RouterLink to="/area/3199">
              Frankston 3199
            </RouterLink>
          </div>
        </div>

        <div class="melbourne-card">
          <h3>Greater Melbourne</h3>

          <div class="melbourne-placeholder"></div>

          <p class="map-label">Illustrative area grid</p>
          <small>Actual results depend on available datasets.</small>
        </div>

      </div>

    </div>
  </section>
</template>