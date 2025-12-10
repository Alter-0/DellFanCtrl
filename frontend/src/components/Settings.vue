<template>
  <div class="settings">
    <el-card shadow="hover">
      <template #header>
        <span>iDRAC 连接设置</span>
      </template>
      
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="iDRAC 地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="192.168.1.100" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="root" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="输入新密码或留空保持不变" />
        </el-form-item>
        
        <el-form-item label="监控间隔" prop="interval">
          <el-input-number v-model="form.interval" :min="5" :max="300" :step="5" />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
          <el-button @click="loadSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="danger-zone" shadow="hover">
      <template #header>
        <span style="color: #F56C6C">危险操作</span>
      </template>
      
      <el-button type="warning" @click="restoreAutoControl">
        恢复自动风扇控制
      </el-button>
      <p class="hint">将风扇控制权交还给 iDRAC 自动管理</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const formRef = ref(null)
const saving = ref(false)

const form = reactive({
  ip_address: '',
  username: '',
  password: '',
  interval: 30
})

const rules = {
  ip_address: [
    { required: true, message: '请输入 iDRAC 地址', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  interval: [
    { required: true, message: '请设置监控间隔', trigger: 'blur' }
  ]
}

async function loadSettings() {
  try {
    const { data } = await axios.get('/api/settings')
    form.ip_address = data.ip_address || ''
    form.username = data.username || ''
    form.password = ''
    form.interval = data.interval || 30
  } catch (error) {
    console.error('Failed to load settings:', error)
    ElMessage.error('加载设置失败')
  }
}

async function saveSettings() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.password) {
      delete payload.password
    }
    
    await axios.put('/api/settings', payload)
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function restoreAutoControl() {
  try {
    await ElMessageBox.confirm(
      '确定要恢复自动风扇控制吗？这将停止手动控制。',
      '确认操作',
      { type: 'warning' }
    )
    
    await axios.post('/api/dashboard/restore-auto')
    ElMessage.success('已恢复自动控制')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 600px;
}

.unit {
  margin-left: 10px;
  color: #909399;
}

.danger-zone {
  margin-top: 20px;
}

.hint {
  margin-top: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
