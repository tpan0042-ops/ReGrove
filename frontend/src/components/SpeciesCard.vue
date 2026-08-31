<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  tag: {
    type: String,
    required: true
  },
  imageAlt: {
    type: String,
    default: 'Garden image'
  }
})
</script>

<template>
  <div class="species-card">
    <div class="species-card-image">
      {{ imageAlt }}
    </div>

    <h3>{{ title }}</h3>
    <p>{{ description }}</p>

    <span class="species-tag">{{ tag }}</span>
  </div>
</template>