<script>
  import { onMount } from 'svelte';

  // LLM图标CDN链接 - 使用@lobehub/icons官方CDN
  const iconUrls = [
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/gemini.svg', 
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/deepseek.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/grok.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/qwen.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/mistral.svg',
    'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/meta.svg'
  ];

  let mounted = false;

  onMount(() => {
    mounted = true;
  });

  // 生成图标行数据
  function generateRows() {
    const rows = [];
    const rowCount = 12; // 更多行数以覆盖屏幕
    
    for (let i = 0; i < rowCount; i++) {
      const row = {
        id: i,
        direction: i % 2 === 0 ? 'left' : 'right',
        delay: i * 0.2, // 更小的延迟
        icons: [...iconUrls, ...iconUrls, ...iconUrls, ...iconUrls, ...iconUrls] // 更多重复确保无缝
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
        {#each row.icons as iconUrl, index}
          <div class="icon-wrapper" style="--index: {index};">
            <img src={iconUrl} alt="LLM Icon" class="icon" />
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
    height: 120px;
    width: 300%;
    transform: rotate(-30deg);
    top: calc(var(--row) * 80px - 120px);
    left: -100%;
    animation-duration: 40s;
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
    width: 96px;
    height: 96px;
    margin: 0 60px;
    opacity: 0.6;
    transition: opacity 0.3s ease;
  }

  .icon-wrapper:hover {
    opacity: 0.9;
  }

  .icon {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  @keyframes moveLeft {
    from {
      transform: rotate(-30deg) translateX(0);
    }
    to {
      transform: rotate(-30deg) translateX(-33.33%);
    }
  }

  @keyframes moveRight {
    from {
      transform: rotate(-30deg) translateX(-33.33%);
    }
    to {
      transform: rotate(-30deg) translateX(0);
    }
  }
</style> 
