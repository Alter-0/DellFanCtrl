import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import './styles/main.css'

// 按需导入图标
import {
  Search,
  Refresh,
  Cpu,
  Odometer,
  Lightning,
  Check,
  RefreshRight,
  Delete,
  Plus,
  DataLine
} from '@element-plus/icons-vue'

const app = createApp(App)

// 注册使用的图标
const icons = { Search, Refresh, Cpu, Odometer, Lightning, Check, RefreshRight, Delete, Plus, DataLine }
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(ElementPlus)
app.mount('#app')
