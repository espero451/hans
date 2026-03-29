<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getServices, getTests } from '../api/catalogs'
import { createOrder, getPatientOrders } from '../api/orders'
import { getOwner } from '../api/owners'
import {
  getPatient,
  getPatientPhoto,
  getSpecies,
  patchPatient,
  uploadPatientPhoto as uploadPatientPhotoRequest,
} from '../api/patients'
import Button from 'primevue/button'
import Card from 'primevue/card'
// import Divider from "primevue/divider";
import MultiSelect from 'primevue/multiselect'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'

const route = useRoute()
const router = useRouter()
const patient = ref<any>(null)
const owner = ref<any>(null)
const orders = ref<any[]>([])
const tests = ref<any[]>([])
const services = ref<any[]>([])
const speciesOptions = ref<any[]>([])
const selectedTestIds = ref<number[]>([])
const selectedServiceIds = ref<number[]>([])
const orderComment = ref('')
const savingAll = ref(false)
const isEditing = ref(false)
const editablePatient = ref<any | null>(null)
const showOrderForm = ref(false)
const patientPhotoUrl = ref<string | null>(null)
const uploadingPhoto = ref(false)
const photoInput = ref<HTMLInputElement | null>(null)

const testOptions = computed(() =>
  tests.value.map((t) => ({ label: t.code || t.name, value: t.id })),
)
const serviceOptions = computed(() => services.value.map((s) => ({ label: s.name, value: s.id })))
const testLabelMap = computed(() => {
  const map = new Map<number, string>()
  tests.value.forEach((t) => {
    map.set(t.id, t.code || t.name)
  })
  return map
})
const serviceLabelMap = computed(() => {
  const map = new Map<number, string>()
  services.value.forEach((s) => {
    map.set(s.id, s.name)
  })
  return map
})
const speciesDisplayName = computed(() => {
  const speciesId = patient.value?.species_id
  if (!speciesId) return ''
  const selected = speciesOptions.value.find((s) => s.id === speciesId)
  return selected ? selected.name : ''
})
const sexOptions = [
  { label: 'Male', value: 'male' },
  { label: 'Female', value: 'female' },
  { label: 'Unknown', value: 'unknown' },
]

async function load() {
  await loadPatient()

  await Promise.all([loadOrders(), loadTests(), loadServices(), loadSpecies()])

  await loadPatientPhoto()
}

async function addOrder() {
  if (!selectedTestIds.value.length && !selectedServiceIds.value.length) return

  const data = await createOrder({
    patient_id: patient.value.id,
    test_catalog_ids: selectedTestIds.value,
    service_catalog_ids: selectedServiceIds.value,
    comment: orderComment.value,
  })

  await loadOrders()
  // clean form
  selectedTestIds.value = []
  selectedServiceIds.value = []
  orderComment.value = ''

  if (data?.id) {
    await router.push(`/orders/${data.id}`)
  }
}

function startEdit() {
  if (!patient.value) return
  editablePatient.value = {
    ...patient.value,
    species_id: patient.value?.species_id ?? null,
    birth_date: patient.value?.birth_date ? new Date(patient.value.birth_date) : null,
  }
  isEditing.value = true
}

async function savePatientAll() {
  if (!patient.value || !editablePatient.value) return
  savingAll.value = true
  try {
    const birthDate = editablePatient.value.birth_date
      ? editablePatient.value.birth_date.toISOString().split('T')[0]
      : null
    const data = await patchPatient(patient.value.id, {
      name: editablePatient.value.name || null,
      species_id: editablePatient.value.species_id ?? null,
      comment: editablePatient.value.comment || null,
      sex: editablePatient.value.sex || null,
      weight: editablePatient.value.weight ?? null,
      breed: editablePatient.value.breed || null,
      microchip_number: editablePatient.value.microchip_number || null,
      birth_date: birthDate,
    })
    patient.value = data
    isEditing.value = false
  } finally {
    savingAll.value = false
  }
}

