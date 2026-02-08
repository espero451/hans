<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/auth";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";

const username = ref("");
const password = ref("");
const router = useRouter();

async function submit() {
  await login(username.value, password.value);
  router.push("/dashboard");
}
</script>

<template>
  <div class="p-4 flex justify-content-center">
    <Card class="surface-card p-3 border-round-xl shadow-1" style="max-width: 420px; width: 100%;">
      <template #title>Login</template>
      <template #content>
        <div class="flex flex-column gap-2">
          <InputText v-model="username" placeholder="Username" />
          <Password v-model="password" toggleMask :feedback="false" />
          <Button label="Login" @click="submit" />
        </div>
      </template>
    </Card>
  </div>
</template>
