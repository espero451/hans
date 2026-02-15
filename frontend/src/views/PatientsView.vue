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

// Состояние пациентов
const patients = ref<any[]>([]);
const name = ref("");
const species = ref("");
const owner_id = ref<number | null>(null);
const owners = ref<any[]>([]);
const birth_date = ref<Date | null>(null);

const router = useRouter();

const speciesOptions = [
  { label: "Cat", value: "Cat" },
  { label: "Dog", value: "Dog" },
  { label: "Dinosaur", value: "Dinosaur" },
];

const ownerOptions = computed(() =>
  owners.value.map((o) => ({
    label: `${o.first_name} ${o.last_name}`,
    value: o.id,
  }))
);

// Loading patients
async function loadPatients() {
  const res = await api.get("/patients/");
  patients.value = res.data;
}

// Load owners (for selector)
async function loadOwners() {
  owners.value = await getOwners();
}

// Add patient
async function addPatient() {
  if (!name.value || !species.value || !owner_id.value) return;
  await api.post("/patients/", {
    name: name.value,
    species: species.value,
    owner_id: owner_id.value,
    birth_date: birth_date.value
      ? birth_date.value.toISOString().split("T")[0]
      : null,
  });
  name.value = "";
  species.value = "";
  owner_id.value = null;
  birth_date.value = null;

  loadPatients();
}

// Delete patient
async function deletePatient(id: number) {
  await api.delete(`/patients/${id}`);
  loadPatients();
}

// Edit pattient (should be rewrited)
async function updatePatient(id: number) {
  const newName = prompt("New name:");
  const newSpecies = prompt("New species:");
  const newOwnerId = Number(prompt("New owner ID:"));

  if (!newName || !newSpecies || !newOwnerId) return;

  await api.put(`/patients/${id}`, {
    name: newName,
    species: newSpecies,
    owner_id: newOwnerId,
  });
  loadPatients();
}

onMounted(() => {
  loadPatients();
  loadOwners();
});

function ownerLabel(ownerId: number) {
  const owner = owners.value.find((o) => o.id === ownerId);
  return owner ? `${owner.first_name} ${owner.last_name}` : ownerId;
}
</script>

<template>
  <div class="p-4 flex flex-column gap-3">
    <h2>Patients</h2>

    <div class="surface-card p-3 border-round-xl shadow-1">
      <div class="flex flex-wrap gap-2 align-items-center">
        <InputText v-model="name" placeholder="Name" />
        <Dropdown
          v-model="species"
          :options="speciesOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select species"
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
        <Column header="Actions">
          <template #body="{ data }">
            <Button
              label="Edit"
              severity="secondary"
              size="small"
              @click.stop="updatePatient(data.id)"
            />
            <Button
              label="Delete"
              severity="danger"
              size="small"
              @click.stop="deletePatient(data.id)"
              class="ml-2"
            />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
