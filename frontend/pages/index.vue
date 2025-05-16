<template>
  <div class="min-h-screen bg-gradient-to-r from-zinc-200 via-white to-zinc-200 flex flex-col">
    <!-- Container with border and neutral background -->
    <div class="bg-white border-l border-r border-slate-300 shadow-lg w-full max-w-7xl p-6 mx-auto flex-1 flex flex-col">
      <FilterBar />

      <!-- Main content area -->
      <div class="flex flex-1 mt-6 gap-4">
        <!-- Main Network View -->
        <div class="w-4/5">
          <NetworkTopology />
        </div>

        <!-- Sidebar -->
        <div class="w-1/5">
          <Sidebar />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import FilterBar from '~/components/FilterBar.vue'
import NetworkTopology from '~/components/NetworkMap.vue'
import Sidebar from '~/components/Sidebar.vue'
</script>
