<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'

const router = useRouter()

// Store the suburb or postcode entered by the user.
const searchArea = ref('')

// Open the result page for the entered postcode.
const searchLocalArea = () => {
  const value = searchArea.value.trim()

  if (!value) {
    return
  }

  // If the user enters something like "Clayton 3168",
  // use the postcode at the end.
  const postcodeMatch = value.match(/\b\d{4}\b/)

  if (postcodeMatch) {
    router.push(`/area/${postcodeMatch[0]}`)
  } else {
    router.push(`/area/${encodeURIComponent(value)}`)
  }
}
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <div class="explore-layout">

        <div class="explore-main">
          <h1>Explore Area</h1>
          <h3>Discover biodiversity in your local area</h3>

          <p class="explore-description">
            Search by suburb or postcode to explore open-data-backed local context.
          </p>

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

          <div class="explore-message">
            <h2>
              The more we know,<br>
              the more we can grow.
            </h2>
          </div>
        </div>

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