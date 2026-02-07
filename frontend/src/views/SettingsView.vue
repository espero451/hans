<script setup lang="ts">
import { ref, onMounted } from "vue";
import api from "../api/http";

// TODO:
// import { getTests, createTest, updateTest, deleteTest } from "../api/tests"
// import { getSpecimens, createSpecimen } from "../api/specimens"
// import { getServices, createService } from "../api/services"

const tests = ref<any[]>([]);
const specimens = ref<any[]>([]);
const services = ref<any[]>([]);

// "Add" forms
const newTestCode = ref("");
const newTestSpecimenTypeId = ref<number | null>(null);
const newTestDescription = ref("");
const newTestPrice = ref<number | null>(null);

const newSpecimenCode = ref("");
const newSpecimenName = ref("");
const newSpecimenTube = ref("");
const newSpecimenDesc = ref("");

const newServiceName = ref("");
const newServiceDesc = ref("");
const newServicePrice = ref<number | null>(null);

// List of existed specimens for test setup
const specimenOptions = ref<any[]>([]);

// ---------- Load data ----------
async function loadTests() {
  const res = await api.get("/tests");
  tests.value = res.data;
}

async function loadSpecimens() {
  const res = await api.get("/specimens");
  specimens.value = res.data;
  specimenOptions.value = res.data;
}

async function loadServices() {
  const res = await api.get("/services");
  services.value = res.data;
}

async function loadAll() {
  await Promise.all([loadTests(), loadSpecimens(), loadServices()]);
}

// ---------- Add handlers ----------

async function addTest() {
  if (
    !newTestCode.value ||
    newTestSpecimenTypeId.value === null ||
    newTestPrice.value === null
  )
    return;

  await api.post("/tests", {
    code: newTestCode.value,
    description: newTestDescription.value,
    price: newTestPrice.value,
    specimen_type_id: newTestSpecimenTypeId.value,
  });

  await loadTests();
}

async function addSpecimen() {
  if (
    !newSpecimenCode.value ||
    !newSpecimenName.value ||
    !newSpecimenTube.value
  )
    return;

  await api.post("/specimens", {
    code: newSpecimenCode.value,
    name: newSpecimenName.value,
    tube: newSpecimenTube.value,
    description: newSpecimenDesc.value,
  });
  newSpecimenCode.value = "";
  newSpecimenName.value = "";
  newSpecimenTube.value = "";
  newSpecimenDesc.value = "";

  await loadSpecimens();
}

async function addService() {
  if (!newServiceName.value) return;

  await api.post("/services", {
    name: newServiceName.value,
    description: newServiceDesc.value,
    price: newServicePrice.value,
  });
  newServiceName.value = "";
  newServiceDesc.value = "";
  newServicePrice.value = null;

  await loadServices();
}

onMounted(loadAll);

// ---------- Delete handlers ----------
async function deleteTest(id: number) {
  await api.delete(`/tests/${id}`);
}

async function deleteSpecimen(id: number) {
  await api.delete(`/specimens/${id}`);
}

async function deleteService(id: number) {
  await api.delete(`/services/${id}`);
}
</script>

