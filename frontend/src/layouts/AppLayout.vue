<template>
  <div class="app-shell">
    <Menubar :model="items" class="app-menubar">
      <template #start>
        <img src="/assets/hans.png" width="48" height="48" class="brand-logo" alt="Hans LIS" />
      </template>
      <template #end>
        <Button
          icon="pi pi-power-off"
          severity="secondary"
          text
          @click="router.push('/login')"
        />
      </template>
    </Menubar>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import Menubar from "primevue/menubar";
import Button from "primevue/button";

const router = useRouter();

const items = [
  { label: "Dashboard", icon: "pi pi-home", command: () => router.push("/dashboard") },
  { label: "Patients", icon: "pi pi-users", command: () => router.push("/patients") },
  { label: "Owners", icon: "pi pi-id-card", command: () => router.push("/owners") },
  { label: "Orders", icon: "pi pi-list-check", command: () => router.push("/orders") },
  { label: "Settings", icon: "pi pi-cog", command: () => router.push("/settings") },
];
</script>

<style scoped>
.app-shell {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.brand-logo {
  display: block;
}

.app-menubar {
  margin-bottom: 1rem;
  border-radius: 12px;
  border: 1px solid #e2e6ef;
}

.main-content {
  text-align: left;
}
</style>
