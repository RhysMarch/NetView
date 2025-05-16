<template>
  <div class="w-full">
    <input
      v-model="search"
      type="text"
      placeholder="Filtering"
      class="w-full px-4 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
    />
  </div>
</template>

<script setup>
const search = ref('');
</script>
