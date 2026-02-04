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
    const ordersRes = await api.get(
      `/patients/${id}/orders?_expand=specimens,results`,
    );
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
    test_ids: selectedTestIds.value,
    service_ids: selectedServiceIds.value,
    comment: orderComment.value,
  });

  // refresh orders localy
  orders.value.push(res.data);
  // clean form
  selectedTestIds.value = [];
  selectedServiceIds.value = [];
  orderComment.value = "";
}

async function collectSpecimen(resultId: number) {
  await api.patch(`/results/${resultId}/collect`);
  load();
}

onMounted(load);

function toggleOrder(orderId: number) {
  expandedOrders.value[orderId] = !expandedOrders.value[orderId];
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
      <option v-for="t in tests" :key="t.id" :value="t.id">{{ t.name }}</option>
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
        Order #<a :href="`/orders/${o.id}`">{{ o.id }}</a> [Status: {{ o.status || "N/A" }}] </strong
      ><br />
      Created:
      <span v-if="o.created_at">
        {{ new Date(o.created_at).toLocaleString() }}
      </span>

      <br /><br />

      <!-- <pre>{{ o }}</pre> -->

      <div v-if="expandedOrders[o.id]">
        <div>
          <b>Tests & Results:</b><br />
          <div v-for="tid in o.test_ids" :key="tid">
            🧪 {{ tests.find((t) => t.id === tid)?.name || tid }}:
            <span
              v-for="r in o.results.filter((res) => res.test_id === tid)"
              :key="r.id"
            >
              Value: {{ r.value || "N/A" }} {{ r.units || "-" }} | Flags:
              {{ r.flags || "-" }} | Specimen Status:
              {{ r.specimen_status || "N" }}
              <button
                v-if="r.specimen_status !== 'C'"
                @click="collectSpecimen(r.id)"
              >
                Collect
              </button>
            </span>
          </div>
          <br />
        </div>
        <div>
          <b>Services:</b><br />
          <span v-for="sid in o.service_ids" :key="sid">
            🩺 {{ services.find((s) => s.id === sid)?.name || sid }}<br />
          </span>

          <p>Comment: {{ o.comment || "N/A" }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
