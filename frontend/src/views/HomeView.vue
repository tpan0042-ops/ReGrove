<template>
  <main class="home-page">
    <!-- Main banner -->
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

    <!-- Prototype features -->
    <section class="prototype-section">
      <div class="prototype-heading">
        <img
          class="tree-icon"
          src="../assets/small tree.png"
          alt=""
          aria-hidden="true"
        />

        <div>
          <h2>What the prototype does</h2>
          <p>Iteration 1 focuses on just two simple experiences.</p>
        </div>
      </div>

      <!-- Two feature cards -->
      <div class="prototype-cards">
        <!-- Explore My Area -->
        <div class="prototype-card">
          <div class="card-title">
            <div class="card-number">1</div>

            <div class="card-heading-text">
              <h3>Explore My Area</h3>
              <strong>Local Biodiversity Context</strong>
            </div>
          </div>

          <p class="card-description">
            Enter your suburb or postcode to see simple,
            open-data-backed information about biodiversity records
            and local vegetation.
          </p>

          <RouterLink class="primary-button" to="/explore">
            Explore area
          </RouterLink>
        </div>

        <!-- My Space -->
        <div class="prototype-card">
          <div class="card-title">
            <div class="card-number">2</div>

            <div class="card-heading-text">
              <h3>My Space</h3>
              <strong>Property Assessment</strong>
            </div>
          </div>

          <p class="card-description">
            Answer a few simple questions about your outdoor space
            and save a basic profile for your next visit.
          </p>

          <RouterLink class="primary-button" to="/assessment">
            Start assessment
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Data source -->
    <section class="data-source-section">
      <strong>Built from open data</strong>

      <p>
        Atlas of Living Australia • Victorian Ecological Vegetation Classes •
        AusTraits
      </p>
    </section>
  </main>
</template>

<style scoped>
/* Whole homepage */
.home-page {
  background-color: #f6f3e8;
}


/* =========================
   Hero banner
   ========================= */

.hero-banner {
  position: relative;
  width: 100%;
  height: 310px;
  overflow: hidden;
}

.hero-banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-banner-overlay {
  position: absolute;
  inset: 0;

  display: flex;
  align-items: center;

  padding: 0 7%;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.35),
    rgba(0, 0, 0, 0.05)
  );
}

.hero-wordmark {
  margin: 0;

  color: white;
  font-size: clamp(3rem, 6vw, 5.5rem);
  font-weight: 700;
  letter-spacing: -2px;
}

.hero-wordmark-underline {
  width: 145px;
  height: 5px;
  margin-top: 8px;

  background-color: white;
  border-radius: 10px;
}


/* =========================
   Prototype section
   ========================= */

.prototype-section {
  width: min(1120px, 90%);
  margin: 0 auto;
  padding: 38px 0 30px;
}

.prototype-heading {
  display: flex;
  align-items: center;
  gap: 20px;

  margin-bottom: 30px;
}

.tree-icon {
  width: 62px;
  height: 62px;
  object-fit: contain;
  flex-shrink: 0;
}

.prototype-heading h2 {
  margin: 0 0 4px;

  color: #256333;
  font-size: 2rem;
  font-weight: 700;
}

.prototype-heading p {
  margin: 0;

  color: #687361;
  font-size: 1rem;
}


/* =========================
   Feature cards
   ========================= */

.prototype-cards {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.prototype-card {
  display: grid;
  grid-template-columns: 260px 1fr auto;
  align-items: center;
  gap: 30px;

  width: 100%;
  min-height: 145px;
  padding: 25px 30px;

  background-color: white;
  border: 1px solid #dddcd4;
  border-radius: 16px;

  box-sizing: border-box;

  box-shadow: 0 2px 10px rgba(50, 75, 45, 0.05);

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.prototype-card:hover {
  transform: translateY(-2px);

  box-shadow: 0 8px 20px rgba(50, 75, 45, 0.08);
}


/* Card title area */
.card-title {
  display: flex;
  align-items: center;
  gap: 18px;
}

.card-number {
  display: flex;
  align-items: center;
  justify-content: center;

  width: 54px;
  height: 54px;

  flex-shrink: 0;

  background-color: #e4f0d6;
  border-radius: 12px;

  color: #28652f;
  font-size: 1.4rem;
  font-weight: 700;
}

.card-heading-text h3 {
  margin: 0 0 5px;

  color: #1f6533;
  font-size: 1.35rem;
  font-weight: 700;
}

.card-heading-text strong {
  color: #61705b;
  font-size: 0.9rem;
  font-weight: 600;
}


/* Card description */
.card-description {
  margin: 0;

  color: #5d6858;
  font-size: 0.97rem;
  line-height: 1.55;
}


/* Card button */
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  width: 178px;
  padding: 15px 20px;

  justify-self: end;
  white-space: nowrap;

  background-color: #246737;
  border-radius: 9px;
  box-shadow: 0 3px 8px rgba(36, 103, 55, 0.25);

  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  text-decoration: none;

  transition:
    background-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.primary-button:hover {
  background-color: #194f29;
  transform: translateY(-1px);
  box-shadow: 0 5px 12px rgba(36, 103, 55, 0.3);
}


/* =========================
   Data source
   ========================= */

.data-source-section {
  display: flex;
  align-items: center;
  gap: 45px;

  width: min(1120px, 90%);
  margin: 0 auto 35px;
  padding: 17px 25px;

  box-sizing: border-box;

  background-color: #f0f4e7;
  border-radius: 10px;
}

.data-source-section strong {
  color: #246333;
  white-space: nowrap;
}

.data-source-section p {
  margin: 0;

  color: #687361;
  font-size: 0.92rem;
}


/* =========================
   Responsive layout
   ========================= */

@media (max-width: 850px) {
  .prototype-card {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .primary-button {
    width: auto;
    min-width: 178px;
    justify-self: start;
  }
}

@media (max-width: 600px) {
  .hero-banner {
    height: 230px;
  }

  .prototype-section {
    width: 92%;
    padding-top: 28px;
  }

  .prototype-heading {
    align-items: flex-start;
  }

  .tree-icon {
    width: 50px;
    height: 50px;
  }

  .prototype-heading h2 {
    font-size: 1.55rem;
  }

  .prototype-card {
    padding: 22px;
  }

  .data-source-section {
    width: 92%;

    flex-direction: column;
    align-items: flex-start;
    gap: 7px;
  }
}
</style>