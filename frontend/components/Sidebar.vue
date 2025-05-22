<template>
  <div class="w-full h-full flex flex-col">
    <!-- Error banner -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl mb-4"
      role="alert"
      title="An error occurred while loading stats"
    >
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <!-- Initial loader -->
    <div
      v-if="loading"
      class="bg-white border border-slate-300 rounded-xl shadow p-4 w-full mb-4"
      title="Loading network statistics…"
    >
      <p class="text-gray-500">Loading statistics…</p>
    </div>

    <!-- Draggable stats blocks -->
    <draggable
      v-else
      v-model="blocks"
      item-key="key"
      animation="150"
      class="flex flex-col flex-grow space-y-4 overflow-hidden"
      title="Drag to reorder your dashboard"
    >
      <template #item="{ element }">
        <SidebarBlock
          :title="element.key === 'alerts' ? '' : element.title"
          :class="element.key === 'alerts'
            ? 'flex flex-col flex-grow min-h-0'
            : 'flex-none'"
        >
          <div class="flex flex-col h-full min-h-0">

            <!-- Alerts header -->
            <div
              v-if="element.key === 'alerts'"
              class="flex items-center justify-between mb-4"
            >
              <span class="font-semibold">Alerts</span>
              <svg
                @click="exportAlerts"
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-black cursor-pointer hover:text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                title="Download alerts as a text file"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
              </svg>
            </div>

            <!-- Stats lines -->
            <div
              v-else
              class="flex items-center justify-between cursor-move"
            >
              <div class="flex-1">
                <template v-if="element.key === 'health'">
                  <span
                    :class="healthClass"
                    title="Overall network health (Excellent, Good, Fair, Poor)"
                  >
                    {{ stats.network_health }}
                  </span>
                </template>
                <template v-else-if="element.key === 'total'">
                  <span title="Total number of devices on the network">
                    {{ stats.total_devices }}
                  </span>
                </template>
                <template v-else-if="element.key === 'online'">
                  <span title="Number of devices currently online">
                    {{ stats.current_online_devices }}
                  </span>
                </template>
                <template v-else-if="element.key === 'latency'">
                  <span
                    :class="latencyClass"
                    title="Average network latency in milliseconds"
                  >
                    {{ stats.average_latency }}
                  </span>
                </template>
              </div>
            </div>

            <!-- Alerts list -->
            <template v-if="element.key === 'alerts'">
              <ul
                class="list-none overflow-y-auto max-h-[35vh] pr-6"
                role="list"
                aria-label="Alerts"
                title="List of recent network alerts"
              >
                <li
                  v-for="a in filteredAlerts"
                  :key="a.id"
                  class="flex items-center justify-between border-b border-gray-200 pl-2 py-2"
                  :title="`At ${formatTimestamp(a.timestamp)},: ${a.message}`"
                >
                  <div class="flex-1 pr-2">
                    <p class="text-sm text-gray-800">{{ a.message }}</p>
                    <p class="mt-1 text-xs text-gray-500">{{ formatTimestamp(a.timestamp) }}</p>
                  </div>
                  <div class="flex-shrink-0 flex items-center">
                    <svg
                      v-if="a.type === 'new_device'"
                      class="h-5 w-5 text-green-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                      title="New device joined the network"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    <svg
                      v-else-if="a.type === 'device_back_online'"
                      class="h-5 w-5 text-emerald-500"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      title="Device came back online"
                    >
                      <circle cx="10" cy="10" r="8" />
                    </svg>
                    <svg
                      v-else-if="a.type === 'device_offline'"
                      class="h-5 w-5 text-slate-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      title="Device went offline"
                    >
                      <circle cx="10" cy="10" r="8" />
                    </svg>
                    <svg
                      v-else
                      class="h-5 w-5 text-yellow-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                      title="Warning-level alert"
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
                  v-if="filteredAlerts.length === 0"
                  class="py-2 text-center text-gray-500"
                  title="No alerts to show"
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

const API    = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const stats  = ref({})
const alerts = ref([])
const loading= ref(true)
const error  = ref(null)
const countdown = ref(0)

const props = defineProps({
  filter: { type: String, default: '' }
})

const blocks = ref([
  { key: 'health', title: 'Network Health' },
  { key: 'total',  title: 'Total Devices' },
  { key: 'online', title: 'Currently Online' },
  { key: 'latency',title: 'Average Latency' },
  { key: 'alerts', title: 'Alerts' }
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

const filteredAlerts = computed(() => {
  if (!props.filter) return alerts.value
  const f = props.filter.toLowerCase()
  return alerts.value.filter(a =>
    a.mac.toLowerCase().includes(f) ||
    a.ip.toLowerCase().includes(f) ||
    a.message.toLowerCase().includes(f)
  )
})

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

function exportAlerts() {
  const lines = filteredAlerts.value.map(a => {
    const time = new Date(a.timestamp).toLocaleString()
    return `${time} — ${a.message}`
  })
  const blob = new Blob([lines.join("\n")], { type: "text/plain" })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `alerts_${new Date().toISOString()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

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
