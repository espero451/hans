<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../api/http";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Dropdown from "primevue/dropdown";

const route = useRoute();
const patient = ref<any>(null);
const owner = ref<any>(null);
const order = ref<any>(null);
const tests = ref<any[]>([]);
const services = ref<any[]>([]);
const specimenTypes = ref<Record<number, any>>({});
const tubeTypes = ref<Record<number, any>>({});
const orderComment = ref("");
const orderUrgency = ref("ROUTINE");
const savingOrderComment = ref(false);
const savingOrderUrgency = ref(false);
const editingUrgency = ref(false);
const editingResultId = ref<number | null>(null);
const editResult = ref<any>({});
const urgencyOptions = [
  { label: "Routine", value: "ROUTINE" },
  { label: "Urgent", value: "URGENT" },
  { label: "STAT", value: "STAT" },
];

async function load() {
  const id = route.params.id;

  // order loading
  const orderRes = await api.get(`/orders/${id}`);
  order.value = orderRes.data;
  orderComment.value = order.value?.comment || "";
  orderUrgency.value = order.value?.urgency || "ROUTINE";
  await loadSpecimenTypes(order.value?.specimens);
  await loadTubeTypes();

  // patient loading
  if (order.value.patient_id) {
    try {
      const patientRes = await api.get(`/patients/${order.value.patient_id}`);
      patient.value = patientRes.data;
    } catch (err) {
      console.error("Failed to load patient:", err);
      owner.value = null;
    }
  }

  // owner loading
  const ownerRes = await api.get(`/owners/${patient.value.owner_id}`);
  owner.value = ownerRes.data;

  // tests/services loading
  const testsRes = await api.get(`/tests/`);
  tests.value = testsRes.data;

  const servicesRes = await api.get(`/services/`);
  services.value = servicesRes.data;
}

onMounted(load);

function testLabel(testCatalogId: number) {
  const test = tests.value.find((t) => t.id === testCatalogId);
  return test ? test.code || test.name : testCatalogId;
}

function serviceLabel(serviceCatalogId: number) {
  const service = services.value.find((s) => s.id === serviceCatalogId);
  return service ? service.name : serviceCatalogId;
}

async function loadSpecimenTypes(specimens?: any[]) {
  if (!Array.isArray(specimens) || specimens.length === 0) return;
  const ids = Array.from(
    new Set(
      specimens
        .map((specimen) => specimen.specimen_type_id)
        .filter((specimenTypeId: number) => Number.isFinite(specimenTypeId))
    )
  );
  const missingIds = ids.filter((id) => !specimenTypes.value[id]);
  if (missingIds.length === 0) return;
  await Promise.all(
    missingIds.map(async (specimenTypeId) => {
      const res = await api.get(`/specimens/${specimenTypeId}`);
      const data = Array.isArray(res.data) ? res.data[0] : res.data;
      if (data) {
        specimenTypes.value[specimenTypeId] = data;
      }
    })
  );
}

async function loadTubeTypes() {
  if (Object.keys(tubeTypes.value).length > 0) return;
  const res = await api.get(`/tubes/`);
  const tubeMap: Record<number, any> = {};
  for (const tube of res.data || []) {
    tubeMap[tube.id] = tube;
  }
  tubeTypes.value = tubeMap;
}

function specimenTypeCode(specimenTypeId: number) {
  return specimenTypes.value[specimenTypeId]?.code || "N/A";
}

function specimenTypeName(specimenTypeId: number) {
  return specimenTypes.value[specimenTypeId]?.name || "N/A";
}

function tubeTypeLabel(specimenTypeId: number) {
  const tubeTypeId = specimenTypes.value[specimenTypeId]?.tube_type_id;
  const tubeType = tubeTypeId ? tubeTypes.value[tubeTypeId] : null;
  return tubeType?.name || tubeType?.code || "N/A";
}

function specimenStatus(specimenId: string) {
  const specimen = order.value?.specimens?.find(
    (s: any) => s.specimen_id === specimenId
  );
  return specimen?.status || "N/A";
}

function urgencySeverity(urgency?: string) {
  if (urgency === "STAT") return "danger";
  if (urgency === "URGENT") return "warning";
  return "secondary";
}

function statusSeverity(status?: string): string {
  if (status === "RECEIVED") return "success";
  if (status === "SENT") return "warning";
  if (status === "COLLECTED") return "warning";
  if (status === "NEW") return "info";
  return "secondary";
}

function formatDateTime(value?: string | Date | null) {
  if (!value) return "N/A";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "N/A";
  return date.toLocaleString();
}

function isLastRun(index: number | string, runs: any[] | undefined) {
  const numericIndex = typeof index === "string" ? Number(index) : index;
  if (!Array.isArray(runs) || Number.isNaN(numericIndex)) return true;
  return numericIndex >= runs.length - 1;
}

function normalizeResultField(value: string | null | undefined) {
  if (value === "") return null;
  return value ?? null;
}

