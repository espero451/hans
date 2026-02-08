<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import api from "../api/http";
import Button from "primevue/button";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Dropdown from "primevue/dropdown";
import Textarea from "primevue/textarea";
import Card from "primevue/card";

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

const specimenTypeOptions = computed(() =>
  specimenOptions.value.map((s) => ({
    label: `${s.name} (${s.code})`,
    value: s.id,
  }))
);

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
  <div class="p-4 flex flex-column gap-3">
    <h2>Settings</h2>

    <!-- <pre>{{ specimenOptions }}</pre> -->

    <!-- ================= TESTS ================= -->

    <section>
      <Card>
        <template #title>Tests</template>
        <template #content>
          <div class="flex flex-wrap gap-2 align-items-center mb-2">
            <InputText v-model="newTestCode" placeholder="Test Code" />
            <Dropdown
              v-model="newTestSpecimenTypeId"
              :options="specimenTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Specimen"
            />
            <InputText v-model="newTestDescription" placeholder="Description" />
            <InputNumber v-model="newTestPrice" placeholder="Price" />
            <Button label="Add" @click="addTest" />
          </div>

          <DataTable :value="tests" dataKey="id" stripedRows class="mt-2">
            <Column field="id" header="ID" />
            <Column field="code" header="Code" />
            <Column field="specimen_type_id" header="Specimen Type" />
            <Column field="price" header="Price" />
            <Column header="Actions">
              <template #body="{ data }">
                <Button
                  label="Delete"
                  severity="danger"
                  size="small"
                  @click="deleteTest(data.id).then(loadTests)"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- ================= SPECIMENS ================= -->

    <section>
      <Card>
        <template #title>Specimens</template>
        <template #content>
          <div class="flex flex-wrap gap-2 align-items-center mb-2">
            <InputText v-model="newSpecimenCode" placeholder="Specimen Code" />
            <InputText v-model="newSpecimenName" placeholder="Name" />
            <InputText v-model="newSpecimenTube" placeholder="Tube" />
            <Textarea v-model="newSpecimenDesc" placeholder="Description" />
            <Button label="Add" @click="addSpecimen" />
          </div>

          <DataTable :value="specimens" dataKey="id" stripedRows class="mt-2">
            <Column field="id" header="ID" />
            <Column field="code" header="Code" />
            <Column field="name" header="Name" />
            <Column field="tube" header="Tube" />
            <Column field="description" header="Description" />
            <Column header="Actions">
              <template #body="{ data }">
                <Button
                  label="Delete"
                  severity="danger"
                  size="small"
                  @click="deleteSpecimen(data.id).then(loadSpecimens)"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- ================= SERVICES ================= -->

    <section>
      <Card>
        <template #title>Services</template>
        <template #content>
          <div class="flex flex-wrap gap-2 align-items-center mb-2">
            <InputText v-model="newServiceName" placeholder="Service Name" />
            <Textarea v-model="newServiceDesc" placeholder="Description" />
            <InputNumber v-model="newServicePrice" placeholder="Price" />
            <Button label="Add" @click="addService" />
          </div>

          <DataTable :value="services" dataKey="id" stripedRows class="mt-2">
            <Column field="name" header="Name" />
            <Column field="description" header="Description" />
            <Column field="price" header="Price" />
            <Column header="Actions">
              <template #body="{ data }">
                <Button
                  label="Delete"
                  severity="danger"
                  size="small"
                  @click="deleteService(data.id).then(loadServices)"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>
  </div>
</template>
