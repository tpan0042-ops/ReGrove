<script setup>
defineProps({
  suburb: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="context-notice">
    <strong>Area-level data</strong>
    <p>
      This information reflects biodiversity records for {{ suburb }} as a
      whole, not a measurement of your individual property.
    </p>
  </div>
</template>