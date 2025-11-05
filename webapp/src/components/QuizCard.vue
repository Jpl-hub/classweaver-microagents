<template>
  <article class="rounded border border-slate-200 bg-white p-4 shadow-sm space-y-2">
    <header class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-slate-800">{{ question.question }}</h2>
      <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ difficultyText }}</span>
    </header>
    <ul class="space-y-1">
      <li v-for="(label, key) in question.options" :key="key">
        <label class="inline-flex w-full items-center gap-3 rounded border border-transparent px-2 py-1 transition hover:border-slate-300 hover:bg-slate-50">
          <input
            type="radio"
            :name="question.id"
            :value="key"
            :checked="modelValue === key"
            :disabled="readonly"
            @change="() => onSelect(key)"
          />
          <span class="flex-1 text-left text-sm text-slate-700">
            <strong class="mr-2">{{ key }}.</strong>{{ label }}
          </span>
        </label>
      </li>
    </ul>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { QuizQuestion } from "../types";

interface Props {
  question: QuizQuestion;
  modelValue?: string;
  readonly?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  readonly: true,
  modelValue: "",
});

const difficultyText = computed(() => {
  const labels: Record<string, string> = {
    easy: "简单",
    medium: "中等",
    hard: "困难",
  };
  const raw = props.question.difficulty ?? "";
  const key = typeof raw === "string" ? raw.toLowerCase() : "";
  const fallback = typeof raw === "string" && raw ? raw : "未知";
  return labels[key] ?? fallback;
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

function onSelect(value: string) {
  if (props.readonly) {
    return;
  }
  emit("update:modelValue", value);
}
</script>
