import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";
import "primeicons/primeicons.css";
import "primeflex/primeflex.css";
import "./style.css";


const app = createApp(App);
app.use(router);
app.use(PrimeVue, { theme: { preset: Aura } });
app.mount("#app");

// createApp(App).use(router).mount("#app");
