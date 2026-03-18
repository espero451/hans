<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getDispatcherStatus,
  getDispatcherTrace,
  restartDispatcher as restartDispatcherRequest,
} from '../api/settings'
import Button from 'primevue/button'
import Card from 'primevue/card'

/*
--- Dispatcher State --------------------------------------------------
*/

const dispatcherStatus = ref<'running' | 'stopped' | 'unknown'>('unknown')
const dispatcherError = ref<string | null>(null)
const dispatcherLoading = ref(false)
const dispatcherLastStartedAt = ref<string | null>(null)
const dispatcherLastStoppedAt = ref<string | null>(null)

/*
--- Dispatcher Actions ------------------------------------------------
*/

async function loadDispatcherStatus() {
  try {
    const data = await getDispatcherStatus()
    dispatcherStatus.value = data.running ? 'running' : 'stopped'
    dispatcherError.value = data.error || null
    dispatcherLastStartedAt.value = data.last_started_at || null
    dispatcherLastStoppedAt.value = data.last_stopped_at || null
  } catch (_err) {
    dispatcherStatus.value = 'stopped'
    dispatcherError.value = 'Unable to load dispatcher status'
    dispatcherLastStartedAt.value = null
    dispatcherLastStoppedAt.value = null
  }
}

async function restartDispatcher() {
  dispatcherLoading.value = true
  try {
    const data = await restartDispatcherRequest()
    dispatcherStatus.value = data.running ? 'running' : 'stopped'
    dispatcherError.value = data.error || null
    dispatcherLastStartedAt.value = data.last_started_at || null
    dispatcherLastStoppedAt.value = data.last_stopped_at || null
  } finally {
    dispatcherLoading.value = false
  }
}

async function openDispatcherTrace() {
  const traceWindow = window.open('', '_blank')
  if (!traceWindow) return

  const doc = traceWindow.document
  doc.title = 'Dispatcher Trace'

  // Styles
  const style = doc.createElement('style')
  style.textContent = `
    body {
      background: #000;
      margin: 0;
      padding: 16px;
    }
    pre {
      color: #e2e8f0;
      font-family: monospace;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.4;
    }
  `
  doc.head.appendChild(style)

  const pre = doc.createElement('pre')
  pre.textContent = 'Loading dispatcher trace...'
  doc.body.appendChild(pre)

  try {
    const traceData = await getDispatcherTrace()
    const traceText = typeof traceData === 'string' ? traceData : JSON.stringify(traceData, null, 2)

    pre.textContent = traceText || 'No dispatcher trace available.'
  } catch {
    pre.textContent = 'Unable to load dispatcher trace.'
  }
}

onMounted(loadDispatcherStatus)
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Settings</h2>

    <section>
      <Card>
        <template #title>Dispatcher</template>
        <template #content>
          <div class="flex align-items-start gap-3 w-full">
            <div class="flex flex-column gap-1">
              <div>
                Status: <strong>{{ dispatcherStatus }}</strong>
              </div>
              <div>Last start: {{ dispatcherLastStartedAt || '-' }}</div>
              <div>Last stop: {{ dispatcherLastStoppedAt || '-' }}</div>
              <div v-if="dispatcherError">Error: {{ dispatcherError }}</div>
            </div>
            <div class="ml-auto flex gap-2">
              <Button
                label="Restart dispatcher"
                :loading="dispatcherLoading"
                @click="restartDispatcher"
              />
              <Button label="Open trace" @click="openDispatcherTrace" />
            </div>
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>
