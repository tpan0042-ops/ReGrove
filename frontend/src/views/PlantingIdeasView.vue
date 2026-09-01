<script setup>
// This page presents the current Planting Ideas interface with native plant examples.
// It currently focuses on the page layout and will support more dynamic recommendations later.

import AppSidebar from '../components/AppSidebar.vue'
</script>

<template>
  <div class="page-layout">

    <!-- Reuse the main sidebar for navigation. -->
    <AppSidebar />

    <main class="page-content">

      <!-- Introduce the Planting Ideas page and its purpose. -->
      <div class="planting-top">

        <div class="planting-heading">
          <h1>Planting Ideas</h1>
          <h3>Native plants for your space</h3>

          <p>
            Planting ideas based on local biodiversity needs and your space.
          </p>
        </div>

        <!-- Decorative banner area used in the current page design. -->
        <div class="planting-banner"></div>

      </div>

      <!-- Show the plant categories available in the current interface. -->
      <div class="plant-filters">
        <button class="filter-active">All plants</button>
        <button>Flowering plants</button>
        <button>Shrubs & small trees</button>
        <button>Groundcovers</button>
      </div>

      <!-- Display example plant cards in the current prototype. -->
      <div class="plant-cards">

        <!-- Common Correa plant card. -->
        <div class="plant-card">
          <div class="plant-card-image green-image"></div>

          <div class="plant-card-content">
            <h3>Common Correa</h3>
            <p class="plant-type">Flowering shrub</p>

            <span class="plant-tag">Native</span>

            <p class="plant-info">
              Supports recommendation<br>
              Local suitability checked<br>
              Habitat impact data
            </p>
          </div>
        </div>

        <!-- Golden Wattle plant card. -->
        <div class="plant-card">
          <div class="plant-card-image green-image"></div>

          <div class="plant-card-content">
            <h3>Golden Wattle</h3>
            <p class="plant-type">Small native tree</p>

            <span class="plant-tag">Native</span>

            <p class="plant-info">
              Supports recommendation<br>
              Local suitability checked<br>
              Habitat impact data
            </p>
          </div>
        </div>

        <!-- Bottlebrush plant card. -->
        <div class="plant-card">
          <div class="plant-card-image pink-image"></div>

          <div class="plant-card-content">
            <h3>Bottlebrush</h3>
            <p class="plant-type">Pollinator friendly</p>

            <span class="plant-tag">Native</span>

            <p class="plant-info">
              Supports recommendation<br>
              Local suitability checked<br>
              Habitat impact data
            </p>
          </div>
        </div>

        <!-- Lomandra plant card. -->
        <div class="plant-card">
          <div class="plant-card-image green-image"></div>

          <div class="plant-card-content">
            <h3>Lomandra</h3>
            <p class="plant-type">Low maintenance grass</p>

            <span class="plant-tag">Easy care</span>

            <p class="plant-info">
              Supports recommendation<br>
              Local suitability checked<br>
              Habitat impact data
            </p>
          </div>
        </div>

      </div>

      <!-- Encourage users to complete My Space before getting more personalised guidance. -->
      <div class="planting-action">

        <div>
          <h3>Not sure where to start?</h3>
          <p>
            Complete My Space to see recommendations around your outdoor area.
          </p>
        </div>

        <!-- I think this action will be more useful once it is connected to the planning flow. -->
        <button type="button">
          Create my plan
        </button>

      </div>

    </main>

  </div>
</template>