onMounted(load)
onUnmounted(() => {
  if (patientPhotoUrl.value) {
    URL.revokeObjectURL(patientPhotoUrl.value)
    patientPhotoUrl.value = null
  }
})

function testLabel(testCatalogId: number) {
  return testLabelMap.value.get(testCatalogId) ?? testCatalogId
}

function serviceLabel(serviceCatalogId: number) {
  return serviceLabelMap.value.get(serviceCatalogId) ?? serviceCatalogId
}

async function loadPatient() {
  const id = route.params.id
  patient.value = await getPatient(String(id))
  if (patient.value.owner_id) {
    try {
      owner.value = await getOwner(patient.value.owner_id)
    } catch (err) {
      console.error('Failed to load owner:', err)
      owner.value = null
    }
  }
}

async function loadOrders() {
  if (!patient.value?.id) return
  try {
    orders.value = await getPatientOrders(patient.value.id)
  } catch (err) {
    console.error('Failed to load orders:', err)
    orders.value = []
  }
}

async function loadTests() {
  tests.value = await getTests()
}

async function loadServices() {
  services.value = await getServices()
}

async function loadSpecies() {
  speciesOptions.value = await getSpecies()
}

async function loadPatientPhoto() {
  if (!patient.value?.id) return
  try {
    const photoBlob = await getPatientPhoto(patient.value.id)
    patientPhotoUrl.value = URL.createObjectURL(photoBlob)
  } catch {
    patientPhotoUrl.value = null
  }
}

function triggerPhotoSelect() {
  photoInput.value?.click()
}

async function uploadPatientPhoto(event: Event) {
  if (!patient.value?.id) return
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadingPhoto.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    await uploadPatientPhotoRequest(patient.value.id, form)
    await loadPatientPhoto()
  } finally {
    uploadingPhoto.value = false
    input.value = ''
  }
}
</script>