<template>
  <div>
    <h2>Settings</h2>

    <!-- <pre>{{ specimenOptions }}</pre> -->

    <!-- ================= TESTS ================= -->

    <section style="margin-bottom: 24px">
      <h3>Tests</h3>
      <div style="margin-bottom: 8px">
        <input v-model="newTestCode" placeholder="Test Code" />
        <select v-model.number="newTestSpecimenTypeId">
          <option disabled :value="null">Select Specimen</option>
          <option v-for="s in specimenOptions" :key="s.id" :value="s.id">
            {{ s.name }} ({{ s.code }})
          </option>
        </select>
        <input v-model="newTestDescription" placeholder="Description" />
        <input type="number" v-model="newTestPrice" placeholder="Price" />
        <button @click="addTest">💾</button>
      </div>

      <div
        style="
          display: flex;
          flex-direction: column;
          gap: 4px;
          border: 1px solid #ccc;
          padding: 4px;
        "
      >
        <div
          style="
            display: flex;
            font-weight: bold;
            padding: 4px;
            border-bottom: 1px solid #ccc;
          "
        >
          <div style="flex: 1">ID</div>
          <div style="flex: 2">Code</div>
          <div style="flex: 2">Specimen Type</div>
          <div style="flex: 1">Price</div>
        </div>
        <div
          v-for="t in tests"
          :key="t.id"
          style="display: flex; padding: 4px; border-bottom: 1px solid #eee"
        >
          <div style="flex: 1">{{ t.id }}</div>
          <div style="flex: 2">{{ t.code }}</div>
          <div style="flex: 2">{{ t.specimen_type_id }}</div>
          <div style="flex: 1">${{ t.price }}</div>
          <div>
            <button @click="deleteTest(t.id).then(loadTests)">🗙</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= SPECIMENS ================= -->

    <section style="margin-bottom: 24px">
      <h3>Specimens</h3>
      <div style="margin-bottom: 8px">
        <input v-model="newSpecimenCode" placeholder="Specimen Code" />
        <input v-model="newSpecimenName" placeholder="Name" />
        <input v-model="newSpecimenTube" placeholder="Tube" />
        <input v-model="newSpecimenDesc" placeholder="Description" />
        <button @click="addSpecimen">💾</button>
      </div>

      <div
        style="
          display: flex;
          flex-direction: column;
          gap: 4px;
          border: 1px solid #ccc;
          padding: 4px;
        "
      >
        <div
          style="
            display: flex;
            font-weight: bold;
            padding: 4px;
            border-bottom: 1px solid #ccc;
          "
        >
          <div style="flex: 1">ID</div>
          <div style="flex: 2">Code</div>
          <div style="flex: 1">Name</div>
          <div style="flex: 1">Tube</div>
          <div style="flex: 2">Description</div>
        </div>
        <div
          v-for="s in specimens"
          :key="s.id"
          style="display: flex; padding: 4px; border-bottom: 1px solid #eee"
        >
          <div style="flex: 1">{{ s.id }}</div>
          <div style="flex: 2">{{ s.code }}</div>
          <div style="flex: 1">{{ s.name }}</div>
          <div style="flex: 1">{{ s.tube }}</div>
          <div style="flex: 2">{{ s.description }}</div>
          <div>
            <button @click="deleteSpecimen(s.id).then(loadSpecimens)">🗙</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= SERVICES ================= -->

    <section style="margin-bottom: 24px">
      <h3>Services</h3>

      <div style="margin-bottom: 8px">
        <input v-model="newServiceName" placeholder="Service Name" />
        <input v-model="newServiceDesc" placeholder="Description" />
        <input type="number" v-model="newServicePrice" placeholder="Price" />
        <button @click="addService">💾</button>
      </div>

      <div
        style="
          display: flex;
          flex-direction: column;
          gap: 4px;
          border: 1px solid #ccc;
          padding: 4px;
        "
      >
        <div
          style="
            display: flex;
            font-weight: bold;
            padding: 4px;
            border-bottom: 1px solid #ccc;
          "
        >
          <!-- <div style="flex:1">ID</div> -->
          <div style="flex: 2">Name</div>
          <div style="flex: 3">Description</div>
          <div style="flex: 1">Price</div>
          <div></div>
        </div>
        <div
          v-for="srv in services"
          :key="srv.id"
          style="display: flex; padding: 4px; border-bottom: 1px solid #eee"
        >
          <!-- <div style="flex:1">{{ srv.id }}</div> -->
          <div style="flex: 2">{{ srv.name }}</div>
          <div style="flex: 3">{{ srv.description }}</div>
          <div style="flex: 1">${{ srv.price }}</div>
          <div>
            <button @click="deleteService(srv.id).then(loadServices)">🗙</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
