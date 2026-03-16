<template>
  <div class="app-shell">
    <div class="content-shell">
      <Menubar :model="items" class="app-menubar">
        <template #start>
          <img src="/assets/hans.png" width="48" height="48" class="brand-logo" alt="Hans LIS" />
        </template>
        <template #end>
          <div class="flex align-items-center gap-3">
            <span v-if="user">
              {{ user.username }}
            </span>

            <Button icon="pi pi-power-off" severity="secondary" text @click="handleLogout" />
          </div>
        </template>
      </Menubar>
    </div>

    <main class="main-content content-shell">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Menubar from 'primevue/menubar'
import Button from 'primevue/button'
import { useAuth } from '../composables/useAuth'

const router = useRouter()

const { user, clearUser, loadUser } = useAuth()

onMounted(async () => {
  try {
    await loadUser()
  } catch (_err) {
    localStorage.removeItem('token')
  }
})

function handleLogout() {
  clearUser()
  localStorage.removeItem('token')
  router.push('/login')
}

const items = [
  { label: 'Dashboard', icon: 'pi pi-home', command: () => router.push('/dashboard') },
  { label: 'Patients', icon: 'pi pi-heart', command: () => router.push('/patients') },
  { label: 'Owners', icon: 'pi pi-users', command: () => router.push('/owners') },
  { label: 'Orders', icon: 'pi pi-list-check', command: () => router.push('/orders') },
  { label: 'Settings', icon: 'pi pi-cog', command: () => router.push('/settings') },
]
</script>

<style scoped>
.app-shell {
  width: 100%;
}

.brand-logo {
  display: block;
}

.app-menubar {
  margin-bottom: 0rem;
  border-radius: 12px;
  border: 1px solid #4d4e50;
  padding: 1rem;
}

.content-shell {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: 1rem;
}

.main-content {
  text-align: left;
}
</style>
