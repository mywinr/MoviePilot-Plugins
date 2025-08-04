<template>
  <v-app>
    <v-main>
      <component
        :is="currentView"
        :model="props.model"
        :api="props.api"
        @switch="handleSwitch"
        @close="handleClose"
        @action="handleAction"
      />
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, markRaw } from 'vue'
import Page from './components/Page.vue'
import Config from './components/Config.vue'

// 接收初始配置
const props = defineProps({
  model: {
    type: Object,
    default: () => {},
  },
  api: {
    type: Object,
    default: () => {},
  },
})

// 当前视图
const currentView = ref(markRaw(Page))

// 处理视图切换
function handleSwitch() {
  currentView.value = currentView.value === Page ? markRaw(Config) : markRaw(Page)
}

// 处理关闭
function handleClose() {
  // 通知主应用关闭插件
  window.parent.postMessage({ type: 'close-plugin' }, '*')
}

// 处理操作事件
function handleAction() {
  // 可以在这里处理一些全局操作
  console.log('Action event received')
}
</script>