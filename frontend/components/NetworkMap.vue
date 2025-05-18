<template>
  <div class="relative h-full">
    <!-- Next-update countdown badge -->
    <div
      class="absolute top-4 left-4 bg-white border border-gray-200 rounded-md shadow px-2 py-1 text-sm z-10"
    >
      Refresh in {{ countdown }}s
    </div>

    <!-- Graph container -->
    <div
      class="bg-white rounded-xl border border-gray-300 shadow h-full"
      ref="graphContainer"
    ></div>

    <!-- Node detail panel -->
    <div
      v-if="selectedNode"
      class="absolute top-4 right-4 bg-white border border-gray-300 rounded-xl shadow p-4 w-64 z-10"
    >
      <div class="mb-2">
        <template v-if="editing">
          <div class="flex items-center mb-2">
            <input
              v-model="newName"
              class="border border-gray-300 rounded p-1 flex-1 text-sm"
              placeholder="Enter name"
            />
          </div>
          <div class="flex justify-start gap-2">
            <button
              class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
              @click="saveName"
              :disabled="saving"
            >
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <button
              class="px-3 py-1 bg-gray-200 rounded text-sm hover:bg-gray-300"
              @click="cancelEdit"
              :disabled="saving"
            >
              Cancel
            </button>
          </div>
        </template>
        <template v-else>
          <div class="flex items-center justify-between">
            <span class="font-semibold text-lg break-all">{{ selectedNode.label }}</span>
            <button
              class="ml-1 text-black hover:text-gray-700"
              @click="startEdit"
              title="Rename"
            >
              <!-- pencil icon -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="black" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 20h9M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </button>
          </div>
        </template>
      </div>

      <p class="text-sm"><strong>IP:</strong> {{ selectedNode.id }}</p>
      <p class="mt-1 text-sm">
        <strong>Status: </strong>
        <span :class="selectedNode.online ? 'text-emerald-600' : 'text-slate-500 italic'">
          {{ selectedNode.online ? 'Online' : 'Offline' }}
        </span>
      </p>
      <p class="mt-1 text-sm"><strong>MAC:</strong> {{ selectedNode.mac || 'Unknown' }}</p>
      <p class="mt-1 text-sm"><strong>Hostname:</strong> {{ selectedNode.hostname || 'Unknown' }}</p>
      <p class="mt-1 text-sm"><strong>Vendor:</strong> {{ selectedNode.vendor || 'Unknown' }}</p>

      <button
        class="mt-4 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
        @click="closePanel"
      >
        Close
      </button>
    </div>

    <!-- Legend -->
    <div class="absolute bottom-4 left-4 bg-white border border-gray-200 rounded-md shadow p-2 text-xs z-10">
      <div><span class="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-1"></span> Online</div>
      <div><span class="inline-block w-3 h-3 rounded-full bg-slate-400 mr-1"></span> Offline</div>
    </div>

    <!-- Zoom Controls -->
    <div class="absolute bottom-4 right-4 flex flex-col space-y-2 z-10">
      <button
        @click="zoomIn"
        class="text-sm px-2 py-1 bg-white border border-gray-200 rounded-md shadow hover:bg-gray-100"
      >
        ＋
      </button>
      <button
        @click="zoomOut"
        class="text-sm px-2 py-1 bg-white border border-gray-200 rounded-md shadow hover:bg-gray-100"
      >
        －
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const REFRESH_INTERVAL = 10 // seconds
const previousStates = new Map()

let timerId
let countdownTimer

const positions = new Map()
let simulation

const graphContainer = ref(null)
const selectedNode = ref(null)

