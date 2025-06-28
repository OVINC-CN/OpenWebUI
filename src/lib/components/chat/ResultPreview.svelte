<script lang="ts">
  import { marked } from 'marked';
  // mock数据
  export let content = '';
  // 气泡mock
  let bubbles = [
    {
      id: 'bubble-1',
      title: '思考过程',
      text: '开始修改任务规划',
      highlight: true
    },
    {
      id: 'bubble-2',
      title: '搜索结果',
      text: '搜索2025中国重点大学学术声誉排名/国际交流/研究生录取/公务员考取率',
      highlight: false
    }
  ];
  let selectedId = '';
  function selectBubble(id) {
    selectedId = id;
  }
</script>

<div class="preview-panel ai-preview flex flex-col h-full min-h-0 w-full max-w-full">
  <div class="preview-header">
    <span>智能体工作流</span>
  </div>
  <div class="preview-content flex flex-col gap-0 flex-1 min-h-0 h-full w-full max-w-full relative justify-center">
    {#each bubbles as bubble, idx (bubble.id)}
      <div
        class="ai-bubble-card {selectedId === bubble.id ? 'ai-bubble-selected' : ''}"
        id={`preview-bubble-${bubble.id}`}
        on:click={() => {
          selectBubble(bubble.id);
          const previewId = `preview-bubble-${bubble.id}`;
          const messageId = `chat-bubble-${bubble.id}`;
          console.log('preview bubble clicked', bubble.id, previewId, messageId);
          window.dispatchEvent(new CustomEvent('preview-bubble-click', { detail: { previewId, messageId } }));
        }}
        tabindex="0"
      >
        <div class="ai-bubble-title">{bubble.title}</div>
        <div class="ai-bubble-text">{bubble.text}</div>
        <div class="bubble-anchor" id={bubble.id + '-anchor'}></div>
      </div>
      {#if idx < bubbles.length - 1}
        <!-- 竖直虚线连线，高度自适应 -->
        <div class="bubble-dashed-line flex-shrink-0"></div>
      {/if}
    {/each}
  </div>
</div>

<style>
.preview-panel.ai-preview {
  border-left: 2px solid #e0e7ef;
  background: linear-gradient(135deg, #f9fafb 60%, #e0e7ef 100%);
  box-shadow: -4px 0 32px 0 rgba(80,120,255,0.10);
  min-width: 340px;
  /* max-width: 480px; */
  width: 100%;
  max-width: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.preview-header {
  font-weight: 700;
  font-size: 1.18rem;
  padding: 1.5rem 2rem 0.8rem 2rem;
  color: #222;
  letter-spacing: 0.02em;
  border-bottom: 1.5px solid #e0e7ef;
  background: transparent;
}
.preview-content {
  flex: 1;
  overflow-y: auto;
  position: relative;
  min-height: 0;
  height: 100%;
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 3.5rem;
  padding-bottom: 3.5rem;
}
.ai-bubble-card {
  background: #fff;
  border-radius: 1.5rem;
  box-shadow: 0 4px 32px 0 rgba(80,120,255,0.10);
  padding: 1.5rem 2rem 1.5rem 1.5rem;
  margin: 0;
  position: relative;
  min-width: 220px;
  max-width: 90%;
  border: 2.5px solid #e5e7eb;
  transition: border 0.3s, box-shadow 0.3s;
  cursor: pointer;
  z-index: 2;
  outline: none;
}
.ai-bubble-card:focus {
  box-shadow: 0 0 0 2px #a78bfa44;
}
.ai-bubble-selected {
  border: 2.5px solid transparent;
  background-clip: padding-box, border-box;
  background-origin: padding-box, border-box;
  background-image: linear-gradient(#fff, #fff), linear-gradient(90deg, #a78bfa, #38bdf8 80%);
  box-shadow: 0 8px 40px 0 #a78bfa44, 0 2px 16px 0 #38bdf844;
}
.ai-bubble-title {
  font-size: 1.12rem;
  font-weight: 700;
  color: #6366f1;
  margin-bottom: 0.4rem;
  letter-spacing: 0.01em;
}
.ai-bubble-text {
  font-size: 1.02rem;
  color: #222;
  white-space: pre-line;
  line-height: 1.7;
}
.bubble-anchor {
  position: absolute;
  left: -18px;
  top: 50%;
  width: 16px;
  height: 16px;
  background: radial-gradient(circle, #a78bfa 60%, #38bdf8 100%);
  border-radius: 50%;
  transform: translateY(-50%);
  box-shadow: 0 0 16px #a78bfa88, 0 0 8px #38bdf888;
  z-index: 3;
  border: 2.5px solid #fff;
  transition: box-shadow 0.3s;
}
.ai-bubble-card:hover .bubble-anchor {
  box-shadow: 0 0 32px #38bdf8cc, 0 0 16px #a78bfa99;
}
.bubble-dashed-line {
  width: 2px;
  height: 2.5rem;
  margin: 0 auto;
  border-left: 2px dashed #a78bfa;
  opacity: 0.5;
  position: relative;
  z-index: 1;
}
</style> 