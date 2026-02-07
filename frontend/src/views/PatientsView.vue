<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getOwners } from "../api/owners";
import api from "../api/http";

// Состояние пациентов
const patients = ref<any[]>([]);
const name = ref("");
const species = ref("");
const owner_id = ref<number | null>(null);
const owners = ref<any[]>([]);
const birth_date = ref<string | null>(null);

// Loading patients
async function loadPatients() {
  const res = await api.get("/patients");
  patients.value = res.data;
}

// Load owners (for selector)
async function loadOwners() {
  owners.value = await getOwners();
}

// Add patient
async function addPatient() {
  if (!name.value || !species.value || !owner_id.value) return;
  await api.post("/patients", {
    name: name.value,
    species: species.value,
    owner_id: owner_id.value,
    birth_date: birth_date.value || null,
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
</script>

<template>
  <div>
    <h2>Patients</h2>

    <div class="form" style="margin-bottom: 16px">
      <input v-model="name" placeholder="Name" />
      <select v-model="species">
        <option disabled value="">Select species</option>
        <option>Cat</option>
        <option>Dog</option>
        <option>Dinosaur</option>
      </select>
      <input type="date" v-model="birth_date" placeholder="Birth Date" />
      <select v-model="owner_id">
        <option disabled value="">Select owner</option>
        <option v-for="o in owners" :key="o.id" :value="o.id">
          {{ o.first_name }} {{ o.last_name }}
        </option>
      </select>
      <button @click="addPatient">Add Patient</button>
    </div>

    <!-- Patients table -->
    <div
      class="patients-table"
      style="display: flex; flex-direction: column; gap: 4px"
    >
      <div
        class="table-header"
        style="
          display: flex;
          font-weight: bold;
          padding: 4px;
          border-bottom: 1px solid #ccc;
        "
      >
        <div style="flex: 1">Name</div>
        <div style="flex: 1">Species</div>
        <div style="flex: 1">Birth Date</div>
        <div style="flex: 1">Owner</div>
        <div style="flex: 1">Actions</div>
      </div>

      <!-- Patients rows -->
      <div
        v-for="p in patients"
        :key="p.id"
        class="table-row"
        style="
          display: flex;
          padding: 4px;
          border-bottom: 1px solid #eee;
          cursor: pointer;
        "
        @click="router.push(`/patients/${p.id}`)"
      >
        <div style="flex: 1">
          <a :href="`/patients/${p.id}`">{{ p.name }}</a>
        </div>
        <div style="flex: 1">{{ p.species }}</div>
        <div style="flex: 1">{{ p.birth_date || "-" }}</div>
        <div style="flex: 1">{{ p.owner_id }}</div>
        <div style="flex: 1">
          <button @click.stop="updatePatient(p.id)">Edit</button>&nbsp;
          <button @click.stop="deletePatient(p.id)">x</button>
        </div>
      </div>
    </div>
  </div>
</template>
