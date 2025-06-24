<script lang="ts">
  import { marked } from 'marked';
  export let content = '';
</script>

<div class="preview-panel prose dark:prose-invert min-h-full min-w-0 flex flex-col h-full bg-gray-50 dark:bg-gray-850 border-l border-gray-200 dark:border-gray-700">
  <div class="p-4 font-semibold text-lg border-b border-gray-200 dark:border-gray-700">
    <span>结果预览</span>
  </div>
  <div class="p-4 flex-grow overflow-y-auto min-w-0">
    {@html marked(content)}
  </div>
</div>

<style>
  .preview-panel {
    border-left: 1px solid var(--border-color, #ccc);
    padding: 0;
    background-color: var(--background-color, #f9f9f9);
    display: flex;
    flex-direction: column;
    height: 100%;
    min-width: 320px;
    max-width: 480px;
  }
  .preview-header {
    font-weight: bold;
    margin-bottom: 1rem;
  }
  .preview-content {
    flex: 1;
    overflow-y: auto;
  }
</style> 