<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { marked } from 'marked';
	import Fuse from 'fuse.js';

	import dayjs from '$lib/dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';

	import { deleteModel, getOllamaVersion, pullModel, unloadModel } from '$lib/apis/ollama';

	import {
		user,
		MODEL_DOWNLOAD_POOL,
		models,
		mobile,
		temporaryChatEnabled,
		settings,
		config
	} from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { capitalizeFirstLetter, sanitizeResponseContent, splitStream } from '$lib/utils';
	import { getModels } from '$lib/apis';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import ChatBubbleOval from '$lib/components/icons/ChatBubbleOval.svelte';

	import ModelItem from './ModelItem.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let id = '';
	export let value = '';
	export let placeholder = $i18n.t('Select a model');
	export let searchEnabled = true;
	export let searchPlaceholder = $i18n.t('Search a model');
	let showExternal = false;

	export let items: {
		label: string;
		value: string;
		model: Model;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		[key: string]: any;
	}[] = [];

	export let className = 'w-[42rem]';
	export let triggerClassName = 'text-lg';

	export let pinModelHandler: (modelId: string) => void = () => {};

	let tagsContainerElement;

	let show = false;
	let tags = [];

	let selectedModel = '';
	$: selectedModel = items.find((item) => item.value === value) ?? '';

	let searchValue = '';

	let selectedTag = '';
	let selectedConnectionType = '';

	let ollamaVersion = null;
	let selectedModelIdx = 0;
	let hoveredBrand: string | null = null;

	const fuse = new Fuse(
		items.map((item) => {
			const _item = {
				...item,
				modelName: item.model?.name,
				tags: (item.model?.tags ?? []).map((tag) => tag.name).join(' '),
				desc: item.model?.info?.meta?.description
			};
			return _item;
		}),
		{
			keys: ['value', 'tags', 'modelName'],
			threshold: 0.4
		}
	);

	const updateFuse = () => {
		if (fuse) {
			fuse.setCollection(
				items.map((item) => {
					const _item = {
						...item,
						modelName: item.model?.name,
						tags: (item.model?.tags ?? []).map((tag) => tag.name).join(' '),
						desc: item.model?.info?.meta?.description
					};
					return _item;
				})
			);
		}
	};

	$: if (items) {
		updateFuse();
	}

	$: filteredItems = (
		searchValue
			? fuse
					.search(searchValue)
					.map((e) => {
						return e.item;
					})
					.filter((item) => {
						if (selectedTag === '') {
							return true;
						}
						return (item.model?.tags ?? []).map((tag) => tag.name).includes(selectedTag);
					})
					.filter((item) => {
						if (selectedConnectionType === '') {
							return true;
						} else if (selectedConnectionType === 'local') {
							return item.model?.connection_type === 'local';
						} else if (selectedConnectionType === 'external') {
							return item.model?.connection_type === 'external';
						} else if (selectedConnectionType === 'direct') {
							return item.model?.direct;
						}
					})
			: items
					.filter((item) => {
						if (selectedTag === '') {
							return true;
						}
						return (item.model?.tags ?? []).map((tag) => tag.name).includes(selectedTag);
					})
					.filter((item) => {
						if (selectedConnectionType === '') {
							return true;
						} else if (selectedConnectionType === 'local') {
							return item.model?.connection_type === 'local';
						} else if (selectedConnectionType === 'external') {
							return item.model?.connection_type === 'external';
						} else if (selectedConnectionType === 'direct') {
							return item.model?.direct;
						}
					})
	).filter((item) => !(item.model?.info?.meta?.hidden ?? false));

	// 从模型ID或名称中提取品牌名称
	const extractBrand = (modelId: string, modelName: string): string => {
		// 从名称中提取品牌
		const name = modelName || modelId;
		const lowerName = name.toLowerCase();
		
		// OpenAI系列: gpt、o1、o3、o4
		if (lowerName.startsWith('gpt') || 
		    lowerName.includes('chatgpt') || 
		    lowerName.startsWith('o1') || 
		    lowerName.startsWith('o3') || 
		    lowerName.startsWith('o4')) {
			return 'OpenAI';
		}
		
		// Anthropic系列: claude
		if (lowerName.startsWith('claude')) {
			return 'Anthropic';
		}
		
		// Google系列: gemini、nano、banana
		if (lowerName.startsWith('gemini') || 
		    lowerName.includes('gemini') ||
		    lowerName.startsWith('nano') ||
		    lowerName.startsWith('banana')) {
			return 'Google';
		}
		
		// xAI系列: grok
		if (lowerName.startsWith('grok')) {
			return 'xAI';
		}
		
		// DeepSeek系列
		if (lowerName.startsWith('deepseek')) {
			return 'DeepSeek';
		}
		
		// Alibaba系列: qwen、qwq
		if (lowerName.startsWith('qwen') || 
		    lowerName.includes('qwen') ||
		    lowerName.startsWith('qwq')) {
			return 'Alibaba';
		}
		
		// 智谱系列: glm
		if (lowerName.startsWith('glm')) {
			return '智谱';
		}
		
		// MoonShot系列: kimi
		if (lowerName.startsWith('kimi')) {
			return 'MoonShot';
		}
		
		// 处理ID中包含/的情况
		if (modelId.includes('/')) {
			const brand = modelId.split('/')[0].toLowerCase();
			// 规范化已知品牌名称
			if (brand === 'openai' || brand === 'gpt') return 'OpenAI';
			if (brand === 'anthropic' || brand === 'claude') return 'Anthropic';
			if (brand === 'google' || brand === 'gemini') return 'Google';
			if (brand === 'xai' || brand === 'grok') return 'xAI';
			if (brand === 'deepseek') return 'DeepSeek';
			if (brand === 'qwen' || brand === 'qwq' || brand === 'alibaba') return 'Alibaba';
			if (brand === 'zhipu' || brand === 'glm') return '智谱';
			if (brand === 'moonshot' || brand === 'kimi') return 'MoonShot';
		}
		
		return 'Other';
	};

	// 获取品牌Logo
	const getBrandLogo = (brand: string): string => {
		const logoMap: Record<string, string> = {
			'OpenAI': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/latest/files/icons/openai.svg',
			'Anthropic': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/anthropic.svg',
			'Google': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/google-color.svg',
			'xAI': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/xai.svg',
			'DeepSeek': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/deepseek-color.svg',
			'Alibaba': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/alibaba-color.svg',
			'智谱': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/zhipu-color.svg',
			'MoonShot': 'https://registry.npmmirror.com/@lobehub/icons-static-svg/1.73.0/files/icons/moonshot.svg'
		};
		
		// 如果有专属logo，返回专属logo
		if (logoMap[brand]) {
			return logoMap[brand];
		}
		
		// 否则尝试从该品牌下的第一个模型获取logo
		const brandModels = groupedFilteredItems.find(([b]) => b === brand)?.[1];
		if (brandModels && brandModels.length > 0) {
			return brandModels[0].model?.info?.meta?.profile_image_url || `${WEBUI_BASE_URL}/static/favicon.png`;
		}
		
		return `${WEBUI_BASE_URL}/static/favicon.png`;
	};

	// 将模型按品牌分组
	$: groupedFilteredItems = (() => {
		const groups = new Map<string, typeof filteredItems>();
		
		filteredItems.forEach(item => {
			const brand = extractBrand(item.value, item.model?.name || item.label);
			if (!groups.has(brand)) {
				groups.set(brand, []);
			}
			groups.get(brand)!.push(item);
		});
		
		// 定义品牌优先级顺序
		const brandOrder = ['OpenAI', 'Anthropic', 'Google', 'xAI', 'DeepSeek', 'Alibaba', '智谱', 'MoonShot'];
		
		// 转换为数组并按指定顺序排序
		return Array.from(groups.entries())
			.sort((a, b) => {
				const aIndex = brandOrder.indexOf(a[0]);
				const bIndex = brandOrder.indexOf(b[0]);
				
				// Other 永远放在最后
				if (a[0] === 'Other') return 1;
				if (b[0] === 'Other') return -1;
				
				// 如果两个都在优先级列表中，按优先级排序
				if (aIndex !== -1 && bIndex !== -1) {
					return aIndex - bIndex;
				}
				
				// 如果只有a在优先级列表中，a排在前面
				if (aIndex !== -1) return -1;
				
				// 如果只有b在优先级列表中，b排在前面
				if (bIndex !== -1) return 1;
				
				// 如果都不在优先级列表中，按字母顺序排序
				return a[0].localeCompare(b[0]);
			});
	})();

	$: if (selectedTag || selectedConnectionType) {
		resetView();
	} else {
		resetView();
	}

	const resetView = async () => {
		await tick();

		const selectedInFiltered = filteredItems.findIndex((item) => item.value === value);

		if (selectedInFiltered >= 0) {
			// The selected model is visible in the current filter
			selectedModelIdx = selectedInFiltered;
		} else {
			// The selected model is not visible, default to first item in filtered list
			selectedModelIdx = 0;
		}

		await tick();
		const item = document.querySelector(`[data-arrow-selected="true"]`);
		item?.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
	};

	const pullModelHandler = async () => {
		const sanitizedModelTag = searchValue.trim().replace(/^ollama\s+(run|pull)\s+/, '');

		console.log($MODEL_DOWNLOAD_POOL);
		if ($MODEL_DOWNLOAD_POOL[sanitizedModelTag]) {
			toast.error(
				$i18n.t(`Model '{{modelTag}}' is already in queue for downloading.`, {
					modelTag: sanitizedModelTag
				})
			);
			return;
		}
		if (Object.keys($MODEL_DOWNLOAD_POOL).length === 3) {
			toast.error(
				$i18n.t('Maximum of 3 models can be downloaded simultaneously. Please try again later.')
			);
			return;
		}

		const [res, controller] = await pullModel(localStorage.token, sanitizedModelTag, '0').catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		if (res) {
			const reader = res.body
				.pipeThrough(new TextDecoderStream())
				.pipeThrough(splitStream('\n'))
				.getReader();

			MODEL_DOWNLOAD_POOL.set({
				...$MODEL_DOWNLOAD_POOL,
				[sanitizedModelTag]: {
					...$MODEL_DOWNLOAD_POOL[sanitizedModelTag],
					abortController: controller,
					reader,
					done: false
				}
			});

			while (true) {
				try {
					const { value, done } = await reader.read();
					if (done) break;

					let lines = value.split('\n');

					for (const line of lines) {
						if (line !== '') {
							let data = JSON.parse(line);
							console.log(data);
							if (data.error) {
								throw data.error;
							}
							if (data.detail) {
								throw data.detail;
							}

							if (data.status) {
								if (data.digest) {
									let downloadProgress = 0;
									if (data.completed) {
										downloadProgress = Math.round((data.completed / data.total) * 1000) / 10;
									} else {
										downloadProgress = 100;
									}

									MODEL_DOWNLOAD_POOL.set({
										...$MODEL_DOWNLOAD_POOL,
										[sanitizedModelTag]: {
											...$MODEL_DOWNLOAD_POOL[sanitizedModelTag],
											pullProgress: downloadProgress,
											digest: data.digest
										}
									});
								} else {
									toast.success(data.status);

									MODEL_DOWNLOAD_POOL.set({
										...$MODEL_DOWNLOAD_POOL,
										[sanitizedModelTag]: {
											...$MODEL_DOWNLOAD_POOL[sanitizedModelTag],
											done: data.status === 'success'
										}
									});
								}
							}
						}
					}
				} catch (error) {
					console.log(error);
					if (typeof error !== 'string') {
						error = error.message;
					}

					toast.error(`${error}`);
					// opts.callback({ success: false, error, modelName: opts.modelName });
					break;
				}
			}

			if ($MODEL_DOWNLOAD_POOL[sanitizedModelTag].done) {
				toast.success(
					$i18n.t(`Model '{{modelName}}' has been successfully downloaded.`, {
						modelName: sanitizedModelTag
					})
				);

				models.set(
					await getModels(
						localStorage.token,
						$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
					)
				);
			} else {
				toast.error($i18n.t('Download canceled'));
			}

			delete $MODEL_DOWNLOAD_POOL[sanitizedModelTag];

			MODEL_DOWNLOAD_POOL.set({
				...$MODEL_DOWNLOAD_POOL
			});
		}
	};

	const setOllamaVersion = async () => {
		ollamaVersion = await getOllamaVersion(localStorage.token).catch((error) => false);
	};

	onMount(async () => {
		if (items) {
			tags = items
				.filter((item) => !(item.model?.info?.meta?.hidden ?? false))
				.flatMap((item) => item.model?.tags ?? [])
				.map((tag) => tag.name);

			// Remove duplicates and sort
			tags = Array.from(new Set(tags)).sort((a, b) => a.localeCompare(b));
		}
	});

	$: if (show) {
		setOllamaVersion();
	}

	const cancelModelPullHandler = async (model: string) => {
		const { reader, abortController } = $MODEL_DOWNLOAD_POOL[model];
		if (abortController) {
			abortController.abort();
		}
		if (reader) {
			await reader.cancel();
			delete $MODEL_DOWNLOAD_POOL[model];
			MODEL_DOWNLOAD_POOL.set({
				...$MODEL_DOWNLOAD_POOL
			});
			await deleteModel(localStorage.token, model);
			toast.success($i18n.t('{{model}} download has been canceled', { model: model }));
		}
	};

	const unloadModelHandler = async (model: string) => {
		const res = await unloadModel(localStorage.token, model).catch((error) => {
			toast.error($i18n.t('Error unloading model: {{error}}', { error }));
		});

		if (res) {
			toast.success($i18n.t('Model unloaded successfully'));
			models.set(
				await getModels(
					localStorage.token,
					$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
				)
			);
		}
	};
