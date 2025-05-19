<!-- components/FilterBar.vue -->
<template>
  <div class="relative w-full">
    <input
      v-model="search"
      type="text"
      placeholder="Filter by IP, MAC, Name, Vendor, Online or Offline."
      class="w-full pr-8 px-4 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
    />
    <button
      v-if="search"
      @click="clear"
      type="button"
      aria-label="Clear filter"
      class="absolute inset-y-0 right-2 flex items-center text-gray-400 hover:text-gray-600"
    >
      <!-- X icon -->
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" clip-rule="evenodd"
          d="M10 8.586l4.95-4.95a1 1 0 011.414 1.414L11.414 10l4.95 4.95a1 1 0 01-1.414 1.414L10 11.414l-4.95 4.95a1 1 0 01-1.414-1.414L8.586 10l-4.95-4.95a1 1 0 011.414-1.414L10 8.586z"
        />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const search = ref(props.modelValue)

// emit up when user types or clears
watch(search, v => emit('update:modelValue', v))
// keep local in sync if parent resets
watch(() => props.modelValue, v => search.value = v)

function clear() {
  search.value = ''
}
</script>
