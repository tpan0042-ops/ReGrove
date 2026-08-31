<script setup>
import AppSidebar from '../components/AppSidebar.vue'
import SpeciesCard from '../components/SpeciesCard.vue'
</script>

<template>
  <div class="page-layout">

    <AppSidebar />

    <main class="page-content">

      <div class="planting-heading">
        <div class="planting-heading-text">
          <h1>Planting ideas for your space</h1>
          <p>Simple examples of how future recommendations could be presented.</p>
        </div>

        <div class="planting-heading-image">
          Garden image
        </div>
      </div>

      <div class="planting-section-intro">
        <h2>For a beginner-friendly backyard</h2>
        <p>These are UI examples only — final suggestions will depend on validated local data.</p>
      </div>

      <div class="species-card-row">
        <SpeciesCard
          title="Native flowering plants"
          description="Flowers that can provide resources for pollinators."
          tag="Pollinators"
        />

        <SpeciesCard
          title="Shrubs & shelter"
          description="Plants that can add structure and potential habitat."
          tag="Shelter"
        />

        <SpeciesCard
          title="Ground cover"
          description="Lower-growing plants for filling smaller spaces."
          tag="Small spaces"
        />
      </div>

      <div class="future-feature-banner">
        <strong>Future feature</strong>
        <p>Recommendations can later include maintenance, space suitability and approximate cost once those data sources are validated.</p>
      </div>

    </main>

  </div>
</template>