<template>
  <div v-if="patient">
    <h2 class="flex align-items-center gap-2">
      <span v-if="!isEditing">{{ patient.name }}</span>
      <InputText v-else v-model="editablePatient.name" placeholder="Name" />
      <Tag v-if="!isEditing" :value="speciesDisplayName" />
      <Dropdown
        v-else
        v-model="editablePatient.species_id"
        :options="speciesOptions"
        optionLabel="name"
        optionValue="id"
        placeholder="Select species"
      />
      <Button
        :label="isEditing ? 'Save' : 'Edit patient'"
        :loading="savingAll"
        @click="isEditing ? savePatientAll() : startEdit()"
        size="small"
      />
    </h2>
    <div class="patient-layout">
      <div class="patient-left">
        <Card>
          <template #content>
            <div class="flex flex-column md:flex-row gap-4">
              <div class="flex flex-column align-items-center gap-3">
                <div class="photo-circle">
                  <img v-if="patientPhotoUrl" :src="patientPhotoUrl" alt="Patient" />
                  <div v-else class="photo-placeholder">No photo</div>
                </div>
                <div v-if="isEditing">
                  <input
                    ref="photoInput"
                    type="file"
                    accept="image/*"
                    class="hidden"
                    @change="uploadPatientPhoto"
                  />
                  <Button
                    label="Add"
                    size="small"
                    :loading="uploadingPhoto"
                    @click="triggerPhotoSelect"
                  />
                </div>
              </div>
              <div class="flex-1">
                <p v-if="owner">
                  Owner: {{ owner.first_name }} {{ owner.last_name }} ({{ owner.email }},
                  {{ owner.phone }})
                </p>
                <p v-else>Loading owner...</p>

                <div class="mt-3 flex flex-column gap-2">
                  <div class="flex flex-wrap align-items-center gap-2">
                    <label class="w-8rem">Breed</label>
                    <span v-if="!isEditing">{{ patient.breed || '-' }}</span>
                    <InputText v-else v-model="editablePatient.breed" placeholder="Breed" />
                  </div>

                  <div class="flex flex-wrap align-items-center gap-2">
                    <label class="w-8rem">Birth Date</label>
                    <span v-if="!isEditing">{{ patient.birth_date || '-' }}</span>
                    <DatePicker
                      v-else
                      v-model="editablePatient.birth_date"
                      dateFormat="yy-mm-dd"
                      placeholder="Birth date"
                      showIcon
                    />
                  </div>

                  <div class="flex flex-wrap align-items-center gap-2">
                    <label class="w-8rem">Sex</label>
                    <span v-if="!isEditing">{{ patient.sex || 'unknown' }}</span>
                    <Dropdown
                      v-else
                      v-model="editablePatient.sex"
                      :options="sexOptions"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Select sex"
                    />
                  </div>

                  <div class="flex flex-wrap align-items-center gap-2">
                    <label class="w-8rem">Weight (kg)</label>
                    <span v-if="!isEditing">{{ patient.weight ?? '-' }}</span>
                    <InputNumber
                      v-else
                      v-model="editablePatient.weight"
                      :minFractionDigits="0"
                      :maxFractionDigits="2"
                      placeholder="Weight"
                    />
                  </div>

                  <div class="flex flex-wrap align-items-center gap-2">
                    <label class="w-8rem">Microchip</label>
                    <span v-if="!isEditing">
                      {{ patient.microchip_number || '-' }}
                    </span>
                    <InputText
                      v-else
                      v-model="editablePatient.microchip_number"
                      placeholder="Microchip number"
                    />
                  </div>
                </div>

                <div class="mt-3">
                  <label class="block mb-2">Comment:</label>
                  <p v-if="!isEditing">{{ patient.comment || '-' }}</p>
                  <Textarea
                    v-else
                    v-model="editablePatient.comment"
                    rows="3"
                    autoResize
                    class="w-full"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <div class="patient-right">
        <div class="orders-header">
          <h3>Orders</h3>
          <Button label="Create a new order" size="small" @click="showOrderForm = !showOrderForm" />
        </div>

        <Card v-if="showOrderForm">
          <template #content>
            <div class="flex flex-wrap gap-2 align-items-center">
              <MultiSelect
                v-model="selectedTestIds"
                :options="testOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select tests"
                display="chip"
              />
              <MultiSelect
                v-model="selectedServiceIds"
                :options="serviceOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select services"
                display="chip"
              />
              <InputText v-model="orderComment" placeholder="Comment" />
              <Button label="Add Order" @click="addOrder" />
            </div>
          </template>
        </Card>

        <Divider v-if="showOrderForm" />

        <div v-for="o in orders" :key="o.id">
          <Card>
            <template #title>
              <span>
                Order #<a :href="`/orders/${o.id}`">{{ o.id }}</a>
              </span>
              <Tag
                :value="o.archived ? 'Archived' : 'Active'"
                :severity="o.archived ? 'secondary' : 'success'"
                style="margin-left: 0.5rem"
              />
            </template>
            <template #content>
              <div>
                Created:
                <span v-if="o.created_at">
                  {{ new Date(o.created_at).toLocaleString() }}
                </span>
              </div>

              <div style="margin-top: 1rem">
                <p>Comment: {{ o.comment || 'N/A' }}</p>

                <div class="mb-3">
                  <b>Tests:</b>&nbsp;
                  <span v-for="(run, index) in o.test_runs || []" :key="run.id">
                    {{ testLabel(run.test_catalog_id) }}
                    <span v-if="Number(index) < (o.test_runs?.length || 0) - 1"> | </span>
                  </span>
                </div>

                <div>
                  <b>Services:</b>
                  <div v-for="sr in o.service_runs" :key="sr.id">
                    🩺 {{ serviceLabel(sr.service_catalog_id) }}
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.patient-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 1.5rem;
}

.patient-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.orders-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

@media (max-width: 960px) {
  .patient-layout {
    grid-template-columns: 1fr;
  }
}

.photo-circle {
  width: 196px;
  height: 196px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #47535f;
  background: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  font-size: 12px;
  color: #6b7280;
}
</style>
