<template>
  <header class="app-header">
    <div class="header-inner">

      <!-- Use the real logo image here instead of plain text. -->
      <RouterLink class="brand" to="/">
        <img class="brand-logo" src="../assets/ReGrove_icon.png" alt="ReGrove logo" />
      </RouterLink>

      <nav class="main-nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/explore">Explore Area</RouterLink>
        <RouterLink to="/assessment">My Space</RouterLink>
        <RouterLink to="/about">About</RouterLink>

        <RouterLink class="get-started" to="/assessment">
          Get Started
        </RouterLink>
      </nav>

    </div>
  </header>
</template>