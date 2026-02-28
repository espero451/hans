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
const selectedTestIds = ref<number[]>([]);
const selectedServiceIds = ref<number[]>([]);
const orderComment = ref("");
const patientComment = ref("");
const savingComment = ref(false);
const patientSex = ref("");
const patientWeight = ref<number | null>(null);
const patientBreed = ref("");
const patientMicrochipNumber = ref("");
const patientBirthDate = ref<Date | null>(null);
const savingSex = ref(false);
const savingWeight = ref(false);
const savingBreed = ref(false);
const savingMicrochipNumber = ref(false);
const savingBirthDate = ref(false);
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

async function savePatientComment() {
  if (!patient.value) return;
  savingComment.value = true;
  try {
    const res = await api.patch(`/patients/${patient.value.id}`, {
      comment: patientComment.value || null,
    });
    patient.value = res.data;
    patientComment.value = patient.value?.comment || "";
  } finally {
    savingComment.value = false;
  }
}

async function savePatientSex() {
  if (!patient.value) return;
  if (!patientSex.value) return;
  savingSex.value = true;
  try {
    const res = await api.patch(`/patients/${patient.value.id}`, {
      sex: patientSex.value,
    });
    patient.value = res.data;
    patientSex.value = patient.value?.sex || "";
  } finally {
    savingSex.value = false;
  }
}

async function savePatientWeight() {
  if (!patient.value) return;
  savingWeight.value = true;
  try {
    const res = await api.patch(`/patients/${patient.value.id}`, {
      weight: patientWeight.value ?? null,
    });
    patient.value = res.data;
    patientWeight.value = patient.value?.weight ?? null;
  } finally {
    savingWeight.value = false;
  }
}

async function savePatientBreed() {
  if (!patient.value) return;
  savingBreed.value = true;
  try {
    const res = await api.patch(`/patients/${patient.value.id}`, {
      breed: patientBreed.value || null,
    });
    patient.value = res.data;
    patientBreed.value = patient.value?.breed || "";
  } finally {
    savingBreed.value = false;
  }
}

async function savePatientBirthDate() {
  if (!patient.value) return;
  savingBirthDate.value = true;
  try {
    const birthDate = patientBirthDate.value
      ? patientBirthDate.value.toISOString().split("T")[0]
      : null;
    const res = await api.patch(`/patients/${patient.value.id}`, {
      birth_date: birthDate,
    });
    patient.value = res.data;
    patientBirthDate.value = patient.value?.birth_date
      ? new Date(patient.value.birth_date)
      : null;
  } finally {
    savingBirthDate.value = false;
  }
}

async function savePatientMicrochipNumber() {
  if (!patient.value) return;
  savingMicrochipNumber.value = true;
  try {
    const res = await api.patch(`/patients/${patient.value.id}`, {
      microchip_number: patientMicrochipNumber.value || null,
    });
    patient.value = res.data;
    patientMicrochipNumber.value = patient.value?.microchip_number || "";
  } finally {
    savingMicrochipNumber.value = false;
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

function specimenStatus(order: any, specimenId: string) {
  const specimen = order?.specimens?.find(
    (s: any) => s.specimen_id === specimenId
  );
  return specimen?.status || "N/A";
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
            <div>
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
              {{ patient.name }}
              <Tag :value="patient.species" />
            </h2>
            <p v-if="owner">
              Owner: {{ owner.first_name }} {{ owner.last_name }} ({{
                owner.email
              }}, {{ owner.phone }})
            </p>
            <p v-else>Loading owner...</p>
            <div class="mt-3 flex flex-column gap-2">
              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Breed</label>
                <InputText v-model="patientBreed" placeholder="Breed" />
                <Button
                  label="Save"
                  size="small"
                  :loading="savingBreed"
                  @click="savePatientBreed"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Birth Date</label>
                <DatePicker
                  v-model="patientBirthDate"
                  dateFormat="yy-mm-dd"
                  placeholder="Birth date"
                  showIcon
                />
                <Button
                  label="Save"
                  size="small"
                  :loading="savingBirthDate"
                  @click="savePatientBirthDate"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Sex</label>
                <Dropdown
                  v-model="patientSex"
                  :options="sexOptions"
                  optionLabel="label"
                  optionValue="value"
                  placeholder="Select sex"
                />
                <Button
                  label="Save"
                  size="small"
                  :loading="savingSex"
                  @click="savePatientSex"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Weight (kg)</label>
                <InputNumber
                  v-model="patientWeight"
                  :minFractionDigits="0"
                  :maxFractionDigits="2"
                  placeholder="Weight"
                />
                <Button
                  label="Save"
                  size="small"
                  :loading="savingWeight"
                  @click="savePatientWeight"
                />
              </div>

              <div class="flex flex-wrap align-items-center gap-2">
                <label class="w-8rem">Microchip</label>
                <InputText
                  v-model="patientMicrochipNumber"
                  placeholder="Microchip number"
                />
                <Button
                  label="Save"
                  size="small"
                  :loading="savingMicrochipNumber"
                  @click="savePatientMicrochipNumber"
                />
              </div>
            </div>

            <div class="mt-3">
              <label class="block mb-2">Comment:</label>
              <Textarea
                v-model="patientComment"
                rows="3"
                autoResize
                class="w-full"
              />
              <div class="mt-2">
                <Button
                  label="Save"
                  :loading="savingComment"
                  @click="savePatientComment"
                />
              </div>
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
            <div class="mb-3">
              <b>Specimens:</b>
              <div v-for="s in o.specimens" :key="s.specimen_id">
                🧪 {{ s.specimen_id }} |
                <Tag :value="s.status" severity="info" />
              </div>
            </div>

            <div class="mb-3">
              <b>Test Runs & Results:</b>
              <table class="w-full text-sm">
                <thead>
                  <tr>
                    <th class="text-left">Test</th>
                    <th class="text-left">Barcode</th>
                    <th class="text-left">Run Status</th>
                    <th class="text-left">Specimen Status</th>
                    <th class="text-left">Results</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="run in o.test_runs" :key="run.id">
                    <td>{{ testLabel(run.test_catalog_id) }}</td>
                    <td>{{ run.specimen_id }}</td>
                    <td><Tag :value="run.status" severity="warning" /></td>
                    <td>
                      <Tag
                        :value="specimenStatus(o, run.specimen_id)"
                        severity="info"
                      />
                    </td>
                    <td>
                      <div v-if="run.results && run.results.length > 0">
                        <div v-for="r in run.results" :key="r.id">
                          {{ r.value || "N/A" }} {{ r.units || "-" }} | Flags:
                          {{ r.flags || "-" }} | Completed:
                          {{
                            r.completed_at
                              ? new Date(r.completed_at).toLocaleString()
                              : "N/A"
                          }}
                          | Verified: {{ r.verified }}
                        </div>
                      </div>
                      <div v-else>No results yet</div>
                    </td>
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

              <p>Comment: {{ o.comment || "N/A" }}</p>
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
