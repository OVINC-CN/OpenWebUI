# Open-WebUI 布局改造与功能增强方案

## 1. 目标 (Objective)

将 Open-WebUI 的现有双栏布局（左侧菜单栏，右侧对话界面）改造为三栏布局（左侧菜单栏，中间对话界面，右侧结果预览面板）。此举旨在将AI智能体的思考过程与最终的结构化输出分离，优化用户体验。预览面板将通过按钮控制显隐，其内容由AI返回的特定数据流动态填充。

## 2. 方案概述 (High-Level Plan)

本次改造将遵循以下核心策略：

- **布局调整**: 使用 CSS Grid 在应用的主布局文件中实现左、中、右三栏结构。
- **组件化**: 创建一个全新的 Svelte 组件 `ResultPreview.svelte` 用于展示预览内容。
- **状态管理**: 利用 Svelte 5 的 `$state` rune 来管理预览面板的可见性 (`showPreview`) 和内容 (`previewContent`)，确保状态的响应式更新。
- **数据流解析**: 修改现有的聊天数据流处理逻辑，通过约定的特殊标记 (`[PREVIEW_START]` 和 `[PREVIEW_END]`) 对流式数据进行解析和分发，决定数据应在对话面板还是预览面板中展示。

## 3. 详细步骤 (Detailed Steps)

### 3.1. 布局修改 (Layout Modification)

- **目标文件**: `open-webui/src/routes/(app)/+layout.svelte`
- **操作**:
  1. 定位到包含 `<slot />` 的主容器 `div`。
  2. 应用 CSS Grid 布局，定义一个类似 `grid-template-columns: auto 1fr auto;` 的样式，来创建三栏。
  3. 将新的 `ResultPreview` 组件放置在右侧栏。

- **伪代码示例**:

```html
<script>
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import ResultPreview from '$lib/components/chat/ResultPreview.svelte';
  import { showPreview, previewContent } from '$lib/stores'; // 假设状态存在store中
</script>

<div class="main-layout" style="display: grid; grid-template-columns: auto 1fr {$showPreview ? '400px' : '0'}; transition: grid-template-columns 0.3s;">
  <Sidebar />

  <main>
    <slot />
  </main>

  {#if $showPreview}
    <ResultPreview content={$previewContent} />
  {/if}
</div>
```

### 3.2. 状态管理 (State Management)

- **目标位置**: 为了全局访问，建议在 `open-webui/src/lib/stores/index.ts` 中创建或修改。
- **操作**:
  1. 定义并导出用于控制预览面板的 `$state` 变量。

- **代码示例 (`index.ts`):**

```typescript
import { $state } from 'svelte';

// true 表示默认显示预览面板
export const showPreview = $state(true);

// 用于存储预览面板的内容
export const previewContent = $state('');

// 用于控制数据流向, 'chat' 或 'preview'
export const streamTarget = $state('chat');
```

### 3.3. 创建结果预览组件 (Create Result Preview Component)

- **新文件**: `open-webui/src/lib/components/chat/ResultPreview.svelte`
- **操作**:
  1. 创建一个新的 Svelte 组件。
  2. 组件接收 `content` 字符串作为 prop。
  3. 组件内部可以渲染 Markdown 或其他富文本格式。

- **代码示例 (`ResultPreview.svelte`):**

```html
<script lang="ts">
  import { marked } from 'marked'; // 假设使用 marked 渲染 markdown

  let { content } = $props();
</script>

<div class="preview-panel">
  <div class="preview-header">
    <span>结果预览</span>
  </div>
  <div class="preview-content">
    {@html marked(content)}
  </div>
</div>

<style>
  .preview-panel {
    border-left: 1px solid #ccc;
    padding: 1rem;
    background-color: #f9f9f9;
  }
  /* 其他样式 */
</style>
```

### 3.4. 实现切换按钮 (Implement Toggle Button)

- **目标文件**: 聊天窗口的头部或工具栏组件 (例如 `ChatHeader.svelte`，需确认具体文件名)。
- **操作**:
  1. 导入 `showPreview` 状态。
  2. 添加一个按钮，其 `onclick` 事件用于修改 `showPreview` 的值。
  3. 按钮的图标或文本根据 `showPreview` 的当前值变化。

- **代码示例 (在某个Header组件中):**

```html
<script lang="ts">
  import { showPreview } from '$lib/stores';
  import Icon from '$lib/components/common/Icon.svelte'; // 假设有Icon组件

  function togglePreview() {
    showPreview = !showPreview;
  }
</script>

<button on:click={togglePreview} title="切换预览面板">
  <Icon name={showPreview ? 'panel-right-close' : 'panel-right-open'} />
</button>
```

### 3.5. 数据流处理 (Stream Handling)

- **目标文件**: `open-webui/src/lib/apis/chats/index.ts` (或处理流式响应的核心函数)。
- **操作**:
  1. 在处理服务器发送事件 (SSE) 的函数内部，对接收到的数据块 (chunk) 进行解析。
  2. 使用 `streamTarget` 状态来动态切换数据追加的目标。

- **伪代码示例 (在 `chats/index.ts` 的流处理函数中):**

```typescript
import { previewContent, streamTarget } from '$lib/stores';

// ... 在处理流的函数内部 ...
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  let chunk = decoder.decode(value);

  if (chunk.includes('[PREVIEW_START]')) {
    streamTarget = 'preview';
    chunk = chunk.replace('[PREVIEW_START]', ''); // 移除标记
  }
  if (chunk.includes('[PREVIEW_END]')) {
    streamTarget = 'chat';
    chunk = chunk.replace('[PREVIEW_END]', ''); // 移除标记
  }

  if (streamTarget === 'preview') {
    previewContent += chunk;
  } else {
    // 将 chunk 追加到主聊天内容的逻辑
    // updateChatContent(chunk);
  }
}
```

## 4. 风险与备选方案 (Risks and Alternatives)

- **主要风险**:
  - **定位数据流处理逻辑**: `open-webui/src/lib/apis/chats/index.ts` 是一个合理的猜测，但实际处理逻辑可能分散在其他 utils 或 workers 中。需要通过代码搜索和调试来精确定位。
  - **组件间状态传递**: 如果组件层级比预想的复杂，单纯的 props 传递可能变得繁琐。Svelte 的上下文（Context API）或我们已经采用的 Stores 是解决此问题的有效方案。
- **备选方案**:
  - 如果在流中解析标记过于复杂或影响性能，可以考虑另一种方案：AI 在一次响应中返回一个包含 `thinking` 和 `result` 两个字段的完整 JSON 对象。前端接收到这个对象后，将 `thinking` 部分渲染到聊天窗口，`result` 部分渲染到预览面板。但这会牺牲流式输出的实时性。 