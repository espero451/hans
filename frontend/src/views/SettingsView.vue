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
const tubes = ref<any[]>([]);
const specimens = ref<any[]>([]);
const services = ref<any[]>([]);
const users = ref<any[]>([]);

// "Add" forms
const newTestCode = ref("");
const newTestSpecimenTypeId = ref<number | null>(null);
const newTestDescription = ref("");
const newTestPrice = ref<number | null>(null);

const newTubeCode = ref("");
const newTubeName = ref("");
const newTubeDesc = ref("");

const newSpecimenCode = ref("");
const newSpecimenName = ref("");
const newSpecimenTubeId = ref<number | null>(null);
const newSpecimenType = ref("");
const newSpecimenDesc = ref("");

const newServiceName = ref("");
const newServiceDesc = ref("");
const newServicePrice = ref<number | null>(null);
const newUserUsername = ref("");
const newUserEmail = ref("");
const newUserRole = ref<string | null>(null);
const newUserPassword = ref("");
const userRoleOptions = ref([
  { label: "admin", value: "admin" },
  { label: "staff", value: "staff" },
  { label: "owner", value: "owner" },
]);

// Edit mode - Tests
const editingTestId = ref<number | null>(null);
const editTestCode = ref("");
const editTestDescription = ref("");
const editTestPrice = ref<number | null>(null);
const editTestSpecimenTypeId = ref<number | null>(null);

// Edit mode - Tubes
const editingTubeId = ref<number | null>(null);
const editTubeCode = ref("");
const editTubeName = ref("");
const editTubeDesc = ref("");

// Edit mode - Specimens
const editingSpecimenId = ref<number | null>(null);
const editSpecimenCode = ref("");
const editSpecimenName = ref("");
const editSpecimenType = ref("");
const editSpecimenTubeId = ref<number | null>(null);
const editSpecimenDesc = ref("");

// Edit mode - Services
const editingServiceId = ref<number | null>(null);
const editServiceName = ref("");
const editServiceDesc = ref("");
const editServicePrice = ref<number | null>(null);

// List of existed tubes for specimen setup
const tubeOptions = ref<any[]>([]);

const tubeTypeOptions = computed(() =>
  tubeOptions.value.map((tub) => ({
    label: `${tub.name} (${tub.code})`,
    value: tub.id,
  }))
);

// List of existed specimens for test setup
const specimenOptions = ref<any[]>([]);

const specimenTypeOptions = computed(() =>
  specimenOptions.value.map((s) => ({
    label: `${s.name} (${s.code})`,
    value: s.id,
  }))
);

const specimenTypeNameById = computed(() => {
  const map = new Map<number, string>();
  for (const s of specimenOptions.value) {
    map.set(s.id, s.name);
  }
  return map;
});

// ---------- Load data ----------
async function loadTests() {
  const res = await api.get("/tests/");
  tests.value = res.data;
}

async function loadTubes() {
  const res = await api.get("/tubes/");
  tubes.value = res.data;
  tubeOptions.value = res.data;
}

async function loadSpecimens() {
  const res = await api.get("/specimens/");
  specimens.value = res.data;
  specimenOptions.value = res.data;
}

async function loadServices() {
  const res = await api.get("/services/");
  services.value = res.data;
}

async function loadUsers() {
  const res = await api.get("/settings/users/");
  users.value = res.data;
}

async function loadAll() {
  await Promise.all([loadTests(), loadTubes(), loadSpecimens(), loadServices()]);
}

// ---------- Add handlers ----------

async function addTest() {
  if (
    !newTestCode.value ||
    newTestSpecimenTypeId.value === null ||
    newTestPrice.value === null
  )
    return;

  await api.post("/tests/", {
    code: newTestCode.value,
    description: newTestDescription.value,
    price: newTestPrice.value,
    specimen_type_id: newTestSpecimenTypeId.value,
  });

  await loadTests();
}

async function addTube() {
  if (
    !newTubeCode.value ||
    !newTubeName.value
  )
    return;

  await api.post("/tubes/", {
    code: newTubeCode.value,
    name: newTubeName.value,
    description: newTubeDesc.value,
  });
  newTubeCode.value = "";
  newTubeName.value = "";
  newTubeDesc.value = "";

  await loadTubes();
}

async function addSpecimen() {
  if (
    !newSpecimenCode.value ||
    !newSpecimenName.value ||
    !newSpecimenTubeId.value ||
    !newSpecimenType.value
  )
    return;

  await api.post("/specimens/", {
    code: newSpecimenCode.value,
    name: newSpecimenName.value,
    tube_type_id: newSpecimenTubeId.value,
    type: newSpecimenType.value,
    description: newSpecimenDesc.value,
  });

  newSpecimenCode.value = "";
  newSpecimenName.value = "";
  newSpecimenTubeId.value = null;
  newSpecimenType.value = "";
  newSpecimenDesc.value = "";

  await loadSpecimens();
}

