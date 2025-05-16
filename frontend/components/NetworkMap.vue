<!-- NetworkMap.vue -->
<template>
  <div class="relative h-full">
    <!-- Graph container -->
    <div
      class="bg-white rounded-xl border border-gray-300 shadow h-full"
      ref="graphContainer"
    ></div>

    <!-- Node detail panel -->
    <div
      v-if="selectedNode"
      class="absolute top-4 right-4 bg-white border border-gray-300 rounded-xl shadow p-4 w-64"
    >
      <!-- Editable title -->
      <div class="flex items-center mb-2">
        <template v-if="editing">
          <input
            v-model="newName"
            class="border border-gray-300 rounded p-1 flex-1 mr-2 text-sm"
            placeholder="Enter name"
          />
          <button
            class="px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            @click="saveName"
            :disabled="saving"
          >
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
          <button
            class="ml-1 px-2 py-1 bg-gray-200 rounded text-sm hover:bg-gray-300"
            @click="cancelEdit"
            :disabled="saving"
          >
            Cancel
          </button>
        </template>
        <template v-else>
          <div class="flex items-center">
            <span class="font-semibold text-lg">{{ selectedNode.label }}</span>
            <button
              class="ml-1 text-black hover:text-gray-700"
              @click="startEdit"
              title="Rename"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="black" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 20h9M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </button>
          </div>
        </template>
      </div>

      <!-- Device details -->
      <p class="text-sm"><strong>IP:</strong> {{ selectedNode.id }}</p>
      <p class="mt-1 text-sm">
        <strong>Status: </strong>
        <span :class="selectedNode.online ? 'text-green-600' : 'text-red-600'">
          {{ selectedNode.online ? 'Online' : 'Offline' }}
        </span>
      </p>
      <p class="mt-1 text-sm"><strong>MAC:</strong> {{ selectedNode.mac || 'Unknown' }}</p>

      <!-- Close button -->
      <button
        class="mt-4 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
        @click="closePanel"
      >
        Close
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
let timerId
const positions = new Map()
let simulation

const graphContainer = ref(null)
const selectedNode = ref(null)

const editing = ref(false)
const newName = ref('')
const saving = ref(false)

async function fetchTopology() {
  const res = await fetch(`${API}/api/topology`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

function renderGraph({ nodes, links }) {
  const container = graphContainer.value
  d3.select(container).selectAll('svg').remove()

  const width = container.clientWidth
  const height = container.clientHeight

  nodes.forEach(node => {
    const prev = positions.get(node.id)
    if (prev) {
      node.x = prev.x
      node.y = prev.y
    }
  })

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(200))
    .force('charge', d3.forceManyBody().strength(-800))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(25))
    .on('tick', onTick)

  svg.append('g')
    .attr('stroke', '#ccc')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke-width', 2)

  svg.append('g')
    .attr('stroke', '#fff')
    .selectAll('circle')
    .data(nodes, d => d.id)
    .join('circle')
      .attr('r', 12)
      .attr('fill', d => (d.online ? '#007bff' : '#dc2626'))
      .style('cursor', 'pointer')
      .on('click', (_, d) => {
        selectedNode.value = d
        editing.value = false
        newName.value = d.label
      })
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      )

  svg.append('g')
    .selectAll('text')
    .data(nodes, d => d.id)
    .join('text')
    .text(d => d.label)
    .attr('font-size', '0.8rem')
    .attr('fill', '#333')

  function onTick() {
    svg.selectAll('line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    svg.selectAll('circle')
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .each(d => positions.set(d.id, { x: d.x, y: d.y }))

    svg.selectAll('text')
      .attr('x', d => d.x + 15)
      .attr('y', d => d.y + 5)
  }

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

async function updateGraph() {
  try {
    const topo = await fetchTopology()
    renderGraph(topo)

    if (selectedNode.value) {
      const fresh = topo.nodes.find(n => n.id === selectedNode.value.id)
      if (fresh) {
        selectedNode.value = fresh
        if (!editing.value) newName.value = fresh.label
      } else {
        selectedNode.value = null
      }
    }
  } catch (e) {
    console.error('Failed to fetch topology:', e)
  } finally {
    clearTimeout(timerId)
    timerId = setTimeout(updateGraph, 10000)
  }
}

function startEdit() {
  editing.value = true
}
function cancelEdit() {
  editing.value = false
  newName.value = selectedNode.value.label
}
async function saveName() {
  if (!selectedNode.value) return
  saving.value = true
  try {
    const mac = selectedNode.value.mac
    await fetch(`${API}/api/devices/${encodeURIComponent(mac)}/rename`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.value })
    })
    selectedNode.value.label = newName.value
    editing.value = false
  } catch (err) {
    console.error('Rename failed:', err)
    alert('Failed to rename device')
  } finally {
    saving.value = false
  }
}

function closePanel() {
  selectedNode.value = null
  editing.value = false
}

onMounted(() => {
  updateGraph()
  window.addEventListener('resize', updateGraph)
})
onUnmounted(() => {
  clearTimeout(timerId)
  window.removeEventListener('resize', updateGraph)
})
</script>

<style scoped>
svg {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