function startEditResult(result: any) {
  editingResultId.value = result.id;
  editResult.value = {
    value: result.value ?? "",
    units: result.units ?? "",
    flags: result.flags ?? "",
    reference_range: result.reference_range ?? "",
    abnormal_flag: result.abnormal_flag ?? "",
    comment: result.comment ?? "",
    completed_at: result.completed_at ?? "",
  };
}

function cancelEditResult() {
  editingResultId.value = null;
  editResult.value = {};
}

async function saveEditResult(resultId: number) {
  const payload = {
    value: normalizeResultField(editResult.value.value),
    units: normalizeResultField(editResult.value.units),
    flags: normalizeResultField(editResult.value.flags),
    reference_range: normalizeResultField(editResult.value.reference_range),
    abnormal_flag: normalizeResultField(editResult.value.abnormal_flag),
    comment: normalizeResultField(editResult.value.comment),
    completed_at: normalizeResultField(editResult.value.completed_at),
  };
  await api.patch(`/results/${resultId}`, payload);
  editingResultId.value = null;
  editResult.value = {};
  await load();
}

async function toggleVerifyResult(resultId: number) {
  await api.post(`/results/${resultId}/verify`);
  await load();
}

async function collectSpecimen(specimenId: string) {
  await api.patch(`/orders/barcode/${specimenId}/collect`);
  await load();
}

async function receiveSpecimen(specimenId: string) {
  await api.patch(`/orders/barcode/${specimenId}/receive`);
  await load();
}

// Archive the order and update only the archived flag
async function archiveOrder(id: number) {
  const res = await api.patch(`/orders/${id}/archive`);
  order.value.archived = res.data.archived;
}

async function saveOrderComment() {
  if (!order.value) return;
  savingOrderComment.value = true;
  try {
    const res = await api.patch(`/orders/${order.value.id}`, {
      comment: orderComment.value || null,
    });
    order.value = res.data;
    orderComment.value = order.value?.comment || "";
  } finally {
    savingOrderComment.value = false;
  }
}

async function saveOrderUrgency() {
  if (!order.value) return;
  if (!orderUrgency.value) return;
  savingOrderUrgency.value = true;
  try {
    const res = await api.patch(`/orders/${order.value.id}`, {
      urgency: orderUrgency.value,
    });
    order.value = res.data;
    orderUrgency.value = order.value?.urgency || "ROUTINE";
    editingUrgency.value = false;
  } finally {
    savingOrderUrgency.value = false;
  }
}

function startEditUrgency() {
  editingUrgency.value = true;
}

function cancelEditUrgency() {
  editingUrgency.value = false;
  orderUrgency.value = order.value?.urgency || "ROUTINE";
}
</script>

