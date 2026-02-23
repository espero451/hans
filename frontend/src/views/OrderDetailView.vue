<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../api/http";
import Button from "primevue/button";
import Card from "primevue/card";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import Divider from "primevue/divider";

const route = useRoute();
const patient = ref<any>(null);
const owner = ref<any>(null);
const order = ref<any>(null);
const tests = ref<any[]>([]);
const services = ref<any[]>([]);

async function load() {
  const id = route.params.id;

  // order loading
  const orderRes = await api.get(`/orders/${id}`);
  order.value = orderRes.data;

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

async function collectSpecimen(specimenId: string) {
  await api.patch(`/orders/barcode/${specimenId}/collect`);
  await load();
}

// Archive the order and update only the archived flag
async function archiveOrder(id: number) {
  const res = await api.patch(`/orders/${id}/archive`);
  order.value.archived = res.data.archived;
}
</script>

<template>
  <div v-if="patient" class="p-4 flex flex-column gap-3">
    <Card>
      <template #title>
        Order #{{ order.id }}
        <Tag
          :value="order.archived ? 'Archived' : 'Active'"
          :severity="order.archived ? 'secondary' : 'success'"
          class="ml-2"
        />
        <Tag
          :value="order.urgency || 'ROUTINE'"
          :severity="urgencySeverity(order.urgency)"
          class="ml-2"
        />
        <Button
          :label="order.archived ? 'Unarchive' : 'Archive'"
          size="small"
          @click="archiveOrder(order.id)"
          class="ml-2"
        />
      </template>
      <template #content>
        <div>Created: {{ new Date(order.created_at).toLocaleString() }}</div>
        <div class="flex align-items-center gap-2">
          <span>Urgency:</span>
          <Tag
            :value="order.urgency || 'ROUTINE'"
            :severity="urgencySeverity(order.urgency)"
          />
        </div>
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

    <Card v-if="order.id">
      <template #title>Specimens</template>
      <template #content>
        <DataTable :value="order.specimens" dataKey="specimen_id">
          <Column field="specimen_id" header="Barcode" />
          <Column header="Status">
            <template #body="{ data }">
              <Tag :value="data.status" severity="info" />
            </template>
          </Column>
          <Column header="Actions">
            <template #body="{ data }">
              <Button
                label="Collect"
                size="small"
                @click="collectSpecimen(data.specimen_id)"
                :disabled="data.status === 'COLLECTED'"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Divider />

    <Card>
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
                <td><Tag :value="run.status" severity="warning" /></td>
                <td><Tag :value="specimenStatus(run.specimen_id)" severity="info" /></td>
              </tr>
              <tr>
                <td colspan="4">
                  <div v-if="run.results && run.results.length > 0" class="flex flex-column gap-2">
                    <div v-for="r in run.results" :key="r.id" class="overflow-auto">
                      <div class="inline-flex gap-2 align-items-center">
                        <span>{{ r.value || "N/A" }} {{ r.units || "" }}</span>
                        <span>Flags: {{ r.flags || "-" }}</span>
                        <span>Abnormal: {{ r.abnormal_flag || "-" }}</span>
                        <span>Verified by: {{ r.verified_by ?? "-" }}</span>
                        <span>Verified at: {{ formatDateTime(r.verified_at) }}</span>
                        <span>Comment: {{ r.comment || "-" }}</span>
                        <span>Completed: {{ formatDateTime(r.completed_at) }}</span>
                      </div>
                    </div>
                  </div>
                  <span v-else>No results yet</span>
                </td>
              </tr>
              <tr v-if="!isLastRun(index, order?.test_runs)">
                <td colspan="4">
                  <Divider class="my-2" />
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
        <p style="margin-top: 0.75rem">Comment: {{ order.comment || "N/A" }}</p>
      </template>
    </Card>
  </div>
</template>
