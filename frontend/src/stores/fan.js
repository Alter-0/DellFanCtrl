import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
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
  
  // 错误状态管理
  const errors = ref({
    status: null,
    curve: null,
    history: null,
    logs: null,
    websocket: null
  })
  
  const loading = ref({
    status: false,
    curve: false,
    history: false,
    logs: false
  })
  
  // 是否有任何错误
  const hasError = computed(() => Object.values(errors.value).some(e => e !== null))
  
  // 清除指定错误
  function clearError(key) {
    if (key) {
      errors.value[key] = null
    } else {
      Object.keys(errors.value).forEach(k => errors.value[k] = null)
    }
  }
  
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
      errors.value.websocket = 'WebSocket 连接错误'
    }
    
    ws.onclose = () => {
      ws = null
      errors.value.websocket = 'WebSocket 连接已断开，正在重连...'
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.onopen = () => {
      errors.value.websocket = null
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
    loading.value.status = true
    errors.value.status = null
    try {
      const { data } = await axios.get('/api/dashboard/status')
      status.value = data
    } catch (error) {
      errors.value.status = error.response?.data?.detail || error.message || '获取状态失败'
      throw error
    } finally {
      loading.value.status = false
    }
  }
  
  async function fetchCurve() {
    loading.value.curve = true
    errors.value.curve = null
    try {
      const { data } = await axios.get('/api/curve')
      curve.value = data.points
    } catch (error) {
      errors.value.curve = error.response?.data?.detail || error.message || '获取曲线失败'
      throw error
    } finally {
      loading.value.curve = false
    }
  }

  async function saveCurve(points) {
    loading.value.curve = true
    errors.value.curve = null
    try {
      await axios.put('/api/curve', { points })
      curve.value = points
    } catch (error) {
      errors.value.curve = error.response?.data?.detail || error.message || '保存曲线失败'
      throw error
    } finally {
      loading.value.curve = false
    }
  }
  
  async function fetchHistory(range = '1h') {
    loading.value.history = true
    errors.value.history = null
    try {
      const { data } = await axios.get(`/api/dashboard/history?range=${range}`)
      history.value = data.data
    } catch (error) {
      errors.value.history = error.response?.data?.detail || error.message || '获取历史数据失败'
      throw error
    } finally {
      loading.value.history = false
    }
  }
  
  async function fetchLogs(params = {}) {
    loading.value.logs = true
    errors.value.logs = null
    try {
      const { data } = await axios.get('/api/logs', { params })
      logs.value = data.logs
    } catch (error) {
      errors.value.logs = error.response?.data?.detail || error.message || '获取日志失败'
      throw error
    } finally {
      loading.value.logs = false
    }
  }
  
  return {
    status,
    curve,
    history,
    logs,
    errors,
    loading,
    hasError,
    clearError,
    connectWebSocket,
    disconnectWebSocket,
    fetchStatus,
    fetchCurve,
    saveCurve,
    fetchHistory,
    fetchLogs
  }
})
