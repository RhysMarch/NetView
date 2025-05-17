<template>
  <div class="w-full h-full">
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
      class="space-y-4"
    >
      <template #item="{ element }">
        <SidebarBlock :title="element.title">
          <div class="flex flex-col">
            <!-- main line -->
            <div
              class="flex items-center justify-between cursor-move"
              @click="element.key === 'alerts' && toggleAlerts()"
            >
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
                <template v-else-if="element.key === 'alerts'">
                  <span :class="alertClass">{{ stats.active_alerts }}</span>
                  <span class="ml-1 text-xs text-gray-500">
                    (click to {{ showAlerts ? 'hide' : 'show' }})
                  </span>
                </template>
              </div>
            </div>

            <!-- Inline alerts list, capped smaller with scroll -->
            <ul
              v-if="element.key === 'alerts' && showAlerts"
              class="mt-2 ml-4 list-disc text-sm space-y-1 overflow-y-auto max-h-32"
            >
              <li v-for="a in alerts" :key="a.id">
                {{ a.message }}
                <span class="text-xs text-gray-400">
                  ({{ formatTimestamp(a.timestamp) }})
                </span>
              </li>
              <li v-if="alerts.length === 0" class="text-gray-500">
                No alerts
              </li>
            </ul>
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
const showAlerts = ref(false)

const blocks = ref([
  { key: 'health', title: 'Network Health' },
  { key: 'total',  title: 'Total Devices' },
  { key: 'online', title: 'Currently Online' },
  { key: 'latency',title: 'Average Latency' },
  { key: 'alerts', title: 'Active Alerts' },
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

function toggleAlerts() {
  showAlerts.value = !showAlerts.value
  if (showAlerts.value) fetchAlerts()
}

function startCountdown() {
  tickTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
}

onMounted(() => {
  fetchStats(true)
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

const alertClass = computed(() => {
  const a = stats.value.active_alerts || 0
  const t = stats.value.current_online_devices || 1
  if (a === 0) return 'text-green-600'
  const ratio = a / t
  if (ratio > 0.5 || a >= 10) return 'text-red-600'
  if (ratio > 0.2 || a >= 3)  return 'text-amber-500'
  return 'text-yellow-600'
})

// helper to format ISO timestamp strings nicely
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
