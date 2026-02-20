<script setup lang="ts">
import { ref, onMounted } from "vue";
import api from "../api/http";
import Button from "primevue/button";
import Card from "primevue/card";

/*
# --- Dispatcher State -------------------------------------------------
*/

const dispatcherStatus = ref<"running" | "stopped" | "unknown">("unknown");
const dispatcherError = ref<string | null>(null);
const dispatcherLoading = ref(false);
const dispatcherLastStartedAt = ref<string | null>(null);
const dispatcherLastStoppedAt = ref<string | null>(null);

/*
# --- Dispatcher Actions -----------------------------------------------
*/

async function loadDispatcherStatus() {
  try {
    const res = await api.get("/settings/dispatcher/status");
    dispatcherStatus.value = res.data.running ? "running" : "stopped";
    dispatcherError.value = res.data.error || null;
    dispatcherLastStartedAt.value = res.data.last_started_at || null;
    dispatcherLastStoppedAt.value = res.data.last_stopped_at || null;
  } catch (error) {
    dispatcherStatus.value = "stopped";
    dispatcherError.value = "Unable to load dispatcher status";
    dispatcherLastStartedAt.value = null;
    dispatcherLastStoppedAt.value = null;
  }
}

async function restartDispatcher() {
  dispatcherLoading.value = true;
  try {
    const res = await api.post("/settings/dispatcher/restart");
    dispatcherStatus.value = res.data.running ? "running" : "stopped";
    dispatcherError.value = res.data.error || null;
    dispatcherLastStartedAt.value = res.data.last_started_at || null;
    dispatcherLastStoppedAt.value = res.data.last_stopped_at || null;
  } finally {
    dispatcherLoading.value = false;
  }
}

async function openDispatcherTrace() {
  const traceWindow = window.open("", "_blank");
  if (!traceWindow) {
    return;
  }
  traceWindow.document.title = "Dispatcher Trace";
  traceWindow.document.body.style.whiteSpace = "pre-wrap";
  traceWindow.document.body.style.fontFamily = "monospace";
  traceWindow.document.body.textContent = "Loading dispatcher trace...";
  try {
    const res = await api.get("/settings/dispatcher/trace", {
      responseType: "text",
    });
    const traceText =
      typeof res.data === "string" ? res.data : JSON.stringify(res.data, null, 2);
    traceWindow.document.body.textContent =
      traceText || "No dispatcher trace available.";
  } catch (error) {
    traceWindow.document.body.textContent = "Unable to load dispatcher trace.";
  }
}

onMounted(loadDispatcherStatus);
</script>

<template>
  <div class="p-4 flex flex-column gap-3">

    <section>
      <Card>
        <template #title>Dispatcher</template>
        <template #content>
          <div class="flex align-items-start gap-3 w-full">
            <div class="flex flex-column gap-1">
              <div>Status: <strong>{{ dispatcherStatus }}</strong></div>
              <div>Last start: {{ dispatcherLastStartedAt || "-" }}</div>
              <div>Last stop: {{ dispatcherLastStoppedAt || "-" }}</div>
              <div v-if="dispatcherError">Error: {{ dispatcherError }}</div>
            </div>
            <div class="ml-auto flex gap-2">
              <Button
                label="Restart dispatcher"
                :loading="dispatcherLoading"
                @click="restartDispatcher"
              />
              <Button
                label="Open trace"
                @click="openDispatcherTrace"
              />
            </div>
          </div>
        </template>
      </Card>
    </section>

  </div>
</template>
