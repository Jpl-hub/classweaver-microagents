<template>
  <pre class="max-h-96 overflow-y-auto rounded border border-slate-800 bg-slate-900 p-4 text-slate-100">
{{ formatted }}
  </pre>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ value: unknown }>();

const formatted = computed(() => {
  if (props.value === null || props.value === undefined) {
    return "// 暂无数据";
  }
  try {
    return JSON.stringify(props.value, null, 2);
  } catch (error) {
    return `// 无法渲染 JSON：${(error as Error).message}`;
  }
});
</script>

<style scoped>
pre {
  font-family: "Fira Code", "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
  font-size: 0.85rem;
}
</style>
