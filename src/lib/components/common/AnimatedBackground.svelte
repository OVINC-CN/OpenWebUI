<script>
  import { onMount } from 'svelte';

  // LLM图标SVG数据
  const icons = [
    // OpenAI
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0734a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>
    </svg>`,
    
    // Google (Gemini) - Updated with better icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2M21 9V7L12 1L3 7V9L12 15L21 9M12 18.5C18.9 20.4 22 22 22 22S18.9 20.4 12 18.5C5.1 20.4 2 22 2 22S5.1 20.4 12 18.5Z"/>
    </svg>`,

    // Claude (Anthropic) - Updated with better icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M12 4A8 8 0 0 1 20 12A8 8 0 0 1 12 20A8 8 0 0 1 4 12A8 8 0 0 1 12 4M12 6A6 6 0 0 0 6 12A6 6 0 0 0 12 18A6 6 0 0 0 18 12A6 6 0 0 0 12 6Z"/>
    </svg>`,

    // DeepSeek - Updated with CPU/brain icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z"/>
    </svg>`,

    // Grok (X) - Updated with lightning icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M7 2V13H10V22L17 10H14L17 2H7Z"/>
    </svg>`,

    // Qwen (Alibaba) - Updated with hexagon pattern
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M17.5 3.5L22 7V17L17.5 20.5H6.5L2 17V7L6.5 3.5H17.5M12 8L8 12L12 16L16 12L12 8Z"/>
    </svg>`,

    // Mistral - Updated with wind/flow icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M4 10A1 1 0 0 1 3 9A1 1 0 0 1 4 8H12A2 2 0 0 0 14 6A2 2 0 0 0 12 4H4A1 1 0 0 1 3 3A1 1 0 0 1 4 2H12A4 4 0 0 1 16 6A4 4 0 0 1 12 10H4M19 12A1 1 0 0 1 20 13A1 1 0 0 1 19 14H4A1 1 0 0 1 3 13A1 1 0 0 1 4 12H19M15 16A4 4 0 0 1 19 20A4 4 0 0 1 15 24H4A1 1 0 0 1 3 23A1 1 0 0 1 4 22H15A2 2 0 0 0 17 20A2 2 0 0 0 15 18H4A1 1 0 0 1 3 17A1 1 0 0 1 4 16H15Z"/>
    </svg>`,

    // Meta - Updated with infinity/meta icon
    `<svg viewBox="0 0 24 24" class="icon">
      <path fill="currentColor" d="M18.5 12C18.5 15.59 15.59 18.5 12 18.5S5.5 15.59 5.5 12 8.41 5.5 12 5.5 18.5 8.41 18.5 12M12 3C7.03 3 3 7.03 3 12S7.03 21 12 21 21 16.97 21 12 16.97 3 12 3M12 8C9.79 8 8 9.79 8 12S9.79 16 12 16 16 14.21 16 12 14.21 8 12 8Z"/>
    </svg>`
  ];

  let mounted = false;

  onMount(() => {
    mounted = true;
  });

  // 生成图标行数据
  function generateRows() {
    const rows = [];
    const rowCount = 10; // 增加行数
    
    for (let i = 0; i < rowCount; i++) {
      const row = {
        id: i,
        direction: i % 2 === 0 ? 'left' : 'right',
        delay: i * 0.3, // 减少延迟间隔
        icons: [...icons, ...icons, ...icons, ...icons] // 更多重复以填充屏幕
      };
      rows.push(row);
    }
    return rows;
  }

  $: rows = generateRows();
</script>

<div class="animated-background">
  {#if mounted}
    {#each rows as row (row.id)}
      <div 
        class="icon-row" 
        class:move-left={row.direction === 'left'}
        class:move-right={row.direction === 'right'}
        style="--delay: {row.delay}s; --row: {row.id};"
      >
        {#each row.icons as icon, index}
          <div class="icon-wrapper" style="--index: {index};">
            {@html icon}
          </div>
        {/each}
      </div>
    {/each}
  {/if}
</div>

<style>
  .animated-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    z-index: 1;
    pointer-events: none;
  }

  .icon-row {
    position: absolute;
    display: flex;
    align-items: center;
    height: 80px;
    width: 200%;
    transform: rotate(-30deg);
    top: calc(var(--row) * 100px - 150px);
    left: -50%;
    animation-duration: 45s;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-delay: var(--delay);
  }

  .move-left {
    animation-name: moveLeft;
  }

  .move-right {
    animation-name: moveRight;
  }

  .icon-wrapper {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    margin: 0 35px;
    opacity: 0.15;
    transition: opacity 0.3s ease;
  }

  .icon-wrapper:hover {
    opacity: 0.4;
  }

  .icon-wrapper :global(.icon) {
    width: 100%;
    height: 100%;
    color: currentColor;
  }

  @keyframes moveLeft {
    from {
      transform: rotate(-30deg) translateX(0);
    }
    to {
      transform: rotate(-30deg) translateX(-50%);
    }
  }

  @keyframes moveRight {
    from {
      transform: rotate(-30deg) translateX(-50%);
    }
    to {
      transform: rotate(-30deg) translateX(0);
    }
  }

  /* 暗色主题下的图标颜色 */
  :global(.dark) .icon-wrapper :global(.icon) {
    color: #e5e7eb;
  }

  /* 亮色主题下的图标颜色 */
  .icon-wrapper :global(.icon) {
    color: #374151;
  }
</style> 
