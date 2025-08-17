<template>
  <div class="home">
    <h1>歡迎使用全端開發專案</h1>
    <p>這是一個使用 Vue3 + TypeScript + FastAPI 的前後端分離專案</p>
    
    <div class="api-test">
      <h2>API 連接測試</h2>
      <button @click="testAPI" :disabled="loading">測試後端連接</button>
      <div v-if="apiResponse" class="response">
        <h3>後端回應:</h3>
        <pre>{{ apiResponse }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiService } from '@/services/api'

const loading = ref(false)
const apiResponse = ref<any>(null)

const testAPI = async () => {
  loading.value = true
  try {
    const response = await apiService.get('/')
    apiResponse.value = response.data
  } catch (error) {
    apiResponse.value = { error: '無法連接到後端 API' }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home {
  text-align: center;
  padding: 20px;
}

.api-test {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #ccc;
}

.response {
  margin-top: 20px;
  text-align: left;
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>