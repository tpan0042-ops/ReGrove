<script setup>
// This page presents the current Planting Ideas interface with native plant examples.
// It currently focuses on the page layout and will support more dynamic recommendations later.

import { useRouter } from 'vue-router'

const router = useRouter()

// Send the user to the Local Insight page for a specific area.
// There is no shared "last searched area" state yet, so this uses the
// same Clayton 3168 example already shown elsewhere in the app (Explore
// Area's popular searches, and the Local Insight mockup).
const goToLocalInsight = () => {
  router.push('/area/3168')
}

// Send the user on to My Plan, which will combine this page's plant
// choices with the user's My Space profile.
const goToMyPlan = () => {
  router.push('/plan')
}
</script>

<template>
  <!-- This page does not use AppSidebar anymore, same as the other pages
       that now show a full background photo. Reusing the same photo as
       the area result page, since it matches this page's design too. -->
  <section class="planting-page">
    <img
      class="planting-page-image"
      src="../assets/postcode_ResultPage.png"
      alt="A meadow of native wildflowers"
    />

    <!-- Same light tint layer as the other full-photo pages. -->
    <div class="planting-page-tint"></div>

    <div class="planting-page-overlay">

      <!-- Introduce the Planting Ideas page and its purpose. -->
      <div class="planting-top">

        <div class="planting-heading">
          <h1>Planting Ideas</h1>
          <h3>Native plants for your space</h3>

          <p>
            Planting ideas based on local biodiversity needs and your space.
          </p>
        </div>

        <!-- Move on to the Local Insight page for this area. -->
        <button
          type="button"
          class="next-button"
          @click="goToLocalInsight"
        >
          See local insight →
        </button>

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

        <button
          type="button"
          @click="goToMyPlan"
        >
          Create my plan
        </button>

      </div>

      <!-- "Your impact" used to live in the sidebar. Show it here now
           since this page does not have a sidebar anymore. -->
      <div class="impact-box floating-impact">
        <strong>Your impact</strong>
        <h3>0</h3>
        <p>Actions completed</p>
        <p>Prototype</p>
      </div>

    </div>
  </section>
</template>