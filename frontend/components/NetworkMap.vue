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
      <h3 class="font-semibold mb-2">Node: {{ selectedNode.label }}</h3>
      <p><strong>IP:</strong> {{ selectedNode.id }}</p>
      <p>
        <strong>Status:</strong>
        <span :class="selectedNode.online ? 'text-green-600' : 'text-red-600'">
          {{ selectedNode.online ? ' Online' : ' Offline' }}
        </span>
      </p>
      <p><strong>MAC:</strong> {{ selectedNode.mac || 'Unknown' }}</p>
      <button
        class="mt-4 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
        @click="selectedNode = null"
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

async function fetchTopology() {
  const res = await fetch(`${API}/api/topology`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

function renderGraph({ nodes, links }) {
  const container = graphContainer.value
  // Clear previous SVG
  d3.select(container).selectAll('svg').remove()

  const width = container.clientWidth
  const height = container.clientHeight

  // Seed node positions from previous run
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

  // Update or create simulation
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(200))
    .force('charge', d3.forceManyBody().strength(-800))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(25))
    .on('tick', onTick)

  // Draw links
  svg.append('g')
    .attr('stroke', '#ccc')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke-width', 2)

  // Draw nodes
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
      })
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      )

  // Draw labels
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

    // ← if a node is selected, find its up-to-date copy
    if (selectedNode.value) {
      const fresh = topo.nodes.find(n => n.id === selectedNode.value.id)
      // either re-assign the full object…
      selectedNode.value = fresh || null
      // …or clear if it’s gone
    }

  } catch (e) {
    console.error('Failed to fetch topology:', e)
  } finally {
    clearTimeout(timerId)
    timerId = setTimeout(updateGraph, 10000)
  }
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
