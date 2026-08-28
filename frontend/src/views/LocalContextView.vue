<script setup>
import { ref } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'

// Store the suburb or postcode entered by the user.
const searchArea = ref('')
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
            >

            <button type="button">
              Search
            </button>
          </div>

          <p class="popular-title">Popular searches</p>

          <div class="popular-searches">
            <RouterLink to="/area/clayton-3168">
              Clayton 3168
            </RouterLink>
            <RouterLink to="/area/blackburn-3130">
              Blackburn 3130
            </RouterLink>
            <RouterLink to="/area/parkville-3052">
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