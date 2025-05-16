<!-- SidebarBlock.vue -->
<template>
  <div class="bg-white border border-slate-300 rounded-xl shadow p-4 w-full">
    <h2 class="font-semibold">
      {{ title }}: <slot />
    </h2>
  </div>
</template>

<script setup>
defineProps({
  title: String
})
</script>
