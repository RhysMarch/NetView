<!-- pages/index.vue -->
<template>
  <div class="min-h-screen bg-gradient-to-r from-zinc-200 via-white to-zinc-200 flex flex-col">
    <div class="bg-white border-l border-r border-slate-300 shadow-lg w-full max-w-7xl p-6 mx-auto flex-1 flex flex-col">
      <FilterBar v-model="search" />

      <div class="flex flex-1 mt-6 gap-4">
        <div class="w-4/5">
          <NetworkTopology :filter="search" />
        </div>
        <div class="w-1/5">
          <Sidebar :filter="search" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FilterBar from '~/components/FilterBar.vue'
import NetworkTopology from '~/components/NetworkMap.vue'
import Sidebar from '~/components/Sidebar.vue'

const search = ref('')
</script>
