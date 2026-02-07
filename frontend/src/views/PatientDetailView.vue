<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../api/http";

const route = useRoute();
const patient = ref<any>(null);
const owner = ref<any>(null);
const orders = ref<any[]>([]);
const tests = ref<any[]>([]);
const services = ref<any[]>([]);
const selectedTestIds = ref<number[]>([]);
const selectedServiceIds = ref<number[]>([]);
const orderComment = ref("");

const expandedOrders = ref<Record<number, boolean>>({});

async function load() {
  const id = route.params.id;

  // patient loading
  const patientRes = await api.get(`/patients/${id}`);
  patient.value = patientRes.data;

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
  } catch (err) {
    console.error("Failed to load orders:", err);
    orders.value = [];
  }

  // tests/services loading
  const testsRes = await api.get(`/tests`);
  tests.value = testsRes.data;

  const servicesRes = await api.get(`/services`);
  services.value = servicesRes.data;
}

async function addOrder() {
  if (!selectedTestIds.value.length && !selectedServiceIds.value.length) return;

  const res = await api.post("/orders", {
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
</script>

<template>
  <div v-if="patient">
    <h2>{{ patient.name }} ({{ patient.species }})</h2>
    <p v-if="patient.breed">Breed: {{ patient.breed }}</p>
    <p v-if="patient.birth_date">Birth Date: {{ patient.birth_date }}</p>
    <p v-if="owner">
      Owner: {{ owner.first_name }} {{ owner.last_name }} ({{ owner.email }},
      {{ owner.phone }})
    </p>
    <p v-else>Loading owner...</p>

    <hr />

    <h3>Create a new order:</h3>
    <label>Tests:</label>
    <select v-model="selectedTestIds" multiple size="3">
      <option v-for="t in tests" :key="t.id" :value="t.id">{{ t.code }}</option>
    </select>

    <label style="padding-left: 50px">Services:</label>
    <select v-model="selectedServiceIds" multiple size="3">
      <option v-for="s in services" :key="s.id" :value="s.id">
        {{ s.name }}
      </option>
    </select>

    <input
      v-model="orderComment"
      placeholder="Comment"
      style="margin-left: 50px"
    />

    <button @click="addOrder">Add Order</button>

    <hr />

    <h3>Orders</h3>

    <div
      v-for="o in orders"
      :key="o.id"
      style="border: 1px solid #ccc; padding: 8px 8px 0px; margin: 8px 0"
    >
      <strong style="cursor: pointer" @click="toggleOrder(o.id)">
        Order #<a :href="`/orders/${o.id}`">{{ o.id }}</a> [Archived: {{ o.archived ? "Yes" : "No" }}] </strong
      ><br />
      Created:
      <span v-if="o.created_at">
        {{ new Date(o.created_at).toLocaleString() }}
      </span>

      <br /><br />

      <!-- <pre>{{ o }}</pre> -->

      <div v-if="expandedOrders[o.id]">
        <div>
          <b>Specimens:</b><br />
          <div v-for="s in o.specimens" :key="s.specimen_id">
            🧪 {{ s.specimen_id }} | Status: {{ s.status }}
          </div>
          <br />
        </div>
        <div>
          <b>Test Runs & Results:</b><br />
          <div v-for="run in o.test_runs" :key="run.id">
            🔬 {{ testLabel(run.test_catalog_id) }} | Barcode:
            {{ run.specimen_id }} | Status: {{ run.status }} | Specimen Status:
            {{ specimenStatus(o, run.specimen_id) }}
            <div v-if="run.results && run.results.length > 0">
              <div v-for="r in run.results" :key="r.id">
                Value: {{ r.value || "N/A" }} {{ r.units || "-" }} | Flags:
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
          <div v-for="sr in o.service_runs" :key="sr.id">
            🩺 {{ serviceLabel(sr.service_catalog_id) }} | Status: {{ sr.status }}
          </div>

          <p>Comment: {{ o.comment || "N/A" }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
