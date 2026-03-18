<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createPatient, getPatientsPage, getSpecies } from '../api/patients'
import { searchOwnersByQuery } from '../api/owners'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import AutoComplete from 'primevue/autocomplete'
import DatePicker from 'primevue/datepicker'

const patients = ref<any[]>([])
const totalRecords = ref(0)
const rows = ref(50)
const loading = ref(false)
const ownerSuggestions = ref<any[]>([])
const filterOwnerSuggestions = ref<any[]>([])
const selectedOwner = ref<any>(null)
const filterName = ref('')
const filterSpeciesId = ref<number | null>(null)
const filterOwner = ref<any>(null)
const name = ref('')
const speciesId = ref<number | null>(null)
const sex = ref('unknown')
const speciesOptions = ref<any[]>([])
const birth_date = ref<Date | null>(null)
const sexOptions = [
  { label: 'Male', value: 'male' },
  { label: 'Female', value: 'female' },
  { label: 'Unknown', value: 'unknown' },
]
const router = useRouter()
const speciesName = computed(() => {
  const selected = speciesOptions.value.find((s) => s.id === speciesId.value)
  return selected ? selected.name : ''
})

async function loadPatients(event?: any) {
  const skip = event?.first ?? 0
  const limit = event?.rows ?? rows.value
  loading.value = true
  try {
    const params: any = { skip, limit }
    if (filterName.value.trim()) {
      params.q = filterName.value.trim()
    }
    if (filterSpeciesId.value) {
      params.species_id = filterSpeciesId.value
    }
    if (filterOwner.value?.value) {
      params.owner_id = filterOwner.value.value
    }
    const data = await getPatientsPage(params)
    patients.value = data.items
    totalRecords.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadSpecies() {
  speciesOptions.value = await getSpecies()
}

async function searchOwners(event: any) {
  if (!event.query || event.query.length < 2) {
    ownerSuggestions.value = []
    return
  }
  ownerSuggestions.value = await searchOwnersByQuery(event.query, 20)
}

async function searchFilterOwners(event: any) {
  if (!event.query || event.query.length < 2) {
    filterOwnerSuggestions.value = []
    return
  }
  filterOwnerSuggestions.value = await searchOwnersByQuery(event.query, 20)
}

function resetFilters() {
  filterName.value = ''
  filterSpeciesId.value = null
  filterOwner.value = null
  loadPatients({ first: 0, rows: rows.value })
}

// Add patient
async function addPatient() {
  const ownerId =
    selectedOwner.value && typeof selectedOwner.value !== 'string'
      ? selectedOwner.value.value
      : null
  if (!name.value || !speciesId.value || !ownerId) return
  if (!speciesName.value) return
  const data = await createPatient({
    name: name.value,
    species: speciesName.value,
    owner_id: ownerId,
    species_id: speciesId.value,
    birth_date: birth_date.value ? birth_date.value.toISOString().split('T')[0] : null,
    sex: sex.value,
  })
  name.value = ''
  speciesId.value = null
  sex.value = 'unknown'
  birth_date.value = null
  if (data?.id) {
    await router.push(`/patients/${data.id}`)
    return
  }
  loadPatients()
}

onMounted(() => {
  loadPatients()
  // loadOwners();
  loadSpecies()
})

watch([filterName, filterSpeciesId, filterOwner], () => {
  if (typeof filterOwner.value === 'string') return
  loadPatients({ first: 0, rows: rows.value })
})
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Patients</h2>
    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="name" placeholder="Name" />
        <Dropdown
          v-model="speciesId"
          :options="speciesOptions"
          optionLabel="name"
          optionValue="id"
          placeholder="Select species"
        />
        <Dropdown
          v-model="sex"
          :options="sexOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select sex"
        />
        <DatePicker v-model="birth_date" placeholder="Birth Date" showIcon />
        <AutoComplete
          v-model="selectedOwner"
          :suggestions="ownerSuggestions"
          optionLabel="label"
          @complete="searchOwners"
          dropdown
          forceSelection
          placeholder="Search owner"
        />
        <Button label="Add Patient" @click="addPatient" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="filterName" placeholder="Filter name" />
        <Dropdown
          v-model="filterSpeciesId"
          :options="speciesOptions"
          optionLabel="name"
          optionValue="id"
          placeholder="Filter species"
          showClear
        />
        <AutoComplete
          v-model="filterOwner"
          :suggestions="filterOwnerSuggestions"
          optionLabel="label"
          @complete="searchFilterOwners"
          dropdown
          forceSelection
          placeholder="Filter owner"
        />
        <Button label="Reset" severity="secondary" @click="resetFilters" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <DataTable
        :value="patients"
        dataKey="id"
        lazy
        paginator
        :rows="rows"
        :totalRecords="totalRecords"
        :loading="loading"
        @page="loadPatients"
        @row-click="(e) => router.push(`/patients/${e.data.id}`)"
      >
        <Column field="name" header="Name">
          <template #body="{ data }">
            <span class="text-primary cursor-pointer">
              {{ data.name }}
            </span>
          </template>
        </Column>
        <Column field="species" header="Species" />
        <Column field="birth_date" header="Birth Date">
          <template #body="{ data }">
            {{ data.birth_date || '-' }}
          </template>
        </Column>
        <Column header="Owner">
          <template #body="{ data }">
            {{ data.owner?.first_name }} {{ data.owner?.last_name }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
