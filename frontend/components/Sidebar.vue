<!-- Sidebar.vue -->
<template>
  <div class="w-full h-full space-y-4">
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl" role="alert">
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <div v-if="loading" class="bg-white border border-slate-300 rounded-xl shadow p-4 w-full">
      <p class="text-gray-500">Loading statistics...</p>
    </div>

    <template v-else>
      <SidebarBlock title="Network Health">
        <span :class="healthClass">{{ stats.network_health }}</span>
      </SidebarBlock>
      <SidebarBlock title="Total Devices">
        {{ stats.total_devices}}
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
import { onMounted, onUnmounted, ref, computed } from 'vue'
import SidebarBlock from '~/components/SidebarBlock.vue'

const SYNC_INTERVAL = 10000  // 10 seconds

const stats    = ref({})
const loading  = ref(true)
const error    = ref(null)
const countdown = ref(SYNC_INTERVAL / 1000)
let intervalId, countdownId

const fetchStats = async (showLoading = false) => {
  try {
    if (showLoading) loading.value = true
    error.value = null
    const res = await fetch('http://localhost:8000/api/stats')
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
    stats.value = await res.json()
  } catch (e) {
    error.value = `Failed to fetch network statistics: ${e.message}`
    console.error(e)
  } finally {
    if (showLoading) loading.value = false
    countdown.value = SYNC_INTERVAL / 1000
  }
}

const healthClass = computed(() => {
  switch (stats.value.network_health) {
    case "Excellent": return "text-green-600"
    case "Good":      return "text-yellow-500"
    case "Fair":      return "text-amber-600"
    case "Poor":      return "text-red-600"
    default:          return "text-gray-500"
  }
})

const latencyClass = computed(() => {
  const l = stats.value.average_latency
  if (!l || l === "timeout") return "text-red-600"
  const v = parseInt(l)
  if (v <= 50)  return "text-green-600"
  if (v <= 100) return "text-yellow-500"
  if (v <= 200) return "text-amber-600"
  return "text-red-600"
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

onMounted(() => {
  fetchStats(true)
  intervalId   = setInterval(() => fetchStats(false), SYNC_INTERVAL)
  countdownId  = setInterval(() => {
    if (countdown.value > 0) countdown.value--
    else countdown.value = SYNC_INTERVAL / 1000
  }, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
  clearInterval(countdownId)
})
</script>