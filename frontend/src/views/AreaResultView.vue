<script setup>
import AppSidebar from '../components/AppSidebar.vue'
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

        <h1>Clayton 3168</h1>
        <h3>Local biodiversity snapshot</h3>

        <p>
          Explore local species records, vegetation context and available data.
        </p>

      </div>

      <!-- Area data summary -->
      <section class="area-summary">

        <div class="summary-item">
          <span>Species evidence</span>
          <strong>Available</strong>
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

      <!-- Biodiversity details -->
      <section class="result-details">

        <!-- Wildlife groups -->
        <div class="wildlife-card">

          <h2>What lives here?</h2>

          <p class="wildlife-note">
            Groups spotted in local records
          </p>

          <div class="wildlife-groups">

            <div class="wildlife-item">
              <div class="wildlife-circle circle-yellow"></div>
              <strong>Birds</strong>
            </div>

            <div class="wildlife-item">
              <div class="wildlife-circle circle-green"></div>
              <strong>Plants</strong>
            </div>

            <div class="wildlife-item">
              <div class="wildlife-circle circle-yellow"></div>
              <strong>Insects</strong>
            </div>

            <div class="wildlife-item">
              <div class="wildlife-circle circle-green"></div>
              <strong>Mammals</strong>
            </div>

            <div class="wildlife-item">
              <div class="wildlife-circle circle-yellow"></div>
              <strong>Reptiles</strong>
            </div>

          </div>

        </div>

        <!-- Vegetation context -->
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