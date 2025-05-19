<!-- components/FilterBar.vue -->
<template>
  <div class="w-full">
    <input
      v-model="search"
      type="text"
      placeholder="Filter by IP, MAC, Name, Vendor, Online or Offline"
      class="w-full px-4 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const search = ref(props.modelValue)

watch(search, (val) => {
  emit('update:modelValue', val)
})

watch(() => props.modelValue, (val) => {
  search.value = val
})
</script>
