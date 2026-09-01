<script setup>
// This page lets the user search for a local area by suburb or postcode.
// It then sends the user to the matching biodiversity result page.

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'

const router = useRouter()

// Store the suburb or postcode entered by the user.
const searchArea = ref('')

// Search the entered area and open its result page.
const searchLocalArea = () => {
  const value = searchArea.value.trim()

  // I think an empty search should not open a result page.
  if (!value) {
    return
  }

  // I think using the four-digit postcode is more reliable when the user
  // enters something like "Clayton 3168".
  const postcodeMatch = value.match(/\b\d{4}\b/)

  if (postcodeMatch) {
    router.push(`/area/${postcodeMatch[0]}`)
  } else {
    // If there is no postcode, keep the entered suburb text in the URL.
    router.push(`/area/${encodeURIComponent(value)}`)
  }
}
</script>

<template>
  <div class="page-layout">

    <!-- Reuse the main sidebar for navigation. -->
    <AppSidebar />

    <main class="page-content">

      <div class="explore-layout">

        <!-- Main search section for the local area. -->
        <div class="explore-main">
          <h1>Explore Area</h1>
          <h3>Discover biodiversity in your local area</h3>

          <p class="explore-description">
            Search by suburb or postcode to explore open-data-backed local context.
          </p>

          <!-- Users can search with the button or press Enter. -->
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
              Search
            </button>
          </div>

          <!-- Quick links for some example areas. -->
          <p class="popular-title">Popular searches</p>

          <div class="popular-searches">
            <RouterLink to="/area/3168">
              Clayton 3168
            </RouterLink>

            <RouterLink to="/area/3130">
              Blackburn 3130
            </RouterLink>

            <RouterLink to="/area/3052">
              Parkville 3052
            </RouterLink>
          </div>

          <!-- Short message used in the Explore Area design. -->
          <div class="explore-message">
            <h2>
              The more we know,<br>
              the more we can grow.
            </h2>
          </div>
        </div>

        <!-- Show an illustrative Melbourne area map beside the search section. -->
        <div class="melbourne-card">
          <h3>Greater Melbourne</h3>

          <div class="melbourne-placeholder">
            <p>Local biodiversity area</p>
          </div>

          <p class="map-label">Illustrative area map</p>
          <small>Actual results depend on postcode entered.</small>
        </div>

      </div>

    </main>
  </div>
</template>