<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getOwners, createOwner, deleteOwner, updateOwner } from '../api/owners'
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
const first_name = ref('')
const last_name = ref('')
const email = ref('')
const phone = ref('')

// Edit mode
const editingId = ref<number | null>(null)
const editFirstName = ref('')
const editLastName = ref('')
const editEmail = ref('')
const editPhone = ref('')

async function load() {
  owners.value = await getOwners()
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
  load()
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
  load()
}

onMounted(load)
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
      <DataTable :value="owners" dataKey="id">
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
                @click="deleteOwner(data.id).then(load)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