</script>

<DropdownMenu.Root
	bind:open={show}
	onOpenChange={async () => {
		searchValue = '';
		window.setTimeout(() => document.getElementById('model-search-input')?.focus(), 0);

		resetView();
	}}
	closeFocus={false}
>
	<DropdownMenu.Trigger
		class="relative w-full {($settings?.highContrastMode ?? false)
			? ''
			: 'outline-hidden focus:outline-hidden'}"
		aria-label={placeholder}
		id="model-selector-{id}-button"
	>
		<div
			class="flex w-full text-left px-0.5 bg-transparent truncate {triggerClassName} justify-between {($settings?.highContrastMode ??
			false)
				? 'dark:placeholder-gray-100 placeholder-gray-800'
				: 'placeholder-gray-400'}"
			on:mouseenter={async () => {
				models.set(
					await getModels(
						localStorage.token,
						$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
					)
				);
			}}
		>
			{#if selectedModel}
				{selectedModel.label}
			{:else}
				{placeholder}
			{/if}
			<ChevronDown className=" self-center ml-2 size-3" strokeWidth="2.5" />
		</div>
	</DropdownMenu.Trigger>

	<DropdownMenu.Content
		class=" z-40 {$mobile
			? `w-full`
			: `${className}`} max-w-[calc(100vw-1rem)] justify-start rounded-2xl  bg-white dark:bg-gray-850 dark:text-white shadow-lg  outline-hidden"
		transition={flyAndScale}
		side={$mobile ? 'bottom' : 'bottom-start'}
		sideOffset={2}
		alignOffset={-1}
	>
		<slot>
			{#if searchEnabled}
				<div class="flex items-center gap-2.5 px-4.5 mt-3.5 mb-1.5">
					<Search className="size-4" strokeWidth="2.5" />

					<input
						id="model-search-input"
						bind:value={searchValue}
						class="w-full text-sm bg-transparent outline-hidden"
						placeholder={searchPlaceholder}
						autocomplete="off"
						aria-label={$i18n.t('Search In Models')}
						on:keydown={(e) => {
							if (e.code === 'Enter' && filteredItems.length > 0) {
								value = filteredItems[selectedModelIdx].value;
								show = false;
								return; // dont need to scroll on selection
							} else if (e.code === 'ArrowDown') {
								e.stopPropagation();
								selectedModelIdx = Math.min(selectedModelIdx + 1, filteredItems.length - 1);
							} else if (e.code === 'ArrowUp') {
								e.stopPropagation();
								selectedModelIdx = Math.max(selectedModelIdx - 1, 0);
							} else {
								// if the user types something, reset to the top selection.
								selectedModelIdx = 0;
							}

							const item = document.querySelector(`[data-arrow-selected="true"]`);
							item?.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
						}}
					/>
				</div>
			{/if}

			<div class="px-2">
				{#if tags && items.filter((item) => !(item.model?.info?.meta?.hidden ?? false)).length > 0}
					<div
						class=" flex w-full bg-white dark:bg-gray-850 overflow-x-auto scrollbar-none font-[450] mb-0.5"
						on:wheel={(e) => {
							if (e.deltaY !== 0) {
								e.preventDefault();
								e.currentTarget.scrollLeft += e.deltaY;
							}
						}}
					>
						<div
							class="flex gap-1 w-fit text-center text-sm rounded-full bg-transparent px-1.5 whitespace-nowrap"
							bind:this={tagsContainerElement}
						>
							{#if items.find((item) => item.model?.connection_type === 'local') || items.find((item) => item.model?.connection_type === 'external') || items.find((item) => item.model?.direct) || tags.length > 0}
								<button
									class="min-w-fit outline-none px-1.5 py-0.5 {selectedTag === '' &&
									selectedConnectionType === ''
										? ''
										: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition capitalize"
									aria-pressed={selectedTag === '' && selectedConnectionType === ''}
									on:click={() => {
										selectedConnectionType = '';
										selectedTag = '';
									}}
								>
									{$i18n.t('All')}
								</button>
							{/if}

							{#if items.find((item) => item.model?.connection_type === 'local')}
								<button
									class="min-w-fit outline-none px-1.5 py-0.5 {selectedConnectionType === 'local'
										? ''
										: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition capitalize"
									aria-pressed={selectedConnectionType === 'local'}
									on:click={() => {
										selectedTag = '';
										selectedConnectionType = 'local';
									}}
								>
									{$i18n.t('Local')}
								</button>
						{/if}

						{#if items.find((item) => item.model?.direct)}
								<button
									class="min-w-fit outline-none px-1.5 py-0.5 {selectedConnectionType === 'direct'
										? ''
										: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition capitalize"
									aria-pressed={selectedConnectionType === 'direct'}
									on:click={() => {
										selectedTag = '';
										selectedConnectionType = 'direct';
									}}
								>
									{$i18n.t('Direct')}
								</button>
							{/if}

							{#each tags as tag}
								<Tooltip content={tag}>
									<button
										class="min-w-fit outline-none px-1.5 py-0.5 {selectedTag === tag
											? ''
											: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition capitalize"
										aria-pressed={selectedTag === tag}
										on:click={() => {
											selectedConnectionType = '';
											selectedTag = tag;
										}}
									>
										{tag.length > 16 ? `${tag.slice(0, 16)}...` : tag}
									</button>
								</Tooltip>
							{/each}
						</div>
					</div>
				{/if}
			</div>

		<div class="flex max-h-64 overflow-hidden group relative">
			<!-- 左侧品牌列表 -->
			<div class="flex-shrink-0 {$mobile ? 'w-32' : 'w-48'} border-r border-gray-200 dark:border-gray-700 overflow-y-auto custom-scrollbar px-1.5">
				{#if groupedFilteredItems.length > 0}
					{#each groupedFilteredItems as [brand, brandItems]}
					<button
						class="w-full {$mobile ? 'px-2 py-2' : 'px-3 py-2'} text-left {$mobile ? 'text-xs' : 'text-sm'} font-medium transition-colors flex items-center gap-2 rounded-xl group/brand {hoveredBrand === brand ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/50'}"
						on:mouseenter={() => {
							if (!$mobile) {
								hoveredBrand = brand;
							}
						}}
						on:click={() => {
							hoveredBrand = brand;
						}}
					>
						<img
							src={getBrandLogo(brand)}
							alt={brand}
							class="rounded-full size-5 flex-shrink-0"
						/>
						<span class="flex-1 truncate">{brand}</span>
						<span class="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
							{brandItems.length}
						</span>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="w-3.5 h-3.5 flex-shrink-0 {hoveredBrand === brand ? 'opacity-100' : 'opacity-0 group-hover/brand:opacity-50'} transition-opacity"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
						</svg>
					</button>
					{/each}
				{:else}
					<div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('No results found')}
					</div>
				{/if}
			</div>

			<!-- 右侧模型详细列表 -->
			<div class="flex-1 overflow-y-auto px-2.5 bg-gray-50/30 dark:bg-gray-800/20 custom-scrollbar">
				{#if hoveredBrand}
					{@const brandModels = groupedFilteredItems.find(([brand]) => brand === hoveredBrand)?.[1] || []}
					{@const tagGroups = (() => {
						// 定义标签分组顺序
						const tagOrder = ['Chat', 'Image', 'Image Edit', 'Video', '聊天', '图像', '图像编辑', '视频'];
						const groups = new Map();
						const shownModels = new Set();
						
						// 为每个标签创建分组
						tagOrder.forEach(tag => {
							groups.set(tag, []);
						});
						
						// 添加"其他"分组
						groups.set('其他', []);
						
						// 将模型分配到各个标签组
						brandModels.forEach(item => {
							const modelTags = (item.model?.tags ?? []).map(tag => tag.name);
							let assigned = false;
							
							// 检查模型是否属于任何定义的标签组
							tagOrder.forEach(tag => {
								if (modelTags.includes(tag)) {
									groups.get(tag).push({
										...item,
										isDuplicate: shownModels.has(item.value)
									});
									shownModels.add(item.value);
									assigned = true;
								}
							});
							
							// 如果没有匹配的标签，放入"其他"组
							if (!assigned) {
								groups.get('其他').push({
									...item,
									isDuplicate: false
								});
								shownModels.add(item.value);
							}
						});
						
						// 只返回有模型的分组
						return Array.from(groups.entries()).filter(([_, models]) => models.length > 0);
					})()}
					
					<div class="py-1">
						{#each tagGroups as [tagName, tagModels]}
							<div class="mb-3">
								<!-- 标签组标题 -->
								<div class="sticky top-0 z-10 bg-gray-50/90 dark:bg-gray-800/90 backdrop-blur-sm -mx-2.5 px-2.5 py-1.5 mb-1 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
									{tagName}
								</div>
								
								<!-- 该标签组的模型列表 -->
								{#each tagModels as item}
									{@const index = filteredItems.findIndex(i => i.value === item.value)}
									{@const displayItem = item.isDuplicate ? {
										...item,
										label: `${item.label} *`
									} : item}
									<ModelItem
										{selectedModelIdx}
										item={displayItem}
										{index}
										{value}
										{pinModelHandler}
										{unloadModelHandler}
										onClick={() => {
											value = item.value;
											selectedModelIdx = index;

											show = false;
										}}
									/>
								{/each}
							</div>
						{/each}
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center h-full text-center px-4">
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
						</svg>
						<p class="text-sm text-gray-400 dark:text-gray-500">
							{$i18n.t('Hover over a brand to see models')}
						</p>
					</div>
				{/if}
			</div>
		</div>

		<div class="px-2.5">
			{#if !(searchValue.trim() in $MODEL_DOWNLOAD_POOL) && searchValue && ollamaVersion && $user?.role === 'admin'}
				<Tooltip
					content={$i18n.t(`Pull "{{searchValue}}" from Ollama.com`, {
						searchValue: searchValue
					})}
					placement="top-start"
				>
					<button
						class="flex w-full font-medium line-clamp-1 select-none items-center rounded-button py-2 pl-3 pr-1.5 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg cursor-pointer data-highlighted:bg-muted"
						on:click={() => {
							pullModelHandler();
						}}
					>
						<div class=" truncate">
							{$i18n.t(`Pull "{{searchValue}}" from Ollama.com`, { searchValue: searchValue })}
						</div>
					</button>
				</Tooltip>
			{/if}

			{#each Object.keys($MODEL_DOWNLOAD_POOL) as model}
				<div
					class="flex w-full justify-between font-medium select-none rounded-button py-2 pl-3 pr-1.5 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 rounded-xl cursor-pointer data-highlighted:bg-muted"
				>
					<div class="flex">
						<div class="mr-2.5 translate-y-0.5">
							<Spinner />
						</div>

						<div class="flex flex-col self-start">
							<div class="flex gap-1">
								<div class="line-clamp-1">
									Downloading "{model}"
								</div>

								<div class="shrink-0">
									{'pullProgress' in $MODEL_DOWNLOAD_POOL[model]
										? `(${$MODEL_DOWNLOAD_POOL[model].pullProgress}%)`
										: ''}
								</div>
							</div>

							{#if 'digest' in $MODEL_DOWNLOAD_POOL[model] && $MODEL_DOWNLOAD_POOL[model].digest}
								<div class="-mt-1 h-fit text-[0.7rem] dark:text-gray-500 line-clamp-1">
									{$MODEL_DOWNLOAD_POOL[model].digest}
								</div>
							{/if}
						</div>
					</div>

					<div class="mr-2 ml-1 translate-y-0.5">
						<Tooltip content={$i18n.t('Cancel')}>
							<button
								class="text-gray-800 dark:text-gray-100"
								on:click={() => {
									cancelModelPullHandler(model);
								}}
							>
								<svg
									class="w-4 h-4 text-gray-800 dark:text-white"
									aria-hidden="true"
									xmlns="http://www.w3.org/2000/svg"
									width="24"
									height="24"
									fill="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke="currentColor"
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M6 18 17.94 6M18 18 6.06 6"
									/>
								</svg>
							</button>
						</Tooltip>
					</div>
				</div>
			{/each}
		</div>

		<div class="mb-2.5"></div>

		<div class="hidden w-[42rem]" />
		<div class="hidden w-[32rem]" />
		</slot>
	</DropdownMenu.Content>
</DropdownMenu.Root>

<style>
	/* 自定义滚动条样式 - 更细 */
	.custom-scrollbar::-webkit-scrollbar {
		width: 5px !important;
		height: 5px !important;
	}

	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent !important;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(156, 163, 175, 0.5) !important;
		border-radius: 3px !important;
	}

	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: rgba(156, 163, 175, 0.7) !important;
	}

	:global(.dark) .custom-scrollbar::-webkit-scrollbar-track {
		background: transparent !important;
	}

	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(156, 163, 175, 0.3) !important;
	}

	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: rgba(156, 163, 175, 0.5) !important;
	}

	/* Firefox 滚动条样式 */
	.custom-scrollbar {
		scrollbar-width: thin !important;
		scrollbar-color: rgba(156, 163, 175, 0.5) transparent !important;
	}

	:global(.dark) .custom-scrollbar {
		scrollbar-color: rgba(156, 163, 175, 0.3) transparent !important;
	}
</style>
