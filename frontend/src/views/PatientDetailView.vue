<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import api from "../api/http";
import Button from "primevue/button";
import Card from "primevue/card";
import Divider from "primevue/divider";
import MultiSelect from "primevue/multiselect";
import InputText from "primevue/inputtext";
import Tag from "primevue/tag";

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

const testOptions = computed(() =>
  tests.value.map((t) => ({ label: t.code || t.name, value: t.id }))
);
const serviceOptions = computed(() =>
  services.value.map((s) => ({ label: s.name, value: s.id }))
);

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
  const testsRes = await api.get(`/tests/`);
  tests.value = testsRes.data;

  const servicesRes = await api.get(`/services/`);
  services.value = servicesRes.data;
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
  <div v-if="patient" class="p-4 flex flex-column gap-3">
    <Card>
      <template #title>
        {{ patient.name }} <Tag :value="patient.species" />
      </template>
      <template #content>
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
              <div v-for="run in o.test_runs" :key="run.id">
                🔬 {{ testLabel(run.test_catalog_id) }} | Barcode:
                {{ run.specimen_id }} |
                <Tag :value="run.status" severity="warning" /> |
                Specimen:
                <Tag :value="specimenStatus(o, run.specimen_id)" severity="info" />
                <div v-if="run.results && run.results.length > 0">
                  <div v-for="r in run.results" :key="r.id">
                    Value: {{ r.value || "N/A" }} {{ r.units || "-" }} | Flags:
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
              </div>
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
