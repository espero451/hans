<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/http'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'
import AutoComplete from 'primevue/autocomplete'

const router = useRouter()

type FilterOption = {
  label: string
  value: number
}

const orders = ref<any[]>([])
const totalRecords = ref(0)
const rows = ref(50)
const first = ref(0)
const loading = ref(false)
const ownerSuggestions = ref<FilterOption[]>([])
const patientSuggestions = ref<FilterOption[]>([])

const statusFilter = ref<'active' | 'resulted' | 'archived'>('active')
const selectedDate = ref<Date | null>(null)
const selectedOwner = ref<FilterOption | string | null>(null)
const selectedPatient = ref<FilterOption | string | null>(null)

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Resulted', value: 'resulted' },
  { label: 'Archived', value: 'archived' },
]

function orderHasResults(order: any) {
  return (order?.test_runs || []).some(
    (run: any) => Array.isArray(run.results) && run.results.length > 0,
  )
}

function urgencySeverity(urgency?: string) {
  if (urgency === 'STAT') return 'danger'
  if (urgency === 'URGENT') return 'warning'
  return 'secondary'
}

function dateKey(input: string | Date | null) {
  if (!input) return ''
  const date = typeof input === 'string' ? new Date(input) : input
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function patientLabel(order: any) {
  return order?.patient?.name ? order.patient.name : `Patient #${order.patient_id}`
}

function ownerLabel(order: any) {
  const patient = order?.patient
  if (!patient) return 'Unknown'
  const owner = patient.owner
  return owner ? `${owner.first_name} ${owner.last_name}` : `Owner #${patient.owner_id}`
}

const resultsSummary = computed(
  () => `${orders.value.length} of ${totalRecords.value} orders`,
)

async function searchOwners(event: { query?: string }) {
  if (!event.query || event.query.length < 2) {
    ownerSuggestions.value = []
    return
  }
  const res = await api.get('/owners/', {
    params: {
      q: event.query,
      limit: 20,
    },
  })
  ownerSuggestions.value = res.data.map((owner: any) => ({
    label: `${owner.first_name} ${owner.last_name}`,
    value: owner.id,
  }))
}

async function searchPatients(event: { query?: string }) {
  if (!event.query || event.query.length < 2) {
    patientSuggestions.value = []
    return
  }
  const res = await api.get('/patients/', {
    params: {
      q: event.query,
      limit: 20,
    },
  })
  patientSuggestions.value = res.data.items.map((patient: any) => ({
    label: patient.name,
    value: patient.id,
  }))
}

function selectedId(option: FilterOption | string | null) {
  if (!option || typeof option === 'string') return undefined
  return option.value
}

async function loadOrders(event?: any) {
  const skip = event?.first ?? first.value
  const limit = event?.rows ?? rows.value
  first.value = skip
  rows.value = limit
  loading.value = true

  try {
    const params: any = {
      skip,
      limit,
      patient_id: selectedId(selectedPatient.value),
      owner_id: selectedId(selectedOwner.value),
      created_date: dateKey(selectedDate.value) || undefined,
    }

    if (statusFilter.value === 'active') params.archived = false
    if (statusFilter.value === 'archived') params.archived = true
    if (statusFilter.value === 'resulted') params.resulted = true

    const res = await api.get('/orders', { params })
    orders.value = res.data.items
    totalRecords.value = res.data.total
  } finally {
    loading.value = false
  }
}

function reloadFromFirstPage() {
  loadOrders({ first: 0, rows: rows.value })
}

function resetFilters() {
  statusFilter.value = 'active'
  selectedDate.value = null
  selectedOwner.value = null
  selectedPatient.value = null
}

watch([statusFilter, selectedDate, selectedOwner, selectedPatient], () => {
  if (typeof selectedOwner.value === 'string') return
  if (typeof selectedPatient.value === 'string') return
  reloadFromFirstPage()
})

onMounted(async () => {
  await loadOrders({ first: 0, rows: rows.value })
})
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Orders</h2>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <Dropdown
          v-model="statusFilter"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Status"
        />
        <DatePicker v-model="selectedDate" placeholder="Filter date" showIcon showButtonBar />
        <AutoComplete
          v-model="selectedOwner"
          :suggestions="ownerSuggestions"
          optionLabel="label"
          placeholder="Filter owner"
          @complete="searchOwners"
          dropdown
          forceSelection
        />
        <AutoComplete
          v-model="selectedPatient"
          :suggestions="patientSuggestions"
          optionLabel="label"
          placeholder="Filter patient"
          @complete="searchPatients"
          dropdown
          forceSelection
        />
        <Button label="Reset" severity="secondary" @click="resetFilters" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex align-items-center justify-content-between mb-2">
        <span class="text-600">{{ resultsSummary }}</span>
      </div>
      <DataTable
        :value="orders"
        dataKey="id"
        lazy
        paginator
        :rows="rows"
        :totalRecords="totalRecords"
        :loading="loading"
        :emptyMessage="'No orders found'"
        @page="loadOrders"
        @row-click="(e) => router.push(`/orders/${e.data.id}`)"
      >
        <Column header="Order">
          <template #body="{ data }">
            <a :href="`/orders/${data.id}`">#{{ data.id }}</a>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag
              :value="data.archived ? 'Archived' : 'Active'"
              :severity="data.archived ? 'secondary' : 'success'"
            />
          </template>
        </Column>
        <Column header="Urgency">
          <template #body="{ data }">
            <Tag :value="data.urgency || 'ROUTINE'" :severity="urgencySeverity(data.urgency)" />
          </template>
        </Column>
        <Column header="Results">
          <template #body="{ data }">
            <Tag
              :value="orderHasResults(data) ? 'Resulted' : 'Pending'"
              :severity="orderHasResults(data) ? 'info' : 'warning'"
            />
          </template>
        </Column>
        <Column header="Created">
          <template #body="{ data }">
            {{ new Date(data.created_at).toLocaleString() }}
          </template>
        </Column>
        <Column header="Patient">
          <template #body="{ data }">
            <a :href="`/patients/${data.patient_id}`">
              {{ patientLabel(data) }}
            </a>
          </template>
        </Column>
        <Column header="Owner">
          <template #body="{ data }">
            {{ ownerLabel(data) }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
