<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../api/http";
import Button from "primevue/button";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Dropdown from "primevue/dropdown";
import DatePicker from "primevue/datepicker";
import Tag from "primevue/tag";

const router = useRouter();

const orders = ref<any[]>([]);
const patients = ref<any[]>([]);
const owners = ref<any[]>([]);

const statusFilter = ref<"active" | "resulted" | "archived">("active");
const selectedDate = ref<Date | null>(null);
const selectedOwner = ref<number | null>(null);
const selectedPatient = ref<number | null>(null);

const statusOptions = [
  { label: "Active", value: "active" },
  { label: "Resulted", value: "resulted" },
  { label: "Archived", value: "archived" },
];

const ownerOptions = computed(() =>
  owners.value.map((o) => ({
    label: `${o.first_name} ${o.last_name}`,
    value: o.id,
  }))
);

const patientOptions = computed(() =>
  patients.value.map((p) => ({
    label: p.name,
    value: p.id,
  }))
);

const patientById = computed(
  () => new Map(patients.value.map((p) => [p.id, p]))
);
const ownerById = computed(
  () => new Map(owners.value.map((o) => [o.id, o]))
);

function orderHasResults(order: any) {
  return (order?.test_runs || []).some(
    (run: any) => Array.isArray(run.results) && run.results.length > 0
  );
}

function dateKey(input: string | Date | null) {
  if (!input) return "";
  const date = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function patientLabel(patientId: number) {
  const patient = patientById.value.get(patientId);
  return patient ? patient.name : `Patient #${patientId}`;
}

function ownerLabelForPatient(patientId: number) {
  const patient = patientById.value.get(patientId);
  if (!patient) return "Unknown";
  const owner = ownerById.value.get(patient.owner_id);
  return owner ? `${owner.first_name} ${owner.last_name}` : `Owner #${patient.owner_id}`;
}

const filteredOrders = computed(() => {
  const selectedDateKey = dateKey(selectedDate.value);
  const list = orders.value.filter((order) => {
    if (statusFilter.value === "active" && order.archived) return false;
    if (statusFilter.value === "archived" && !order.archived) return false;
    if (statusFilter.value === "resulted" && !orderHasResults(order)) return false;

    if (selectedDateKey) {
      const orderDateKey = dateKey(order.created_at);
      if (!orderDateKey || orderDateKey !== selectedDateKey) return false;
    }

    if (selectedPatient.value && order.patient_id !== selectedPatient.value) {
      return false;
    }

    if (selectedOwner.value) {
      const patient = patientById.value.get(order.patient_id);
      if (!patient || patient.owner_id !== selectedOwner.value) return false;
    }

    return true;
  });

  return list.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
});

const resultsSummary = computed(
  () => `${filteredOrders.value.length} of ${orders.value.length} orders`
);

async function loadOwners() {
  const res = await api.get("/owners");
  owners.value = res.data;
}

async function loadPatients() {
  const res = await api.get("/patients");
  patients.value = res.data;
}

async function loadOrders() {
  const orderPromises = patients.value.map(async (patient) => {
    try {
      const res = await api.get(`/patients/${patient.id}/orders`);
      return res.data;
    } catch (err) {
      console.error(`Failed to load orders for patient ${patient.id}`, err);
      return [];
    }
  });

  const ordersNested = await Promise.all(orderPromises);
  orders.value = ordersNested.flat();
}

function resetFilters() {
  statusFilter.value = "active";
  selectedDate.value = null;
  selectedOwner.value = null;
  selectedPatient.value = null;
}

onMounted(async () => {
  await Promise.all([loadOwners(), loadPatients()]);
  await loadOrders();
});
</script>

<template>
  <div class="p-4 flex flex-column gap-3">
    <h2>Orders</h2>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <Dropdown
          v-model="statusFilter"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Status"
        />
        <DatePicker
          v-model="selectedDate"
          placeholder="Filter date"
          showIcon
          showButtonBar
        />
        <Dropdown
          v-model="selectedOwner"
          :options="ownerOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Filter owner"
          showClear
        />
        <Dropdown
          v-model="selectedPatient"
          :options="patientOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Filter patient"
          showClear
        />
        <Button label="Reset" severity="secondary" @click="resetFilters" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex align-items-center justify-content-between mb-2">
        <span class="text-600">{{ resultsSummary }}</span>
      </div>
      <DataTable
        :value="filteredOrders"
        dataKey="id"
        :emptyMessage="'No orders found'"
        @row-click="(e) => router.push(`/orders/${e.data.id}`)">
        <Column header="Order">
          <template #body="{ data }">
            <a :href="`/orders/${data.id}`">#{{ data.id }}</a>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag
              :value="data.archived ? 'Archived' : 'Active'"
              :severity="data.archived ? 'secondary' : 'success'"
            />
          </template>
        </Column>
        <Column header="Results">
          <template #body="{ data }">
            <Tag
              :value="orderHasResults(data) ? 'Resulted' : 'Pending'"
              :severity="orderHasResults(data) ? 'info' : 'warning'"
            />
          </template>
        </Column>
        <Column header="Created">
          <template #body="{ data }">
            {{ new Date(data.created_at).toLocaleString() }}
          </template>
        </Column>
        <Column header="Patient">
          <template #body="{ data }">
            <a :href="`/patients/${data.patient_id}`">
              {{ patientLabel(data.patient_id) }}
            </a>
          </template>
        </Column>
        <Column header="Owner">
          <template #body="{ data }">
            {{ ownerLabelForPatient(data.patient_id) }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
