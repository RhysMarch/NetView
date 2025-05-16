<template>
  <div
    class="bg-white rounded-xl border border-gray-300 shadow h-full relative"
    ref="graphContainer"
  ></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
let timerId

async function fetchTopology() {
  const res = await fetch(`${API}/api/topology`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

function renderGraph({ nodes, links }) {
  // Clear any existing SVG
  d3.select(graphContainer.value).select('svg').remove()

  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight

  const svg = d3
    .select(graphContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const simulation = d3
    .forceSimulation(nodes)
    .force('link',
      d3.forceLink(links)
        .id(d => d.id)
        .distance(200)    // increased link distance
    )
    .force('charge',
      d3.forceManyBody().strength(-800)  // stronger repulsion
    )
    .force('center',
      d3.forceCenter(width / 2, height / 2)
    )
    .force('collide',
      d3.forceCollide().radius(25)      // prevent overlap
    )

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
    .data(nodes)
    .join('circle')
    .attr('r', 12)                  // larger radius
    .attr('fill', d => (d.online ? '#007bff' : '#dc2626'))
    .call(
      d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
    )

  // Draw labels
  svg.append('g')
    .selectAll('text')
    .data(nodes)
    .join('text')
    .text(d => d.label)
    .attr('x', 15)
    .attr('y', 5)
    .attr('font-size', '0.8rem')
    .attr('fill', '#333')

  // Simulation tick
  simulation.on('tick', () => {
    svg.selectAll('line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    svg.selectAll('circle')
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    svg.selectAll('text')
      .attr('x', d => d.x + 15)
      .attr('y', d => d.y + 5)
  })
}

async function updateGraph() {
  try {
    const topo = await fetchTopology()
    renderGraph(topo)
  } catch (e) {
    console.error('Failed to fetch topology:', e)
  } finally {
    clearTimeout(timerId)
    timerId = setTimeout(updateGraph, 10000)
  }
}

const graphContainer = ref(null)

onMounted(updateGraph)
onUnmounted(() => clearTimeout(timerId))
</script>

<style scoped>
svg {
  width: 100%;
  height: 100%;
}
</style>
