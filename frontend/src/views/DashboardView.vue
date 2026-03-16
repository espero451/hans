<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Card from 'primevue/card'
import api from '../api/http'

type DashboardStats = {
  total_orders: number
  total_patients: number
  total_owners: number
}

const stats = ref<DashboardStats>({
  total_orders: 0,
  total_patients: 0,
  total_owners: 0,
})
const isLoading = ref(false)
const errorMessage = ref('')

async function loadStats(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const res = await api.get('/dashboard/stats')
    stats.value = res.data
  } catch (error) {
    console.error('Failed to load dashboard stats', error)
    errorMessage.value = 'Failed to load dashboard statistics.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadStats)
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Dashboard</h2>

    <Card>
      <template #content>
        <div v-if="errorMessage" class="text-red-500">{{ errorMessage }}</div>
        <div v-else-if="isLoading" class="text-500">Loading...</div>
        <div v-else class="grid">
          <div class="col-12 md:col-4">
            <div class="text-500 text-sm">Total orders</div>
            <div class="text-2xl font-semibold mt-1">{{ stats.total_orders }}</div>
          </div>
          <div class="col-12 md:col-4">
            <div class="text-500 text-sm">Total patients</div>
            <div class="text-2xl font-semibold mt-1">{{ stats.total_patients }}</div>
          </div>
          <div class="col-12 md:col-4">
            <div class="text-500 text-sm">Total owners</div>
            <div class="text-2xl font-semibold mt-1">{{ stats.total_owners }}</div>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>
