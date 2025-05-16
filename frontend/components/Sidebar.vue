<!-- Sidebar.vue -->
<template>
  <div class="w-full h-full space-y-4">
    <!-- Error banner -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl" role="alert">
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <!-- Initial loader -->
    <div v-if="loading" class="bg-white border border-slate-300 rounded-xl shadow p-4 w-full">
      <p class="text-gray-500">Loading statistics...</p>
    </div>

    <!-- Stats & countdown -->
    <template v-else>
      <SidebarBlock title="Network Health">
        <span :class="healthClass">{{ stats.network_health }}</span>
      </SidebarBlock>
      <SidebarBlock title="Total Devices">
        {{ stats.total_devices }}
      </SidebarBlock>
      <SidebarBlock title="Currently Online">
        {{ stats.current_online_devices }}
      </SidebarBlock>
      <SidebarBlock title="Average Latency">
        <span :class="latencyClass">{{ stats.average_latency }}</span>
      </SidebarBlock>
      <SidebarBlock title="Active Alerts">
        <span :class="alertClass">{{ stats.active_alerts }}</span>
      </SidebarBlock>
      <SidebarBlock title="Next Update">
        {{ countdown }}s
      </SidebarBlock>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import SidebarBlock from '~/components/SidebarBlock.vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// reactive state
const stats    = ref({})
const loading  = ref(true)
const error    = ref(null)
const countdown = ref(0)

// timers
let refreshTimer = null
let tickTimer    = null

async function fetchStats(showLoading = false) {
  if (showLoading) loading.value = true
  error.value = null

  try {
    const res = await fetch(`${API}/api/stats`)
    if (!res.ok) throw new Error(res.statusText)
    stats.value = await res.json()
  } catch (e) {
    error.value = `Failed to fetch network statistics: ${e.message}`
  } finally {
    if (showLoading) loading.value = false

    // parse next_update ("10s") into seconds
    const secs = parseInt(stats.value.next_update) || 10
    countdown.value = secs

    // schedule next silent refresh
    clearTimeout(refreshTimer)
    refreshTimer = setTimeout(() => fetchStats(false), secs * 1000)
  }
}

function startCountdown() {
  tickTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
}

onMounted(() => {
  // initial load shows loader
  fetchStats(true)
  // start the 1s countdown ticker
  startCountdown()
})

onUnmounted(() => {
  clearTimeout(refreshTimer)
  clearInterval(tickTimer)
})

// computed CSS classes
const healthClass = computed(() => {
  switch (stats.value.network_health) {
    case 'Excellent': return 'text-green-600'
    case 'Good':      return 'text-yellow-500'
    case 'Fair':      return 'text-amber-600'
    case 'Poor':      return 'text-red-600'
    default:          return 'text-gray-500'
  }
})

const latencyClass = computed(() => {
  const l = stats.value.average_latency
  if (!l || l === 'timeout') return 'text-red-600'
  const v = parseInt(l)
  if (v <= 50)   return 'text-green-600'
  if (v <= 100)  return 'text-yellow-500'
  if (v <= 200)  return 'text-amber-600'
  return 'text-red-600'
})

const alertClass = computed(() => {
  const a = stats.value.active_alerts || 0
  const t = stats.value.current_online_devices || 1
  if (a === 0) return 'text-green-600'
  const ratio = a / t
  if (ratio > 0.5 || a >= 10) return 'text-red-600'
  if (ratio > 0.2 || a >= 3)  return 'text-amber-500'
  return 'text-yellow-600'
})
</script>
