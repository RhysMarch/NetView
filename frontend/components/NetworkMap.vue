<!-- NetworkMap.vue -->
<template>
  <div class="bg-white rounded-xl border border-gray-300 shadow p-8 h-full relative" ref="graphContainer">
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'

const SYNC_INTERVAL = 10000

const graphContainer = ref(null)
const countdown = ref(SYNC_INTERVAL / 1000)
let intervalId = null
let countdownId = null
let svg = null
let simulation = null

const fetchTopology = async () => {
  const res = await fetch('http://localhost:8000/api/topology')
  return await res.json()
}

const renderGraph = ({ nodes, links }) => {
  d3.select(graphContainer.value).select("svg").remove()
  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight

  svg = d3.select(graphContainer.value).append("svg")
    .attr("width", "100%")
    .attr("height", "100%")

  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))

  const link = svg.append("g").attr("stroke", "#ccc")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", 2)

  const node = svg.append("g").attr("stroke", "#fff")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", 10)
    .attr("fill", "#007bff")
    .call(d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on("drag", (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })
    )

  const label = svg.append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text(d => d.label)
    .attr("x", 12)
    .attr("y", 3)

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y)
    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
    label
      .attr("x", d => d.x + 12)
      .attr("y", d => d.y + 3)
  })
}

const updateGraph = async () => {
  const topology = await fetchTopology()
  renderGraph(topology)
  countdown.value = SYNC_INTERVAL / 1000
}

onMounted(() => {
  updateGraph()
  intervalId = setInterval(updateGraph, SYNC_INTERVAL)
  countdownId = setInterval(() => {
    if (countdown.value > 0) countdown.value--
    else countdown.value = SYNC_INTERVAL / 1000
  }, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
  clearInterval(countdownId)
})
</script>


<style scoped>
svg {
  width: 100%;
  height: 100%;
}
</style>
