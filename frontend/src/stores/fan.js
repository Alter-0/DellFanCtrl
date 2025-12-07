import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useFanStore = defineStore('fan', () => {
  const status = ref({
    cpu_temp: 0,
    fan_speed: 0,
    power: 0,
    control_mode: 'auto',
    last_update: null
  })
  
  const curve = ref([])
  const history = ref([])
  const logs = ref([])
  
  let ws = null
  
  // WebSocket 连接
  function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      return // 已连接，不重复连接
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'status_update') {
          status.value = { ...status.value, ...data.data }
        } else if (data.type === 'log') {
          logs.value.unshift(data.data)
          if (logs.value.length > 200) {
            logs.value.pop()
          }
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onclose = () => {
      ws = null
      setTimeout(connectWebSocket, 3000)
    }
  }
  
  function disconnectWebSocket() {
    if (ws) {
      ws.close()
      ws = null
    }
  }
  
  // API 调用
  async function fetchStatus() {
    const { data } = await axios.get('/api/dashboard/status')
    status.value = data
  }
  
  async function fetchCurve() {
    const { data } = await axios.get('/api/curve')
    curve.value = data.points
  }

  async function saveCurve(points) {
    await axios.put('/api/curve', { points })
    curve.value = points
  }
  
  async function fetchHistory(range = '1h') {
    const { data } = await axios.get(`/api/dashboard/history?range=${range}`)
    history.value = data.data
  }
  
  async function fetchLogs(params = {}) {
    const { data } = await axios.get('/api/logs', { params })
    logs.value = data.logs
  }
  
  return {
    status,
    curve,
    history,
    logs,
    connectWebSocket,
    disconnectWebSocket,
    fetchStatus,
    fetchCurve,
    saveCurve,
    fetchHistory,
    fetchLogs
  }
})
