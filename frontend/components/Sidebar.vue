<template>
  <div class="w-full h-full flex flex-col">
    <!-- Error banner -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl mb-4"
      role="alert"
    >
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <!-- Initial loader -->
    <div
      v-if="loading"
      class="bg-white border border-slate-300 rounded-xl shadow p-4 w-full mb-4"
    >
      <p class="text-gray-500">Loading statistics...</p>
    </div>

    <!-- Draggable stats blocks -->
    <draggable
      v-else
      v-model="blocks"
      item-key="key"
      animation="150"
      class="flex flex-col flex-grow space-y-4 overflow-hidden"
    >
      <template #item="{ element }">
        <SidebarBlock
          :title="element.title"
          :class="element.key === 'alerts'
            ? 'flex flex-col flex-grow min-h-0'
            : 'flex-none'"
        >
          <div class="flex flex-col h-full min-h-0">
            <!-- main line -->
            <div class="flex items-center justify-between cursor-move">
              <div class="flex-1">
                <template v-if="element.key === 'health'">
                  <span :class="healthClass">{{ stats.network_health }}</span>
                </template>
                <template v-else-if="element.key === 'total'">
                  {{ stats.total_devices }}
                </template>
                <template v-else-if="element.key === 'online'">
                  {{ stats.current_online_devices }}
                </template>
                <template v-else-if="element.key === 'latency'">
                  <span :class="latencyClass">{{ stats.average_latency }}</span>
                </template>
              </div>
            </div>

            <!-- Always-visible alerts list with scroll -->
            <template v-if="element.key === 'alerts'">
              <ul
                class="list-none overflow-y-auto max-h-[35vh] pr-6"
                role="list"
                aria-label="Active alerts"
              >
                <li
                  v-for="a in alerts"
                  :key="a.id"
                  class="flex items-center justify-between py-2"
                >
                  <!-- left: message + timestamp -->
                  <div class="flex-1 pr-2">
                    <p class="text-sm text-gray-800">
                      {{ a.message }}
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                      {{ formatTimestamp(a.timestamp) }}
                    </p>
                  </div>

                  <!-- right: icon, vertically centered -->
                  <div class="flex-shrink-0 flex items-center">
                    <!-- brand-new device -->
                    <svg
                      v-if="a.type === 'new_device'"
                      class="h-5 w-5 text-green-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                        clip-rule="evenodd"
                      />
                    </svg>

                   <!-- device back online -->
                    <svg
                      v-else-if="a.type === 'device_back_online'"
                      class="h-5 w-5 text-emerald-500"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <circle cx="10" cy="10" r="8" />
                    </svg>

                    <!-- device went offline -->
                    <svg
                      v-else-if="a.type === 'device_offline'"
                      class="h-5 w-5 text-slate-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <circle cx="10" cy="10" r="8" />
                    </svg>

                    <!-- fallback warning -->
                    <svg
                      v-else
                      class="h-5 w-5 text-yellow-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.516 9.811c.75 1.334-.213 2.99-1.742 2.99H4.483c-1.528 0-2.492-1.656-1.742-2.99L8.257 3.1zM11 12a1 1 0 10-2 0 1 1 0 002 0zm-1-4a1 1 0 00-.993.883L9 9v2a1 1 0 001.993.117L11 11V9a1 1 0 00-1-1z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                </li>

                <li
                  v-if="alerts.length === 0"
                  class="py-2 text-center text-gray-500"
                >
                  No alerts
                </li>
              </ul>
            </template>
          </div>
        </SidebarBlock>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import draggable from 'vuedraggable'
import SidebarBlock from '~/components/SidebarBlock.vue'

const API       = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const stats     = ref({})
const alerts    = ref([])
const loading   = ref(true)
const error     = ref(null)
const countdown = ref(0)

const blocks = ref([
  { key: 'health', title: 'Network Health' },
  { key: 'total',  title: 'Total Devices' },
  { key: 'online', title: 'Currently Online' },
  { key: 'latency',title: 'Average Latency' },
  { key: 'alerts', title: 'Alerts' },
])

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
    const secs = parseInt(stats.value.next_update) || 10
    countdown.value = secs
    clearTimeout(refreshTimer)
    refreshTimer = setTimeout(() => fetchStats(false), secs * 1000)
    fetchAlerts()
  }
}

async function fetchAlerts() {
  try {
    const res = await fetch(`${API}/api/alerts`)
    if (!res.ok) throw new Error(res.statusText)
    alerts.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch alerts:', e)
    alerts.value = []
  }
}

function startCountdown() {
  tickTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
}

onMounted(() => {
  fetchStats(true)
  fetchAlerts()
  startCountdown()
})

onUnmounted(() => {
  clearTimeout(refreshTimer)
  clearInterval(tickTimer)
})

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

// compute real number of alerts
const activeAlertCount = computed(() => alerts.value.length)

// update class logic based on real alert count
const alertClass = computed(() => {
  const a = alerts.value.length
  const t = stats.value.current_online_devices || 1
  if (a === 0) return 'text-green-600'
  const ratio = a / t
  if (ratio > 0.5 || a >= 10) return 'text-red-600'
  if (ratio > 0.2 || a >= 3)  return 'text-amber-500'
  return 'text-yellow-600'
})

function formatTimestamp(ts) {
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}
</script>

<style scoped>
/* keep original styling */
</style>