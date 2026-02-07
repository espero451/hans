<template>

<img src="/assets/hans.png" width="100"> 
<!--<h2>Hans LIS</h2>-->

  <div>
    <!-- Top navigation -->
    <nav class="navbar">
      <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
      <router-link to="/patients" class="nav-link">Patients</router-link>
      <router-link to="/owners" class="nav-link">Owners</router-link>
      <router-link to="/orders" class="nav-link">Orders</router-link>
      <router-link to="/settings" class="nav-link">Settings</router-link>
      <router-link to="/login" class="nav-link login">⏻</router-link>
    </nav>

    <!-- Page content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>

</template>

<script setup lang="ts">
//
</script>

<style scoped>
/* Navbar styles */
.navbar {
  display: flex;
  flex-wrap: wrap;
  background-color: #1e1e2f;
  padding: 0.5rem 1rem;
  color: white;
  gap: 1rem;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.nav-link:hover {
  background-color: #33334d;
}

.nav-link.login {
  margin-left: auto;
  background-color: #3b82f6;
}

.nav-link.login:hover {
  background-color: #2563eb;
}

/* Main content styles */
.main-content {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  text-align: left;
}

/* Responsive */
@media (max-width: 600px) {
  .navbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .nav-link.login {
    margin-left: 0;
  }
}
</style>
