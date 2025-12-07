<template>
  <el-container class="app-container">
    <el-header>
      <div class="header-content">
        <h1>🖥️ Dell 服务器风扇控制</h1>
        <el-tag :type="statusType">{{ statusText }}</el-tag>
      </div>
    </el-header>
    
    <el-main>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="仪表盘" name="dashboard">
          <Dashboard />
        </el-tab-pane>
        <el-tab-pane label="风扇曲线" name="curve">
          <CurveEditor />
        </el-tab-pane>
        <el-tab-pane label="系统日志" name="logs">
          <LogViewer />
        </el-tab-pane>
        <el-tab-pane label="系统设置" name="settings">
          <Settings />
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFanStore } from './stores/fan'
import Dashboard from './components/Dashboard.vue'
import CurveEditor from './components/CurveEditor.vue'
import LogViewer from './components/LogViewer.vue'
import Settings from './components/Settings.vue'

const activeTab = ref('dashboard')
const fanStore = useFanStore()

const statusType = computed(() => {
  return fanStore.status.control_mode === 'manual' ? 'success' : 'warning'
})

const statusText = computed(() => {
  return fanStore.status.control_mode === 'manual' ? '手动控制中' : '自动控制'
})

onMounted(() => {
  fanStore.connectWebSocket()
  fanStore.fetchStatus()
})

onUnmounted(() => {
  fanStore.disconnectWebSocket()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 1.5rem;
}
</style>
