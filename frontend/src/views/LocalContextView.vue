<script setup>
// This page lets the user search for a local area by suburb or postcode.
// It then sends the user to the matching biodiversity result page.

import { ref } from 'vue'
import { useRouter } from 'vue-router'

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
  <!-- This page does not use AppSidebar anymore, same as My Space.
       It is now a full background photo with the search card and the
       Greater Melbourne card floating on top of it. -->
  <section class="explore-page">
    <img
      class="explore-page-image"
      src="../assets/EA_background.png"
      alt="A garden path lined with native flowers and trees"
    />

    <!-- Same light tint layer as the My Space page. -->
    <div class="explore-page-tint"></div>

    <div class="explore-page-overlay">

      <div class="explore-layout">

        <!-- Main search section for the local area. -->
        <div class="explore-main">
          <h1>Explore Area</h1>
          <h3>Discover biodiversity in your local area</h3>

          <!-- Short message used in the Explore Area design. Sits right
               under the heading, above the search bar, on a translucent
               grey panel over the photo. -->
          <div class="explore-message">
            <h2>
              The more we know,<br>
              the more we can grow.
            </h2>
          </div>

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
              Explore
            </button>
          </div>

          <!-- Quick links for some example areas. The search bar above
               already covers the "explore" action, so there is no
               separate button here anymore. -->
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

        <!-- Show an illustrative Melbourne area map beside the search section. -->
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
