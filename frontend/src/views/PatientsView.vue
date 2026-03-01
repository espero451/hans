<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { getOwners } from "../api/owners";
import api from "../api/http";
import Button from "primevue/button";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import InputText from "primevue/inputtext";
import Dropdown from "primevue/dropdown";
import DatePicker from "primevue/datepicker";

const patients = ref<any[]>([]);
const name = ref("");
const speciesId = ref<number | null>(null);
const sex = ref("unknown");
const owner_id = ref<number | null>(null);
const owners = ref<any[]>([]);
const speciesOptions = ref<any[]>([]);
const birth_date = ref<Date | null>(null);
const sexOptions = [
  { label: "Male", value: "male" },
  { label: "Female", value: "female" },
  { label: "Unknown", value: "unknown" },
];

const router = useRouter();

const ownerOptions = computed(() =>
  owners.value.map((o) => ({
    label: `${o.first_name} ${o.last_name}`,
    value: o.id,
  }))
);
const speciesName = computed(() => {
  const selected = speciesOptions.value.find((s) => s.id === speciesId.value);
  return selected ? selected.name : "";
});

// Loading patients
async function loadPatients() {
  const res = await api.get("/patients/");
  patients.value = res.data;
}

// Load owners (for selector)
async function loadOwners() {
  owners.value = await getOwners();
}

async function loadSpecies() {
  const res = await api.get("/species/");
  speciesOptions.value = res.data;
}

// Add patient
async function addPatient() {
  if (!name.value || !speciesId.value || !owner_id.value) return;
  if (!speciesName.value) return;
  const res = await api.post("/patients/", {
    name: name.value,
    species: speciesName.value,
    species_id: speciesId.value,
    owner_id: owner_id.value,
    birth_date: birth_date.value
      ? birth_date.value.toISOString().split("T")[0]
      : null,
    sex: sex.value,
  });
  name.value = "";
  speciesId.value = null;
  sex.value = "unknown";
  owner_id.value = null;
  birth_date.value = null;

  if (res.data?.id) {
    await router.push(`/patients/${res.data.id}`);
    return;
  }

  loadPatients();
}

onMounted(() => {
  loadPatients();
  loadOwners();
  loadSpecies();
});

function ownerLabel(ownerId: number) {
  const owner = owners.value.find((o) => o.id === ownerId);
  return owner ? `${owner.first_name} ${owner.last_name}` : ownerId;
}
</script>

<template>
  <div class="flex flex-column gap-3">
    <h2>Patients</h2>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="name" placeholder="Name" />
        <Dropdown
          v-model="speciesId"
          :options="speciesOptions"
          optionLabel="name"
          optionValue="id"
          placeholder="Select species"
        />
        <Dropdown
          v-model="sex"
          :options="sexOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select sex"
        />
        <DatePicker v-model="birth_date" placeholder="Birth Date" showIcon />
        <Dropdown
          v-model="owner_id"
          :options="ownerOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select owner"
        />
        <Button label="Add Patient" @click="addPatient" />
      </div>
    </div>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <DataTable
        :value="patients"
        dataKey="id"
        @row-click="(e) => router.push(`/patients/${e.data.id}`)"
      >
        <Column field="name" header="Name">
          <template #body="{ data }">
            <a :href="`/patients/${data.id}`">{{ data.name }}</a>
          </template>
        </Column>
        <Column field="species" header="Species" />
        <Column field="birth_date" header="Birth Date">
          <template #body="{ data }">
            {{ data.birth_date || "-" }}
          </template>
        </Column>
        <Column header="Owner">
          <template #body="{ data }">
            {{ ownerLabel(data.owner_id) }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
