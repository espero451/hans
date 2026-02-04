<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/auth";

const username = ref("");
const password = ref("");
const router = useRouter();

async function submit() {
  await login(username.value, password.value);
  router.push("/dashboard");
}
</script>

<template>
  <h2>Login</h2>
  <input v-model="username" placeholder="Username" />&nbsp;
  <input v-model="password" type="password" />&nbsp;
  <button @click="submit">Login</button>
</template>