async function addService() {
  if (!newServiceName.value) return;

  await api.post("/services/", {
    name: newServiceName.value,
    description: newServiceDesc.value,
    price: newServicePrice.value,
  });
  newServiceName.value = "";
  newServiceDesc.value = "";
  newServicePrice.value = null;

  await loadServices();
}

function startEditTest(test: any) {
  editingTestId.value = test.id;
  editTestCode.value = test.code || "";
  editTestDescription.value = test.description || "";
  editTestPrice.value = test.price ?? null;
  editTestSpecimenTypeId.value = test.specimen_type_id ?? null;
}

async function saveEditTest(testId: number) {
  if (
    !editTestCode.value ||
    editTestSpecimenTypeId.value === null ||
    editTestPrice.value === null
  )
    return;

  await api.put(`/tests/${testId}`, {
    code: editTestCode.value,
    description: editTestDescription.value || null,
    price: editTestPrice.value,
    specimen_type_id: editTestSpecimenTypeId.value,
  });
  editingTestId.value = null;
  await loadTests();
}

function startEditTube(tube: any) {
  editingTubeId.value = tube.id;
  editTubeCode.value = tube.code || "";
  editTubeName.value = tube.name || "";
  editTubeDesc.value = tube.description || "";
}

async function saveEditTube(tubeId: number) {
  if (!editTubeCode.value || !editTubeName.value) return;

  await api.put(`/tubes/${tubeId}`, {
    code: editTubeCode.value,
    name: editTubeName.value,
    description: editTubeDesc.value || null,
  });
  editingTubeId.value = null;
  await loadTubes();
}

function startEditSpecimen(specimen: any) {
  editingSpecimenId.value = specimen.id;
  editSpecimenCode.value = specimen.code || "";
  editSpecimenName.value = specimen.name || "";
  editSpecimenType.value = specimen.type || "";
  editSpecimenTubeId.value = specimen.tube_type_id ?? null;
  editSpecimenDesc.value = specimen.description || "";
}

async function saveEditSpecimen(specimenId: number) {
  if (
    !editSpecimenCode.value ||
    !editSpecimenName.value ||
    !editSpecimenType.value ||
    editSpecimenTubeId.value === null
  )
    return;

  await api.put(`/specimens/${specimenId}`, {
    code: editSpecimenCode.value,
    name: editSpecimenName.value,
    type: editSpecimenType.value,
    tube_type_id: editSpecimenTubeId.value,
    description: editSpecimenDesc.value || null,
  });
  editingSpecimenId.value = null;
  await loadSpecimens();
}

function startEditService(service: any) {
  editingServiceId.value = service.id;
  editServiceName.value = service.name || "";
  editServiceDesc.value = service.description || "";
  editServicePrice.value = service.price ?? null;
}

async function saveEditService(serviceId: number) {
  if (!editServiceName.value || editServicePrice.value === null) return;

  await api.put(`/services/${serviceId}`, {
    name: editServiceName.value,
    description: editServiceDesc.value || null,
    price: editServicePrice.value,
  });
  editingServiceId.value = null;
  await loadServices();
}

async function addUser() {
  if (
    !newUserUsername.value ||
    !newUserEmail.value ||
    !newUserRole.value ||
    !newUserPassword.value
  )
    return;

  await api.post("/settings/users/", {
    username: newUserUsername.value,
    email: newUserEmail.value,
    role: newUserRole.value,
    password: newUserPassword.value,
  });

  newUserUsername.value = "";
  newUserEmail.value = "";
  newUserRole.value = null;
  newUserPassword.value = "";
  await loadUsers();
}

onMounted(loadAll);
onMounted(loadUsers);

// ---------- Delete handlers ----------
async function deleteTest(id: number) {
  await api.delete(`/tests/${id}`);
}

