<template>
  <main>
    <!-- Main introduction area -->
    <section class="hero-section">
      <div class="hero-text">
        <h1>Plant local. Help local wildlife.</h1>

        <h2>
          Simple biodiversity guidance for the outdoor space you control.
        </h2>

        <p>
          Tell us about your garden, balcony or courtyard, then explore what
          biodiversity information is available around your local area.
        </p>

        <div class="hero-buttons">
          <RouterLink class="primary-button" to="/assessment">
            Assess My Space
          </RouterLink>

          <RouterLink class="secondary-button" to="/explore">
            Explore My Area
          </RouterLink>
        </div>
      </div>

      <div class="hero-card">
        <h2>Your space can make<br>a difference.</h2>

        <div class="hero-card-small">
          <p>Start small</p>
          <strong>Learn what works locally.</strong>
        </div>
      </div>
    </section>

    <!-- Iteration 1 features -->
    <section class="prototype-section">
      <h2>What the prototype does</h2>
      <p>Iteration 1 focuses on just two simple experiences.</p>

      <div class="prototype-cards">

        <div class="prototype-card">
          <div class="card-title">
            <div class="card-number">1</div>

            <div>
              <h3>My Space</h3>
              <strong>Property Assessment</strong>
            </div>
          </div>

          <p>
            Answer a few simple questions about your outdoor space and
            understand its current features.
          </p>

          <RouterLink class="primary-button" to="/assessment">
            Start assessment
          </RouterLink>
        </div>

        <div class="prototype-card">
          <div class="card-title">
            <div class="card-number">2</div>

            <div>
              <h3>Explore My Area</h3>
              <strong>Local Biodiversity Context</strong>
            </div>
          </div>

          <p>
            Enter your suburb or postcode to see simple, open-data-backed
            information about biodiversity records and local vegetation.
          </p>

          <RouterLink class="primary-button" to="/explore">
            Explore area
          </RouterLink>
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