const countdown = ref(REFRESH_INTERVAL)

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
  d3.select(container).selectAll('*').remove()
  const width = container.clientWidth
  const height = container.clientHeight

  // Detect state changes
  const changedIds = new Set()
  for (const node of nodes) {
    const prevOnline = previousStates.get(node.id)
    if (prevOnline !== undefined && prevOnline !== node.online) {
      changedIds.add(node.id)
    }
    previousStates.set(node.id, node.online)
  }

  const svg = d3.select(container).append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .classed('w-full h-full', true)

  const zoomGroup = svg.append('g')

  const link = zoomGroup.append('g')
    .attr('stroke', '#cbd5e1')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke-width', 2)

  const nodeGroup = zoomGroup.append('g')
    .attr('stroke', '#e5e7eb')
    .attr('stroke-width', 2)
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', d => d.is_gateway ? 20 : 12)
    .attr('fill', d => d.is_gateway ? '#10b981' : d.online ? '#10b981' : '#94a3b8')
    .style('cursor', 'pointer')
    .style('filter', 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1))')
    .on('mouseover', function () { d3.select(this).attr('stroke', '#0ea5e9') })
    .on('mouseout',  function () { d3.select(this).attr('stroke', '#e5e7eb') })
    .on('click', (_, d) => {
      selectedNode.value = d
      editing.value = false
      newName.value = d.label
    })
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag',  dragged)
      .on('end',   dragended)
    )

  const pulses = 5           // Number of pulse cycles
  const pulseInDur = 400     // Duration of the outward pulse in ms
  const pulseOutDur = 500    // Duration of the inward pulse in ms
  const pauseDur = 200       // Pause between each pulse cycle in ms
  const baseStroke = 2       // Default stroke width
  const thickStroke = 8      // Stroke width during pulse

  changedIds.forEach(id => {
    const sel = zoomGroup
      .selectAll('circle')
      .filter(d => d.id === id)

    let t0 = 0
    for (let i = 0; i < pulses; i++) {
      // pulse out
      sel.transition()
        .delay(t0)
        .duration(pulseInDur)
        .attr('stroke-width', thickStroke)
        .attr('stroke', d => d.online ? '#10b981' : '#94a3b8')
        .ease(d3.easeQuadOut)

      t0 += pulseInDur

      // pulse in
      sel.transition()
        .delay(t0)
        .duration(pulseOutDur)
        .attr('stroke-width', baseStroke)
        .attr('stroke', '#e5e7eb')
        .ease(d3.easeQuadIn)

      t0 += pulseOutDur + pauseDur
    }
  })

  const labels = zoomGroup.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'label-group')

  labels.append('rect')
    .attr('x', 0)
    .attr('y', -10)
    .attr('rx', 3)
    .attr('ry', 3)
    .attr('fill', 'white')
    .attr('opacity', 0.8)

  labels.append('text')
    .text(d => d.label)
    .attr('font-size', '0.75rem')
    .attr('fill', '#111')
    .attr('x', 4)
    .attr('y', 0)

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(200))
    .force('charge', d3.forceManyBody().strength(-800))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(50))
    .on('tick', ticked)

  function ticked() {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeGroup
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .each(d => positions.set(d.id, { x: d.x, y: d.y }))

    labels.attr('transform', d => `translate(${d.x + 15}, ${d.y + 5})`)
    labels.selectAll('rect').each(function () {
      const textEl = this.nextSibling
      if (textEl && textEl.getBBox) {
        const { width, height } = textEl.getBBox()
        d3.select(this)
          .attr('width', width + 8)
          .attr('height', height + 4)
      }
    })
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

  // Zooming
  const zoom = d3.zoom()
    .scaleExtent([0.5, 5])
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform)
      renderGraph.zoomTransform = event.transform
    })

  svg.call(zoom)
  renderGraph.zoom = zoom
  renderGraph.zoomTransform = d3.zoomIdentity
  svg.call(zoom.transform, renderGraph.zoomTransform)
}

async function updateGraph() {
  try {
    const topo = await fetchTopology()
    renderGraph(topo)
  } catch (e) {
    console.error('Failed to fetch topology:', e)
  } finally {
    clearTimeout(timerId)
    countdown.value = REFRESH_INTERVAL
    timerId = setTimeout(updateGraph, REFRESH_INTERVAL * 1000)
  }
}

function zoomIn() {
  const svg = d3.select(graphContainer.value).select('svg')
  renderGraph.zoomTransform = renderGraph.zoomTransform.scale(1.2)
  svg.transition().duration(300).call(renderGraph.zoom.transform, renderGraph.zoomTransform)
}

function zoomOut() {
  const svg = d3.select(graphContainer.value).select('svg')
  renderGraph.zoomTransform = renderGraph.zoomTransform.scale(0.8)
  svg.transition().duration(300).call(renderGraph.zoom.transform, renderGraph.zoomTransform)
}

function startCountdown() {
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
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
  startCountdown()
  window.addEventListener('resize', updateGraph)
})
onUnmounted(() => {
  clearTimeout(timerId)
  clearInterval(countdownTimer)
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
