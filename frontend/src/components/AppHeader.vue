<template>
  <header class="app-header">
    <div class="header-inner">

      <RouterLink class="brand" to="/">
        <img class="brand-logo" src="../assets/ReGrove_icon.png" alt="ReGrove logo" />
      </RouterLink>

      <nav class="main-nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/assessment">My Space</RouterLink>
        <RouterLink to="/explore">Explore Area</RouterLink>

        <RouterLink class="get-started" to="/assessment">
          Get Started
        </RouterLink>
      </nav>

    </div>
  </header>
</template>