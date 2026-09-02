<script setup>
// This page shows the local biodiversity results for the postcode selected by the user.
// The species/vegetation summary that used to live here is on hold for this
// iteration - see the "Historical" / "Current" section below instead.

import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// Read the postcode from the current URL.
const postcode = ref(route.params.postcode)
</script>

<template>
  <!-- This page does not use AppSidebar anymore, same as My Space and
       Explore Area. It is now a full background photo with the result
       cards floating on top of it. -->
  <section class="area-result-page">
    <img
      class="area-result-page-image"
      src="../assets/postcode_ResultPage.png"
      alt="A meadow of native wildflowers"
    />

    <!-- Same light tint layer as the other full-photo pages. -->
    <div class="area-result-page-tint"></div>

    <div class="area-result-page-overlay">

      <!-- Show the postcode and introduce the local biodiversity result. -->
      <div class="area-result-heading">

        <RouterLink class="back-area-link" to="/explore">
          Back to Explore Area
        </RouterLink>

        <h1>Postcode {{ postcode }}</h1>

        <h3>Local biodiversity snapshot</h3>

        <p>
          Explore local species records, vegetation context and available data.
        </p>

      </div>

      <!-- Explore Area continued: historical vs current species presence
           for this postcode. Cards are left blank on purpose, this is
           just the layout until that comparison is wired up to real
           data. Next moves on to the My Space assessment. -->
      <section class="species-timeline">

        <h2 class="timeline-heading">Historical</h2>

        <div class="timeline-cards">
          <div
            v-for="n in 4"
            :key="'historical-' + n"
            class="timeline-card"
          ></div>
        </div>

        <h2 class="timeline-heading">Current</h2>

        <div class="timeline-cards">
          <div
            v-for="n in 4"
            :key="'current-' + n"
            class="timeline-card timeline-card-current"
          ></div>
        </div>

        <div class="timeline-actions">
          <RouterLink
            class="next-button"
            to="/assessment"
          >
            Next →
          </RouterLink>
        </div>

      </section>

    </div>
  </section>
</template>
