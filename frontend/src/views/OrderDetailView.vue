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
const selectedTestIds = ref<number[]>([]);
const selectedServiceIds = ref<number[]>([]);
const orderComment = ref("");

const expandedOrders = ref<Record<number, boolean>>({});

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

async function collectSpecimen(specimenId: number) {
  await api.patch(`/specimens/${specimenId}/collect`, { collected: true });
  load();
}

onMounted(load);
</script>

<template>
  <div v-if="patient">
    <h2>Order #{{ order.id }} [Status: {{ order.status || "N/A" }}]</h2>
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
        <div v-if="order.test_ids.length > 0">
          <b>Tests & Results:</b><br />
          <div v-for="tid in order.test_ids" :key="tid">
            🧪 {{ tests.find((t) => t.id === tid)?.name || tid }}:
            <span
              v-for="r in order.results.filter((res) => res.test_id === tid)"
              :key="r.id"
            >
              Value: {{ r.value || "N/A" }} {{ r.units || "" }} | Flags:
              {{ r.flags || "-" }} | {{ r.specimen_id }} Specimen Status:
              {{ r.specimen_status || "N" }}
              <button
                v-if="r.specimen_status !== 'C'"
                @click="collectSpecimen(r.specimen_id)"
              >
                Collect
              </button>
              | Verified: {{ r.verified }}
            </span>
          </div>
        </div>
        <br />
      </div>
      <div v-if="order.service_ids.length > 0">
        <b>Services:</b><br />
        <span v-for="sid in order.service_ids" :key="sid">
          🩺 {{ services.find((s) => s.id === sid)?.name || sid }}<br />
        </span>

        <p>Comment: {{ order.comment || "N/A" }}</p>
      </div>
    </div>

    <!-- <pre>{{ order }}</pre> -->
  </div>
</template>
