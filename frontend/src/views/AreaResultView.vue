<script setup>
import AppSidebar from '../components/AppSidebar.vue'
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <div class="area-result-heading">
        <h1>Clayton 3168</h1>
        <h3>Local biodiversity snapshot</h3>
        <p>
          Explore local species records, vegetation context and available data.
        </p>
      </div>

      <section class="area-summary">

        <div class="summary-item">
          <span>Species records</span>
          <strong>Available</strong>
        </div>

        <div class="summary-item">
          <span>Vegetation context</span>
          <strong>Available</strong>
        </div>

        <div class="summary-item">
          <span>Data confidence</span>
          <strong>To assess</strong>
        </div>

        <div class="summary-item">
          <span>Local opportunities</span>
          <strong>To assess</strong>
        </div>

      </section>

      <section class="result-details">

        <div class="wildlife-card">
            <h2>What lives here?</h2>

            <div class="wildlife-groups">

            <div class="wildlife-item">
                <div class="wildlife-circle circle-yellow"></div>
                <strong>Birds</strong>
            </div>

            <div class="wildlife-item">
                <div class="wildlife-circle circle-light-yellow"></div>
                <strong>Pollinators</strong>
            </div>

            <div class="wildlife-item">
                <div class="wildlife-circle circle-green"></div>
                <strong>Frogs</strong>
            </div>

            <div class="wildlife-item">
                <div class="wildlife-circle circle-gold"></div>
                <strong>Other wildlife</strong>
            </div>

            </div>
        </div>

        </section>

    </main>

  </div>
</template>