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
          style="margin-left: 0.5rem"
        />
        <!-- <Button
          label="Archive"
          size="small"
          @click="archiveOrder(order.id)"
          :disabled="order.archived"
        /> -->
        &nbsp;<Button
          :label="order.archived ? 'Unarchive' : 'Archive'"
          size="small"
          @click="archiveOrder(order.id)"
        />
      </template>
      <template #content>
        <div>Created: {{ new Date(order.created_at).toLocaleString() }}</div>
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
        </DataTable>
      </template>
    </Card>

    <Divider />

    <Card>
      <template #title>Test Runs & Results</template>
      <template #content>
        <DataTable :value="order.test_runs" dataKey="id">
          <Column header="Test">
            <template #body="{ data }">
              {{ testLabel(data.test_catalog_id) }}
            </template>
          </Column>
          <Column field="specimen_id" header="Barcode" />
          <Column header="Status">
            <template #body="{ data }">
              <Tag :value="data.status" severity="warning" />
            </template>
          </Column>
          <Column header="Specimen Status">
            <template #body="{ data }">
              <Tag :value="specimenStatus(data.specimen_id)" severity="info" />
            </template>
          </Column>
          <Column header="Results">
            <template #body="{ data }">
              <div v-if="data.results && data.results.length > 0">
                <div v-for="r in data.results" :key="r.id">
                  {{ r.value || "N/A" }} {{ r.units || "" }} | Flags:
                  {{ r.flags || "-" }}<br>
                  Completed:
                  {{
                    r.completed_at
                      ? new Date(r.completed_at).toLocaleString()
                      : "N/A"
                  }}
                </div>
              </div>
              <span v-else>No results yet</span>
            </template>
          </Column>
          <Column header="Actions">
            <template #body="{ data }">
              <Button
                label="Collect"
                size="small"
                @click="collectSpecimen(data.specimen_id)"
                :disabled="specimenStatus(data.specimen_id) === 'COLLECTED'"
              />
            </template>
          </Column>
        </DataTable>
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