<template>
  <div v-if="patient" class="flex flex-column gap-3">
        <h2>Order #{{ order.id }}
        <Tag
          :value="order.archived ? 'Archived' : 'Active'"
          :severity="order.archived ? 'secondary' : 'success'"
          class="ml-2"
        />
        <Button
          :label="order.archived ? 'Unarchive' : 'Archive'"
          size="small"
          @click="archiveOrder(order.id)"
          class="ml-2"
        />
        </h2>
    <Card>

      <template #content>
        <p>Created: {{ new Date(order.created_at).toLocaleString() }}</p>
        <p><div class="flex align-items-center gap-2">
          <span>Urgency:</span>
          <Tag
            v-if="!editingUrgency"
            :value="order.urgency || 'ROUTINE'"
            :severity="urgencySeverity(order.urgency)"
          />
          <Dropdown
            v-else
            v-model="orderUrgency"
            :options="urgencyOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select urgency"
          />
          <Button
            v-if="!editingUrgency"
            label="Edit"
            size="small"
            severity="secondary"
            @click="startEditUrgency"
          />
          <Button
            v-else
            label="Save"
            size="small"
            :loading="savingOrderUrgency"
            @click="saveOrderUrgency"
          />
          <Button
            v-if="editingUrgency"
            label="Cancel"
            size="small"
            severity="secondary"
            @click="cancelEditUrgency"
          />
        </div></p>
        <p v-if="patient.name">
          Patient:
          <a :href="`/patients/${order.patient_id}`">{{ patient.name }}</a> ({{
            patient.species
          }})
        </p>
        <p v-if="patient.breed">Breed: {{ patient.breed }}</p>
        <p v-if="patient.birth_date">Birth Date: {{ patient.birth_date }}</p>
        <p v-if="owner">
          Owner: {{ owner.first_name }} {{ owner.last_name }} ({{ owner.email }},
          {{ owner.phone }})
        </p>
        <p v-else>Loading owner...</p>
      </template>
    </Card>

    <Card>
      <template #content>
        <label class="block mb-2">Comment:</label>
        <Textarea v-model="orderComment" rows="3" autoResize class="w-full" />
        <div class="mt-2">
          <Button
            label="Save"
            :loading="savingOrderComment"
            @click="saveOrderComment"
          />
        </div>
      </template>
    </Card>

    <Card v-if="order?.test_runs?.length">
      <template #title>Specimens</template>
      <template #content>
        <DataTable :value="order.specimens" dataKey="specimen_id">
          <Column field="specimen_id" header="Barcode" />
          <Column header="Code">
            <template #body="{ data }">
              {{ specimenTypeCode(data.specimen_type_id) }}
            </template>
          </Column>
          <Column header="Name">
            <template #body="{ data }">
              {{ specimenTypeName(data.specimen_type_id) }}
            </template>
          </Column>
          <Column header="Tube Type">
            <template #body="{ data }">
              {{ tubeTypeLabel(data.specimen_type_id) }}
            </template>
          </Column>
          <Column header="Status">
            <template #body="{ data }">
              <Tag :value="data.status" :severity="statusSeverity(data.status)" />

            </template>
          </Column>
          <Column header="Actions">
            <template #body="{ data }">
              <Button
                v-if="data.status === 'COLLECTED' || data.status === 'RECEIVED'"
                label="Receive"
                size="small"
                @click="receiveSpecimen(data.specimen_id)"
                :disabled="data.status === 'RECEIVED'"
              />
              <Button
                v-else
                label="Collect"
                size="small"
                @click="collectSpecimen(data.specimen_id)"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Card v-if="order?.test_runs?.length">
      <template #title>Test Runs & Results</template>
      <template #content>
        <table class="w-full">
          <thead>
            <tr>
              <th class="text-left">Test</th>
              <th class="text-left">Barcode</th>
              <th class="text-left">Status</th>
              <th class="text-left">Specimen Status</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(run, index) in order?.test_runs || []" :key="run.id">
              <tr>
                <td>{{ testLabel(run.test_catalog_id) }}</td>
                <td>{{ run.specimen_id }}</td>
                <td><Tag :value="run.status" :severity="statusSeverity(run.status)" /></td>
                <td><Tag :value="specimenStatus(run.specimen_id)" :severity="statusSeverity(specimenStatus(run.specimen_id))" /></td>
              </tr>
              <tr>
                <td colspan="4">
                  <div v-if="run.results && run.results.length > 0" class="overflow-auto">
                    <DataTable :value="run.results" dataKey="id" class="p-datatable-sm">
                      <Column header="Value">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.value"
                            placeholder="Value"
                          />
                          <span v-else>{{ data.value || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Units">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.units"
                            placeholder="Units"
                          />
                          <span v-else>{{ data.units || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Flags">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.flags"
                            placeholder="Flags"
                          />
                          <span v-else>{{ data.flags || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Ref Range">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.reference_range"
                            placeholder="Reference range"
                          />
                          <span v-else>{{ data.reference_range || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Abnormal">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.abnormal_flag"
                            placeholder="Abnormal flag"
                          />
                          <span v-else>{{ data.abnormal_flag || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Verified By">
                        <template #body="{ data }">
                          <span>{{ data.verified_by ?? "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Verified At">
                        <template #body="{ data }">
                          <span>{{ formatDateTime(data.verified_at) }}</span>
                        </template>
                      </Column>
                      <Column header="Comment">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.comment"
                            placeholder="Comment"
                          />
                          <span v-else>{{ data.comment || "-" }}</span>
                        </template>
                      </Column>
                      <Column header="Completed">
                        <template #body="{ data }">
                          <InputText
                            v-if="editingResultId === data.id"
                            v-model="editResult.completed_at"
                            placeholder="Completed at"
                          />
                          <span v-else>{{ formatDateTime(data.completed_at) }}</span>
                        </template>
                      </Column>
                      <Column header="Actions">
                        <template #body="{ data }">
                          <div v-if="editingResultId === data.id" class="flex gap-2">
                            <Button
                              label="Save"
                              size="small"
                              severity="success"
                              @click.stop="saveEditResult(data.id)"
                            />
                            <Button
                              label="Cancel"
                              size="small"
                              severity="secondary"
                              @click.stop="cancelEditResult"
                            />
                          </div>
                          <div v-else class="flex gap-2">
                            <Button
                              :label="data.verified ? 'Unverify' : 'Verify'"
                              size="small"
                              severity="info"
                              @click.stop="toggleVerifyResult(data.id)"
                            />
                            <Button
                              label="Edit"
                              size="small"
                              severity="secondary"
                              @click.stop="startEditResult(data)"
                            />
                          </div>
                        </template>
                      </Column>
                    </DataTable>
                  </div>
                  <span v-else>No results yet</span>
                </td>
              </tr>
              <tr v-if="!isLastRun(index, order?.test_runs)">
                <td colspan="4">
                  &nbsp;
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </template>
    </Card>

    <Card v-if="order?.service_runs?.length">
      <template #title>Services</template>
      <template #content>
        <DataTable :value="order.service_runs" dataKey="id">
          <Column header="Service">
            <template #body="{ data }">
              {{ serviceLabel(data.service_catalog_id) }}
            </template>
          </Column>
          <Column header="Status">
            <template #body="{ data }">
              <Tag :value="data.status" severity="info" />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

  </div>

</template>

<style scoped>
.tag-yellow {
  background: #fde047 !important;
  border-color: #eab308 !important;
  color: #713f12 !important;
}
</style>