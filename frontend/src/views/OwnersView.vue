<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { createOwner, deleteOwner, getOwnersPage, updateOwner } from '../api/owners'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'

interface Owner {
  id: number
  first_name: string
  last_name: string
  email?: string | null
  phone?: string | null
}

const owners = ref<Owner[]>([])
const totalRecords = ref(0)
const rows = ref(50)
const loading = ref(false)
const first_name = ref('')
const last_name = ref('')
const email = ref('')
const phone = ref('')
const filterFirstName = ref('')
const filterLastName = ref('')
const filterEmail = ref('')
const filterPhone = ref('')
let filterTimer: ReturnType<typeof setTimeout> | null = null

// Edit mode
const editingId = ref<number | null>(null)
const editFirstName = ref('')
const editLastName = ref('')
const editEmail = ref('')
const editPhone = ref('')

async function load(event?: any) {
  const skip = event?.first ?? 0
  const limit = event?.rows ?? rows.value
  loading.value = true
  try {
    const params: any = { skip, limit }
    if (filterFirstName.value.trim()) {
      params.first_name = filterFirstName.value.trim()
    }
    if (filterLastName.value.trim()) {
      params.last_name = filterLastName.value.trim()
    }
    if (filterEmail.value.trim()) {
      params.email = filterEmail.value.trim()
    }
    if (filterPhone.value.trim()) {
      params.phone = filterPhone.value.trim()
    }
    const data = await getOwnersPage(params)
    owners.value = data.items
    totalRecords.value = data.total
  } finally {
    loading.value = false
  }
}

function reloadFromFirstPage() {
  load({ first: 0, rows: rows.value })
}

function resetFilters() {
  filterFirstName.value = ''
  filterLastName.value = ''
  filterEmail.value = ''
  filterPhone.value = ''
  reloadFromFirstPage()
}

async function addOwner() {
  const fName = first_name.value.trim()
  const lName = last_name.value.trim()

  if (!fName || !lName) {
    alert('First name and Last name are required')
    return
  }

  await createOwner({
    first_name: fName,
    last_name: lName,
    email: email.value.trim() || null,
    phone: phone.value.trim() || null,
  })

  first_name.value = ''
  last_name.value = ''
  email.value = ''
  phone.value = ''
  reloadFromFirstPage()
}

function startEdit(owner: Owner) {
  editingId.value = owner.id
  editFirstName.value = owner.first_name
  editLastName.value = owner.last_name
  editEmail.value = owner.email || ''
  editPhone.value = owner.phone || ''
}

async function saveEdit(ownerId: number) {
  await updateOwner(ownerId, {
    first_name: editFirstName.value,
    last_name: editLastName.value,
    email: editEmail.value || null,
    phone: editPhone.value || null,
  })
  editingId.value = null
  reloadFromFirstPage()
}

watch([filterFirstName, filterLastName, filterEmail, filterPhone], () => {
  if (filterTimer) {
    clearTimeout(filterTimer)
  }
  filterTimer = setTimeout(() => {
    reloadFromFirstPage()
  }, 250)
})

onMounted(() => {
  load({ first: 0, rows: rows.value })
})
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Owners</h2>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="first_name" placeholder="First name" />
        <InputText v-model="last_name" placeholder="Last name" />
        <InputText v-model="email" placeholder="Email" />
        <InputText v-model="phone" placeholder="Phone" />
        <Button label="Add" @click="addOwner" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="filterFirstName" placeholder="Filter first name" />
        <InputText v-model="filterLastName" placeholder="Filter last name" />
        <InputText v-model="filterEmail" placeholder="Filter email" />
        <InputText v-model="filterPhone" placeholder="Filter phone" />
        <Button label="Reset" severity="secondary" @click="resetFilters" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <DataTable
        :value="owners"
        dataKey="id"
        lazy
        paginator
        :rows="rows"
        :totalRecords="totalRecords"
        :loading="loading"
        @page="load"
      >
        <Column header="Owner">
          <template #body="{ data }">
            <div v-if="editingId === data.id" class="flex gap-2">
              <InputText v-model="editFirstName" placeholder="First name" />
              <InputText v-model="editLastName" placeholder="Last name" />
            </div>
            <span v-else>{{ data.first_name }} {{ data.last_name }}</span>
          </template>
        </Column>
        <Column header="E-mail">
          <template #body="{ data }">
            <div v-if="editingId === data.id">
              <InputText v-model="editEmail" placeholder="Email" />
            </div>
            <span v-else>{{ data.email || '-' }}</span>
          </template>
        </Column>
        <Column header="Phone">
          <template #body="{ data }">
            <div v-if="editingId === data.id">
              <InputText v-model="editPhone" placeholder="Phone" />
            </div>
            <span v-else>{{ data.phone || '-' }}</span>
          </template>
        </Column>
        <Column header="Actions">
          <template #body="{ data }">
            <div v-if="editingId === data.id" class="flex gap-2">
              <Button label="Save" size="small" severity="success" @click="saveEdit(data.id)" />
              <Button label="Cancel" size="small" severity="secondary" @click="editingId = null" />
            </div>
            <div v-else class="flex gap-2">
              <Button
                label="Edit"
                size="small"
                severity="secondary"
                @click.stop="startEdit(data)"
              />
              <Button
                label="Delete"
                size="small"
                severity="danger"
                @click="deleteOwner(data.id).then(reloadFromFirstPage)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
