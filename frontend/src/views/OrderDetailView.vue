<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../api/http";

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
  const testsRes = await api.get(`/tests`);
  tests.value = testsRes.data;

  const servicesRes = await api.get(`/services`);
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

</script>

<template>
  <div v-if="patient">
    <h2>Order #{{ order.id }} {{ order.archived ? "[archived]" : "" }}</h2>
    Created: {{ new Date(order.created_at).toLocaleString() }}

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

    <div
      v-if="order.id"
      style="border: 1px solid #ccc; padding: 8px 8px 0px; margin: 8px 0"
    >
      <div>
        <b>Specimens:</b><br />
        <div v-for="s in order.specimens" :key="s.specimen_id">
          🧪 {{ s.specimen_id }} | Status: {{ s.status }}
        </div>
        <br />
      </div>
      <div>
        <b>Test Runs & Results:</b><br />
        <div v-for="run in order.test_runs" :key="run.id">
          🔬 {{ testLabel(run.test_catalog_id) }} | Barcode:
          {{ run.specimen_id }} | Status: {{ run.status }} | Specimen Status:
          {{ specimenStatus(run.specimen_id) }}
          <button
            @click="collectSpecimen(run.specimen_id)"
            :disabled="specimenStatus(run.specimen_id) === 'COLLECTED'"
          >
            Collect
          </button>
          <div v-if="run.results && run.results.length > 0">
            <div v-for="r in run.results" :key="r.id">
              Value: {{ r.value || "N/A" }} {{ r.units || "" }} | Flags:
              {{ r.flags || "-" }} | Completed:
              {{ r.completed_at ? new Date(r.completed_at).toLocaleString() : "N/A" }}
              | Verified: {{ r.verified }}
            </div>
          </div>
          <div v-else>No results yet</div>
        </div>
        <br />
      </div>
      <div>
        <b>Services:</b><br />
        <div v-for="sr in order.service_runs" :key="sr.id">
          🩺 {{ serviceLabel(sr.service_catalog_id) }} | Status: {{ sr.status }}
        </div>

        <p>Comment: {{ order.comment || "N/A" }}</p>
      </div>
    </div>

    <!-- <pre>{{ order }}</pre> -->
  </div>
</template>
