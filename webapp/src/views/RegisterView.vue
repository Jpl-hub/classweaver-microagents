<template>
  <div class="mx-auto flex max-w-6xl flex-col gap-10 px-2 py-6 md:flex-row md:items-stretch md:px-4 lg:px-0">
    <section class="flex-1 rounded-3xl bg-gradient-to-br from-blue-600 via-indigo-600 to-slate-900 p-8 text-white shadow-2xl">
      <div class="flex flex-col gap-3">
        <p class="text-xs uppercase tracking-[0.3em] text-blue-100">Join ClassWeaver</p>
        <h1 class="text-3xl font-semibold leading-tight md:text-4xl">&#36827;&#20837;&#19968;&#20010;&#30693;&#35782;&#26080;&#38480;&#30340;&#23398;&#20064;&#31354;&#38388;</h1>
        <p class="text-slate-100">&#27880;&#20876;&#21518;&#21363;&#21487;&#21516;&#27493;&#35838;&#31243;&#12289;&#27979;&#39564;&#12289;&#21382;&#21490;&#20107;&#20214;&#19982;&#25512;&#33616;&#65292;&#20840;&#38754;&#37322;&#25918;&#20320;&#30340;&#23398;&#20064;&#24212;&#29992;&#12290;</p>
      </div>
      <div class="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div class="rounded-2xl bg-white/10 px-4 py-3 shadow-sm">&#23450;&#21046;&#21270;&#23398;&#20064;&#35745;&#21010;&#19982;&#24635;&#32467;</div>
        <div class="rounded-2xl bg-white/10 px-4 py-3 shadow-sm">&#23436;&#25972;&#30340;&#21382;&#21490;&#35760;&#24405;&#19982;&#26102;&#38388;&#32447;</div>
        <div class="rounded-2xl bg-white/10 px-4 py-3 shadow-sm">&#33258;&#23450;&#20041;&#30693;&#35782;&#24211;&#19982;&#26234;&#33021;&#25512;&#33616;</div>
        <div class="rounded-2xl bg-white/10 px-4 py-3 shadow-sm">&#22810;&#20154;&#22330;&#26223;&#36866;&#37197;&#65292;&#36328;&#31471;&#21487;&#29992;</div>
      </div>
    </section>

    <section class="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-100">
      <header class="space-y-2">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Create account</p>
        <h2 class="text-2xl font-semibold text-slate-900">&#27880;&#20876;&#26032;&#36134;&#21495;</h2>
        <p class="text-sm text-slate-600">&#21019;&#24314;&#19968;&#20010;&#23646;&#20110;&#20320;&#30340;&#23398;&#20064;&#31354;&#38388;&#65292;&#24320;&#22987;&#35268;&#21010;&#12289;&#25512;&#33616;&#12289;&#25171;&#21360;&#19982;&#27979;&#39564;&#12290;</p>
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
          <label class="text-sm font-medium text-slate-700" for="email">&#37038;&#31665;</label>
          <input
            id="email"
            v-model="email"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
            type="email"
            name="email"
            autocomplete="email"
            placeholder="可选"
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
            autocomplete="new-password"
            required
            minlength="8"
          />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium text-slate-700" for="confirm">&#30830;&#35748;&#23494;&#30721;</label>
          <input
            id="confirm"
            v-model="confirmPassword"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
            type="password"
            name="confirm-password"
            autocomplete="new-password"
            required
          />
        </div>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{{ errorMessage }}</p>

        <button
          type="submit"
          class="flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="submitting"
        >
          {{ submitting ? "&#27880;&#20876;&#20013;..." : "&#23436;&#25104;&#27880;&#20876;" }}
        </button>

        <p class="text-center text-sm text-slate-600">
          &#24050;&#26377;&#36134;&#21495;&#65311;
          <RouterLink class="font-semibold text-slate-900 underline-offset-4 hover:underline" to="/login">&#30452;&#25509;&#30331;&#24405;</RouterLink>
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
const { signUp } = useAuth();

const username = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");
const submitting = ref(false);

const onSubmit = async () => {
  if (submitting.value) return;
  if (password.value !== confirmPassword.value) {
    errorMessage.value = "两次密码不一致";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";

  try {
    await signUp({ username: username.value.trim(), password: password.value, email: email.value.trim() || undefined });
    const redirect = (route.query.redirect as string) || "/";
    await router.replace(redirect);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "注册失败，请稍后重试";
  } finally {
    submitting.value = false;
  }
};
</script>
