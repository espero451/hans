<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../api/http";
import Button from "primevue/button";
import Card from "primevue/card";
import Divider from "primevue/divider";
import MultiSelect from "primevue/multiselect";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Textarea from "primevue/textarea";
import Tag from "primevue/tag";
import Dropdown from "primevue/dropdown";
import DatePicker from "primevue/datepicker";

const route = useRoute();
const router = useRouter();
const patient = ref<any>(null);
const owner = ref<any>(null);
const orders = ref<any[]>([]);
const tests = ref<any[]>([]);
const services = ref<any[]>([]);
const speciesOptions = ref<any[]>([]);
const speciesId = ref<number | null>(null);
const selectedTestIds = ref<number[]>([]);
const selectedServiceIds = ref<number[]>([]);
const orderComment = ref("");
const patientComment = ref("");
const savingAll = ref(false);
const isEditing = ref(false);
const patientName = ref("");
const patientSex = ref("");
const patientWeight = ref<number | null>(null);
const patientBreed = ref("");
const patientMicrochipNumber = ref("");
const patientBirthDate = ref<Date | null>(null);
const patientPhotoUrl = ref<string | null>(null);
const uploadingPhoto = ref(false);
const photoInput = ref<HTMLInputElement | null>(null);

const expandedOrders = ref<Record<number, boolean>>({});

const testOptions = computed(() =>
  tests.value.map((t) => ({ label: t.code || t.name, value: t.id }))
);
const serviceOptions = computed(() =>
  services.value.map((s) => ({ label: s.name, value: s.id }))
);
const speciesName = computed(() => {
  const selected = speciesOptions.value.find((s) => s.id === speciesId.value);
  return selected ? selected.name : "";
});
const sexOptions = [
  { label: "Male", value: "male" },
  { label: "Female", value: "female" },
  { label: "Unknown", value: "unknown" },
];

async function load() {
  const id = route.params.id;

  // patient loading
  const patientRes = await api.get(`/patients/${id}`);
  patient.value = patientRes.data;
  patientComment.value = patient.value?.comment || "";
  patientSex.value = patient.value?.sex || "";
  patientWeight.value = patient.value?.weight ?? null;
  patientBreed.value = patient.value?.breed || "";
  patientMicrochipNumber.value = patient.value?.microchip_number || "";
  patientName.value = patient.value?.name || "";
  patientBirthDate.value = patient.value?.birth_date
    ? new Date(patient.value.birth_date)
    : null;

  // owner loading
  if (patient.value.owner_id) {
    try {
      const ownerRes = await api.get(`/owners/${patient.value.owner_id}`);
      owner.value = ownerRes.data;
    } catch (err) {
      console.error("Failed to load owner:", err);
      owner.value = null;
    }
  }

  try {
    const ordersRes = await api.get(`/patients/${id}/orders`);
    orders.value = ordersRes.data;
    expandedOrders.value = Object.fromEntries(
      orders.value.map((order) => [order.id, !order.archived])
    );
  } catch (err) {
    console.error("Failed to load orders:", err);
    orders.value = [];
    expandedOrders.value = {};
  }

  // tests/services loading
  const testsRes = await api.get(`/tests/`);
  tests.value = testsRes.data;

  const servicesRes = await api.get(`/services/`);
  services.value = servicesRes.data;

  await loadSpecies();
  await loadPatientPhoto();
}

async function addOrder() {
  if (!selectedTestIds.value.length && !selectedServiceIds.value.length) return;

  const res = await api.post("/orders/", {
    patient_id: patient.value.id,
    test_catalog_ids: selectedTestIds.value,
    service_catalog_ids: selectedServiceIds.value,
    comment: orderComment.value,
  });

  // refresh orders localy
  orders.value.push(res.data);
  // clean form
  selectedTestIds.value = [];
  selectedServiceIds.value = [];
  orderComment.value = "";

  if (res.data?.id) {
    await router.push(`/orders/${res.data.id}`);
  }
}

function startEdit() {
  if (!patient.value) return;
  patientComment.value = patient.value?.comment || "";
  patientSex.value = patient.value?.sex || "";
  patientWeight.value = patient.value?.weight ?? null;
  patientBreed.value = patient.value?.breed || "";
  patientMicrochipNumber.value = patient.value?.microchip_number || "";
  patientName.value = patient.value?.name || "";
  patientBirthDate.value = patient.value?.birth_date
    ? new Date(patient.value.birth_date)
    : null;
  syncSpeciesSelection();
  isEditing.value = true;
}

async function savePatientAll() {
  if (!patient.value) return;
  savingAll.value = true;
  try {
    const birthDate = patientBirthDate.value
      ? patientBirthDate.value.toISOString().split("T")[0]
      : null;
    const res = await api.patch(`/patients/${patient.value.id}`, {
      name: patientName.value || null,
      species: speciesName.value || null,
      species_id: speciesId.value,
      comment: patientComment.value || null,
      sex: patientSex.value || null,
      weight: patientWeight.value ?? null,
      breed: patientBreed.value || null,
      microchip_number: patientMicrochipNumber.value || null,
      birth_date: birthDate,
    });
    patient.value = res.data;
    patientComment.value = patient.value?.comment || "";
    patientSex.value = patient.value?.sex || "";
    patientWeight.value = patient.value?.weight ?? null;
    patientBreed.value = patient.value?.breed || "";
    patientMicrochipNumber.value = patient.value?.microchip_number || "";
    patientName.value = patient.value?.name || "";
    patientBirthDate.value = patient.value?.birth_date
      ? new Date(patient.value.birth_date)
      : null;
    syncSpeciesSelection();
    isEditing.value = false;
  } finally {
    savingAll.value = false;
  }
}

