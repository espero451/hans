<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  getOwners,
  createOwner,
  deleteOwner,
  updateOwner,
} from "../api/owners";

interface Owner {
  id: number;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
}

// const owners = ref<any[]>([])
const owners = ref<Owner[]>([]);
const first_name = ref("");
const last_name = ref("");
const email = ref("");
const phone = ref("");

// Edit mode
const editingId = ref<number | null>(null);
const editFirstName = ref("");
const editLastName = ref("");
const editEmail = ref("");
const editPhone = ref("");

async function load() {
  owners.value = await getOwners();
}

async function addOwner() {
  const fName = first_name.value.trim();
  const lName = last_name.value.trim();

  if (!fName || !lName) {
    alert("First name and Last name are required");
    return;
  }

  await createOwner({
    first_name: fName,
    last_name: lName,
    email: email.value.trim() || null,
    phone: phone.value.trim() || null,
  });

  first_name.value = "";
  last_name.value = "";
  email.value = "";
  phone.value = "";
  load();
}

function startEdit(owner: Owner) {
  editingId.value = owner.id;
  editFirstName.value = owner.first_name;
  editLastName.value = owner.last_name;
  editEmail.value = owner.email || "";
  editPhone.value = owner.phone || "";
}

async function saveEdit(ownerId: number) {
  await updateOwner(ownerId, {
    first_name: editFirstName.value,
    last_name: editLastName.value,
    email: editEmail.value || null,
    phone: editPhone.value || null,
  });
  editingId.value = null;
  load();
}

onMounted(load);
</script>

<template>
  <div>
    <h2>Owners</h2>

    <div style="margin-bottom: 16px">
      <input v-model="first_name" placeholder="First name" />
      <input v-model="last_name" placeholder="Last name" />
      <input v-model="email" placeholder="Email" />
      <input v-model="phone" placeholder="Phone" />
      <button @click="addOwner">Add</button>
    </div>

    <div
      class="owners-table"
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
        <div style="flex: 1">Owner</div>
        <div style="flex: 1">E-mail</div>
        <div style="flex: 1">Phone</div>
        <!-- <div style="flex:1">ID</div> -->
        <div style="flex: 1">Actions</div>
      </div>

      <div
        v-for="o in owners"
        :key="o.id"
        class="table-row"
        style="display: flex; padding: 4px; border-bottom: 1px solid #eee"
      >
        <template v-if="editingId === o.id">
          <div style="flex: 1">
            <input v-model="editFirstName" placeholder="First name" />
            <input v-model="editLastName" placeholder="Last name" />
          </div>
          <div style="flex: 1">
            <input v-model="editEmail" placeholder="Email" />
          </div>
          <div style="flex: 1">
            <input v-model="editPhone" placeholder="Phone" />
          </div>
          <div style="flex: 1">
            <button @click="saveEdit(o.id)">💾</button>&nbsp;
            <button @click="editingId = null">Cancel</button>
          </div>
        </template>
        <template v-else>
          <div style="flex: 1">{{ o.first_name }} {{ o.last_name }}</div>
          <div style="flex: 1">
            <span v-if="o.email">{{ o.email }}</span>
          </div>
          <div style="flex: 1">
            <span v-if="o.phone">{{ o.phone }}</span>
          </div>
          <!-- <div style="flex:1">{{ p.owner_id }}</div> -->
          <div style="flex: 1">
            <button @click.stop="startEdit(o)">Edit</button>&nbsp;
            <button @click="deleteOwner(o.id).then(load)">🗙</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