async function deleteTube(id: number) {
  await api.delete(`/tubes/${id}`);
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
          <div class="flex flex-wrap gap-2 align-items-center mb-2 w-full">
            <InputText v-model="newTestCode" placeholder="Test Code" class="flex-1 min-w-0" />
            <Dropdown
              v-model="newTestSpecimenTypeId"
              :options="specimenTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Specimen"
              class="flex-1 min-w-0"
            />
            <InputText v-model="newTestDescription" placeholder="Description" class="flex-1 min-w-0" />
            <InputNumber v-model="newTestPrice" placeholder="Price" class="flex-1 min-w-0" />
            <Button label="Add" @click="addTest" class="ml-auto" />
          </div>

          <DataTable :value="tests" dataKey="id" class="mt-2 w-full">
            <!-- <Column field="id" header="ID" /> -->
            <Column field="code" header="Code">
              <template #body="{ data }">
                <div v-if="editingTestId === data.id">
                  <InputText v-model="editTestCode" placeholder="Code" />
                </div>
                <span v-else>{{ data.code }}</span>
              </template>
            </Column>
            <Column field="specimen_type_id" header="Specimen Type">
              <template #body="{ data }">
                <div v-if="editingTestId === data.id">
                  <Dropdown
                    v-model="editTestSpecimenTypeId"
                    :options="specimenTypeOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select Specimen"
                  />
                </div>
                <span v-else>{{ specimenTypeNameById.get(data.specimen_type_id) || "-" }}</span>
              </template>
            </Column>
            <Column field="description" header="Description">
              <template #body="{ data }">
                <div v-if="editingTestId === data.id">
                  <InputText v-model="editTestDescription" placeholder="Description" />
                </div>
                <span v-else>{{ data.description || "-" }}</span>
              </template>
            </Column>
            <Column field="price" header="Price">
              <template #body="{ data }">
                <div v-if="editingTestId === data.id">
                  <InputNumber v-model="editTestPrice" placeholder="Price" />
                </div>
                <span v-else>{{ data.price }}</span>
              </template>
            </Column>
            <Column header="Actions" style="width: 1%; white-space: nowrap;">
              <template #body="{ data }">
                <div v-if="editingTestId === data.id" class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Save"
                    size="small"
                    severity="success"
                    @click="saveEditTest(data.id)"
                  />
                  <Button
                    label="Cancel"
                    size="small"
                    severity="secondary"
                    @click="editingTestId = null"
                  />
                </div>
                <div v-else class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Edit"
                    severity="secondary"
                    size="small"
                    @click.stop="startEditTest(data)"
                  />
                  <Button
                    label="Delete"
                    severity="danger"
                    size="small"
                    @click="deleteTest(data.id).then(loadTests)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- ================= TUBES ================= -->

    <section>
      <Card>
        <template #title>Tubes</template>
        <template #content>
          <div class="flex flex-wrap gap-2 align-items-center mb-2 w-full">
            <InputText v-model="newTubeCode" placeholder="Tube Code" class="flex-1 min-w-0" />
            <InputText v-model="newTubeName" placeholder="Name" class="flex-1 min-w-0" />
            <InputText v-model="newTubeDesc" placeholder="Description" class="flex-1 min-w-0" />
            <Button label="Add" @click="addTube" class="ml-auto" />
          </div>

          <DataTable :value="tubes" dataKey="id" class="mt-2 w-full">
            <!-- <Column field="id" header="ID" /> -->
            <Column field="code" header="Code">
              <template #body="{ data }">
                <div v-if="editingTubeId === data.id">
                  <InputText v-model="editTubeCode" placeholder="Code" />
                </div>
                <span v-else>{{ data.code }}</span>
              </template>
            </Column>
            <Column field="name" header="Name">
              <template #body="{ data }">
                <div v-if="editingTubeId === data.id">
                  <InputText v-model="editTubeName" placeholder="Name" />
                </div>
                <span v-else>{{ data.name }}</span>
              </template>
            </Column>
            <Column field="description" header="Description">
              <template #body="{ data }">
                <div v-if="editingTubeId === data.id">
                  <InputText v-model="editTubeDesc" placeholder="Description" />
                </div>
                <span v-else>{{ data.description || "-" }}</span>
              </template>
            </Column>
            <Column header="Actions" style="width: 1%; white-space: nowrap;">
              <template #body="{ data }">
                <div v-if="editingTubeId === data.id" class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Save"
                    size="small"
                    severity="success"
                    @click="saveEditTube(data.id)"
                  />
                  <Button
                    label="Cancel"
                    size="small"
                    severity="secondary"
                    @click="editingTubeId = null"
                  />
                </div>
                <div v-else class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Edit"
                    severity="secondary"
                    size="small"
                    @click.stop="startEditTube(data)"
                  />
                  <Button
                    label="Delete"
                    severity="danger"
                    size="small"
                    @click="deleteTube(data.id).then(loadTubes)"
                  />
                </div>
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
            <Dropdown
              v-model="newSpecimenTubeId"
              :options="tubeTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Tube"
            />
            <InputText v-model="newSpecimenType" placeholder="Type" />
            <InputText v-model="newSpecimenDesc" placeholder="Description" />
            <Button label="Add" @click="addSpecimen" />
          </div>

          <DataTable :value="specimens" dataKey="id" class="mt-2 w-full">
            <!-- <Column field="id" header="ID" /> -->
            <Column field="code" header="Code">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id">
                  <InputText v-model="editSpecimenCode" placeholder="Code" />
                </div>
                <span v-else>{{ data.code }}</span>
              </template>
            </Column>
            <Column field="name" header="Name">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id">
                  <InputText v-model="editSpecimenName" placeholder="Name" />
                </div>
                <span v-else>{{ data.name }}</span>
              </template>
            </Column>
            <Column field="type" header="Type">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id">
                  <InputText v-model="editSpecimenType" placeholder="Type" />
                </div>
                <span v-else>{{ data.type }}</span>
              </template>
            </Column>
            <Column field="tube_type_id" header="Tube">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id">
                  <Dropdown
                    v-model="editSpecimenTubeId"
                    :options="tubeTypeOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select Tube"
                  />
                </div>
                <span v-else>{{ data.tube_type_id }}</span>
              </template>
            </Column>
            <Column field="description" header="Description">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id">
                  <InputText v-model="editSpecimenDesc" placeholder="Description" />
                </div>
                <span v-else>{{ data.description || "-" }}</span>
              </template>
            </Column>
            <Column header="Actions" style="width: 1%; white-space: nowrap;">
              <template #body="{ data }">
                <div v-if="editingSpecimenId === data.id" class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Save"
                    size="small"
                    severity="success"
                    @click="saveEditSpecimen(data.id)"
                  />
                  <Button
                    label="Cancel"
                    size="small"
                    severity="secondary"
                    @click="editingSpecimenId = null"
                  />
                </div>
                <div v-else class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Edit"
                    severity="secondary"
                    size="small"
                    @click.stop="startEditSpecimen(data)"
                  />
                  <Button
                    label="Delete"
                    severity="danger"
                    size="small"
                    @click="deleteSpecimen(data.id).then(loadSpecimens)"
                  />
                </div>
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
          <div class="flex flex-wrap gap-2 align-items-center mb-2 w-full">
            <InputText v-model="newServiceName" placeholder="Service Name" class="flex-1 min-w-0" />
            <InputText v-model="newServiceDesc" placeholder="Description" class="flex-1 min-w-0" />
            <InputNumber v-model="newServicePrice" placeholder="Price" class="flex-1 min-w-0" />
            <Button label="Add" @click="addService" class="ml-auto" />
          </div>

          <DataTable :value="services" dataKey="id" class="mt-2 w-full">
            <Column field="name" header="Name">
              <template #body="{ data }">
                <div v-if="editingServiceId === data.id">
                  <InputText v-model="editServiceName" placeholder="Name" />
                </div>
                <span v-else>{{ data.name }}</span>
              </template>
            </Column>
            <Column field="description" header="Description">
              <template #body="{ data }">
                <div v-if="editingServiceId === data.id">
                  <InputText v-model="editServiceDesc" placeholder="Description" />
                </div>
                <span v-else>{{ data.description || "-" }}</span>
              </template>
            </Column>
            <Column field="price" header="Price">
              <template #body="{ data }">
                <div v-if="editingServiceId === data.id">
                  <InputNumber v-model="editServicePrice" placeholder="Price" />
                </div>
                <span v-else>{{ data.price }}</span>
              </template>
            </Column>
            <Column header="Actions" style="width: 1%; white-space: nowrap;">
              <template #body="{ data }">
                <div v-if="editingServiceId === data.id" class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Save"
                    size="small"
                    severity="success"
                    @click="saveEditService(data.id)"
                  />
                  <Button
                    label="Cancel"
                    size="small"
                    severity="secondary"
                    @click="editingServiceId = null"
                  />
                </div>
                <div v-else class="flex gap-2 justify-content-end w-full">
                  <Button
                    label="Edit"
                    severity="secondary"
                    size="small"
                    @click.stop="startEditService(data)"
                  />
                  <Button
                    label="Delete"
                    severity="danger"
                    size="small"
                    @click="deleteService(data.id).then(loadServices)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- ================= USERS ================= -->

    <section>
      <Card>
        <template #title>Users</template>
        <template #content>
          <div class="flex flex-wrap gap-2 align-items-center mb-2 w-full">
            <InputText v-model="newUserUsername" placeholder="Username" class="flex-1 min-w-0" />
            <InputText v-model="newUserEmail" placeholder="Email" class="flex-1 min-w-0" />
            <Dropdown
              v-model="newUserRole"
              :options="userRoleOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Role"
              class="flex-1 min-w-0"
            />
            <InputText v-model="newUserPassword" type="password" placeholder="Password" class="flex-1 min-w-0" />
            <Button label="Add" @click="addUser" class="ml-auto" />
          </div>

          <DataTable :value="users" dataKey="id" class="mt-2 w-full">
            <Column field="username" header="Username" />
            <Column field="email" header="Email" />
            <Column field="role" header="Role" />
          </DataTable>
        </template>
      </Card>
    </section>
  </div>
</template>
