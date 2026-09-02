<template>
  <main>
    <!-- Main introduction area -->
    <!-- I used the real garden photo here as the banner background instead
         of the old text-and-card layout, to match the new homepage design. -->
    <section class="hero-banner">
      <img
        class="hero-banner-image"
        src="../assets/HomePage_background.png"
        alt="A native Australian garden with flowering shrubs and trees"
      />

      <div class="hero-banner-overlay">
        <div>
          <h1 class="hero-wordmark">ReGrove</h1>
          <div class="hero-wordmark-underline"></div>
        </div>
      </div>
    </section>

    <!-- Iteration 1 features -->
    <section class="prototype-section">
      <div class="prototype-heading">
        <!-- Small tree icon next to the heading, matches the design. -->
        <img class="tree-icon" src="../assets/small tree.png" alt="" aria-hidden="true" />

        <div>
          <h2>What the prototype does</h2>
          <p>Iteration 1 focuses on just two simple experiences.</p>
        </div>
      </div>

      <!-- Cards now stack top-to-bottom instead of side by side, with the
           action button sitting inline next to the title instead of at
           the bottom. Explore My Area is first, My Space is second. -->
      <div class="prototype-cards">

        <div class="prototype-card">
          <div class="card-top">
            <div class="card-title">
              <div class="card-number">1</div>

              <div>
                <h3>Explore My Area</h3>
                <strong>Local Biodiversity Context</strong>
              </div>
            </div>

            <RouterLink class="primary-button" to="/explore">
              Explore area
            </RouterLink>
          </div>

          <p>
            Enter your suburb or postcode to see simple, open-data-backed
            information about biodiversity records and local vegetation.
          </p>
        </div>

        <div class="prototype-card">
          <div class="card-top">
            <div class="card-title">
              <div class="card-number">2</div>

              <div>
                <h3>My Space</h3>
                <strong>Property Assessment</strong>
              </div>
            </div>

            <RouterLink class="primary-button" to="/assessment">
              Start assessment
            </RouterLink>
          </div>

          <p>
            Answer a few simple questions about your outdoor space
            and save a basic profile for your next visit.
          </p>
        </div>

      </div>
    </section>

    <section class="data-source-section">
        <strong>Built from open data</strong>

        <p>
            Atlas of Living Australia • Victorian Ecological Vegetation Classes • AusTraits
        </p>
        </section>
  </main>
</template>