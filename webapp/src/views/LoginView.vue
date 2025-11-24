<template>
  <div class="mx-auto flex max-w-6xl flex-col gap-10 px-2 py-6 md:flex-row md:items-stretch md:px-4 lg:px-0">
    <section class="flex-1 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-8 text-white shadow-2xl">
      <div class="flex flex-col gap-4">
        <p class="text-sm uppercase tracking-[0.2em] text-slate-200">ClassWeaver V3</p>
        <h1 class="text-3xl font-semibold leading-tight md:text-4xl">&#22238;&#21040;&#39640;&#25928;&#30340;&#35760;&#24405;&#19982;&#22797;&#20064;&#33410;&#22863;</h1>
        <p class="text-slate-200">
          &#30331;&#24405;&#21518;&#21487;&#24555;&#36895;&#36827;&#20837;&#23398;&#20064;&#24037;&#20316;&#21488;&#65292;&#32487;&#32493;&#20351;&#29992;&#30693;&#35782;&#24211;&#12289;&#39044;&#20064;/&#27979;&#39564;/&#24635;&#32467;&#31561;&#21151;&#33021;&#12290;
        </p>
        <ul class="mt-4 grid grid-cols-1 gap-3 text-sm text-slate-100 sm:grid-cols-2">
          <li class="flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2">&#27969;&#24335;&#22810; Agent &#35268;&#21010;&#19982;&#35760;&#24405;</li>
          <li class="flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2">&#30693;&#35782;&#24211; RAG &#21484;&#22238;&#22686;&#24378;</li>
          <li class="flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2">&#23398;&#20064;&#36827;&#31243; / &#25512;&#33616;&#19968;&#31449;&#24335;</li>
          <li class="flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2">&#35821;&#22659;&#20849;&#20139;&#30340;&#21382;&#21490;&#19982;&#20107;&#20214;</li>
        </ul>
      </div>
    </section>

    <section class="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-100">
      <header class="space-y-2">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Welcome back</p>
        <h2 class="text-2xl font-semibold text-slate-900">&#30331;&#24405;&#36134;&#21495;</h2>
        <p class="text-sm text-slate-600">&#30331;&#24405;&#21518;&#21487;&#32487;&#32493;&#21516;&#27493;&#23398;&#20064;&#35760;&#24405;&#12290;</p>
      </header>

      <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
        <div class="space-y-1">
          <label class="text-sm font-medium text-slate-700" for="username">&#29992;&#25143;&#21517;</label>
          <input
            id="username"
            v-model="username"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
            type="text"
            name="username"
            autocomplete="username"
            required
          />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium text-slate-700" for="password">&#23494;&#30721;</label>
          <input
            id="password"
            v-model="password"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
            type="password"
            name="password"
            autocomplete="current-password"
            required
          />
        </div>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{{ errorMessage }}</p>

        <button
          type="submit"
          class="flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="submitting || authLoading"
        >
          {{ submitting ? "&#30331;&#24405;&#20013;..." : "&#30331;&#24405;" }}
        </button>

        <p class="text-center text-sm text-slate-600">
          &#36824;&#27809;&#26377;&#36134;&#21495;&#65311;
          <RouterLink class="font-semibold text-slate-900 underline-offset-4 hover:underline" to="/register">&#21435;&#27880;&#20876;</RouterLink>
        </p>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "../utils/auth";

const router = useRouter();
const route = useRoute();
const { signIn, authLoading } = useAuth();

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const submitting = ref(false);

const onSubmit = async () => {
  if (submitting.value) return;
  submitting.value = true;
  errorMessage.value = "";
  try {
    await signIn({ username: username.value.trim(), password: password.value });
    const redirect = (route.query.redirect as string) || "/";
    await router.replace(redirect);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试";
  } finally {
    submitting.value = false;
  }
};
</script>
