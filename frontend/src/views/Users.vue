<template>
  <div class="users">
    <h1>用戶管理</h1>
    
    <div class="user-form">
      <h2>新增用戶</h2>
      <form @submit.prevent="createUser">
        <div>
          <label>用戶名:</label>
          <input v-model="newUser.username" type="text" required />
        </div>
        <div>
          <label>Email:</label>
          <input v-model="newUser.email" type="email" required />
        </div>
        <div>
          <label>密碼:</label>
          <input v-model="newUser.password" type="password" required />
        </div>
        <button type="submit" :disabled="loading">新增用戶</button>
      </form>
    </div>

    <div class="users-list">
      <h2>用戶列表</h2>
      <button @click="fetchUsers">重新載入</button>
      <div v-if="users.length > 0">
        <div v-for="user in users" :key="user.id" class="user-card">
          <h3>{{ user.username }}</h3>
          <p>Email: {{ user.email }}</p>
          <p>狀態: {{ user.is_active ? '啟用' : '停用' }}</p>
          <p>建立時間: {{ new Date(user.created_at).toLocaleString() }}</p>
        </div>
      </div>
      <p v-else>暫無用戶資料</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/api'

interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

const users = ref<User[]>([])
const loading = ref(false)
const newUser = ref({
  username: '',
  email: '',
  password: ''
})

const fetchUsers = async () => {
  try {
    const response = await apiService.get('/users/')
    users.value = response.data
  } catch (error) {
    console.error('獲取用戶列表失敗:', error)
  }
}

const createUser = async () => {
  loading.value = true
  try {
    await apiService.post('/users/', newUser.value)
    newUser.value = { username: '', email: '', password: '' }
    await fetchUsers()
  } catch (error) {
    console.error('新增用戶失敗:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.users {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.user-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.user-form div {
  margin-bottom: 15px;
}

.user-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.user-form input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 15px;
}

button:disabled {
  background-color: #ccc;
}
</style>