onMounted(load);

function toggleOrder(orderId: number) {
  expandedOrders.value[orderId] = !expandedOrders.value[orderId];
}

function testLabel(testCatalogId: number) {
  const test = tests.value.find((t) => t.id === testCatalogId);
  return test ? test.code || test.name : testCatalogId;
}

function serviceLabel(serviceCatalogId: number) {
  const service = services.value.find((s) => s.id === serviceCatalogId);
  return service ? service.name : serviceCatalogId;
}

async function loadSpecies() {
  const res = await api.get("/species/");
  speciesOptions.value = res.data;
  syncSpeciesSelection();
}

function syncSpeciesSelection() {
  if (!patient.value) return;
  const selected = speciesOptions.value.find(
    (s) => s.name === patient.value?.species
  );
  speciesId.value = selected ? selected.id : null;
}

async function loadPatientPhoto() {
  if (!patient.value?.id) return;
  if (patientPhotoUrl.value) {
    URL.revokeObjectURL(patientPhotoUrl.value);
    patientPhotoUrl.value = null;
  }
  try {
    const res = await api.get(`/patients/${patient.value.id}/photo`, {
      responseType: "blob",
    });
    patientPhotoUrl.value = URL.createObjectURL(res.data);
  } catch (err) {
    patientPhotoUrl.value = null;
  }
}

function triggerPhotoSelect() {
  photoInput.value?.click();
}

async function uploadPatientPhoto(event: Event) {
  if (!patient.value?.id) return;
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploadingPhoto.value = true;
  try {
    const form = new FormData();
    form.append("file", file);
    await api.post(`/patients/${patient.value.id}/photo`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await loadPatientPhoto();
  } finally {
    uploadingPhoto.value = false;
    input.value = "";
  }
}
</script>

<template>
  <div v-if="patient" class="p-4 flex flex-column gap-3">
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
            <h2 class="flex align-items-center gap-2">
              <span v-if="!isEditing">{{ patient.name }}</span>
              <InputText v-else v-model="patientName" placeholder="Name" />
              <Tag v-if="!isEditing" :value="patient.species" />
              <Dropdown
                v-else
                v-model="speciesId"
                :options="speciesOptions"
                optionLabel="name"
                optionValue="id"
                placeholder="Select species"
              />
            </h2>
            <p v-if="owner">
              Owner: {{ owner.first_name }} {{ owner.last_name }} ({{
                owner.email
              }}, {{ owner.phone }})
            </p>
            <p v-else>Loading owner...</p>
            <div class="mt-2">
              <Button
                :label="isEditing ? 'Save' : 'Edit patient'"
                :loading="savingAll"
                @click="isEditing ? savePatientAll() : startEdit()"
              />
            </div>
            <div class="mt-3 flex flex-column gap-2">
              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Breed</label>
                <span v-if="!isEditing">{{ patient.breed || "-" }}</span>
                <InputText v-else v-model="patientBreed" placeholder="Breed" />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Birth Date</label>
                <span v-if="!isEditing">{{ patient.birth_date || "-" }}</span>
                <DatePicker
                  v-else
                  v-model="patientBirthDate"
                  dateFormat="yy-mm-dd"
                  placeholder="Birth date"
                  showIcon
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Sex</label>
                <span v-if="!isEditing">{{ patient.sex || "unknown" }}</span>
                <Dropdown
                  v-else
                  v-model="patientSex"
                  :options="sexOptions"
                  optionLabel="label"
                  optionValue="value"
                  placeholder="Select sex"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Weight (kg)</label>
                <span v-if="!isEditing">{{ patient.weight ?? "-" }}</span>
                <InputNumber
                  v-else
                  v-model="patientWeight"
                  :minFractionDigits="0"
                  :maxFractionDigits="2"
                  placeholder="Weight"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Microchip</label>
                <span v-if="!isEditing">
                  {{ patient.microchip_number || "-" }}
                </span>
                <InputText
                  v-else
                  v-model="patientMicrochipNumber"
                  placeholder="Microchip number"
                />
              </div>
            </div>

            <div class="mt-3">
              <label class="block mb-2">Comment:</label>
              <p v-if="!isEditing">{{ patient.comment || "-" }}</p>
              <Textarea
                v-else
                v-model="patientComment"
                rows="3"
                autoResize
                class="w-full"
              />
            </div>
          </div>
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Create a new order</template>
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

    <Divider />

    <h3>Orders</h3>

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
          <Button
            label="Toggle"
            size="small"
            severity="secondary"
            style="margin-left: 0.75rem"
            @click="toggleOrder(o.id)"
          />
        </template>
        <template #content>
          <div>
            Created:
            <span v-if="o.created_at">
              {{ new Date(o.created_at).toLocaleString() }}
            </span>
          </div>

          <div v-if="expandedOrders[o.id]" style="margin-top: 1rem">
            <p>Comment: {{ o.comment || "N/A" }}</p>

            <div class="mb-3">
              <b>Test Runs:</b>
              <table class="w-full text-sm">
                <thead>
                  <tr>
                    <th class="text-left">Test</th>
                    <th class="text-left">Barcode</th>
                    <th class="text-left">Run Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="run in o.test_runs" :key="run.id">
                    <td>{{ testLabel(run.test_catalog_id) }}</td>
                    <td>{{ run.specimen_id }}</td>
                    <td><Tag :value="run.status" severity="warning" /></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div>
              <b>Services:</b>
              <div v-for="sr in o.service_runs" :key="sr.id">
                🩺 {{ serviceLabel(sr.service_catalog_id) }} |
                <Tag :value="sr.status" severity="info" />
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
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
