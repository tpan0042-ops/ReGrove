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

    </main>

  </div>
</template>