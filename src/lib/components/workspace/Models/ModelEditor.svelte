<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { onMount, getContext, tick } from 'svelte';
	import { models, tools, functions, knowledge as knowledgeCollections, user } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import { getTools } from '$lib/apis/tools';
	import { getFunctions } from '$lib/apis/functions';
	import { getKnowledgeBases } from '$lib/apis/knowledge';

	import AdvancedParams from '$lib/components/chat/Settings/Advanced/AdvancedParams.svelte';
	import Tags from '$lib/components/common/Tags.svelte';
	import Knowledge from '$lib/components/workspace/Models/Knowledge.svelte';
	import ToolsSelector from '$lib/components/workspace/Models/ToolsSelector.svelte';
	import FiltersSelector from '$lib/components/workspace/Models/FiltersSelector.svelte';
	import ActionsSelector from '$lib/components/workspace/Models/ActionsSelector.svelte';
	import Capabilities from '$lib/components/workspace/Models/Capabilities.svelte';
	import Textarea from '$lib/components/common/Textarea.svelte';
	import AccessControl from '../common/AccessControl.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import DefaultFiltersSelector from './DefaultFiltersSelector.svelte';
	import DefaultFeatures from './DefaultFeatures.svelte';

	const i18n = getContext('i18n');

	export let onSubmit: Function;
	export let onBack: null | Function = null;

	export let model = null;
	export let edit = false;

	export let preset = true;

	let loading = false;
	let success = false;

	let filesInputElement;
	let inputFiles;

	let showAdvanced = false;
	let showPreview = false;

	let loaded = false;

	// ///////////
	// model
	// ///////////

	let id = '';
	let name = '';

	let enableDescription = true;

	$: if (!edit) {
		if (name) {
			id = name
				.replace(/\s+/g, '-')
				.replace(/[^a-zA-Z0-9-]/g, '')
				.toLowerCase();
		}
	}

	let system = '';
	let info = {
		id: '',
		base_model_id: null,
		name: '',
		meta: {
			profile_image_url: `${WEBUI_BASE_URL}/static/favicon.png`,
			description: '',
			suggestion_prompts: null,
			tags: []
		},
		params: {
			system: ''
		},
		price: {
			prompt_price: 0,
			prompt_cache_price: 0,
			completion_price: 0,
			request_price: 0,
			minimum_credit: 0
		}
	};

	let params = {
		system: ''
	};

	let knowledge = [];
	let toolIds = [];

	let filterIds = [];
	let defaultFilterIds = [];

	let capabilities = {
		vision: true,
		file_upload: true,
		web_search: true,
		image_generation: true,
		code_interpreter: true,
		citations: true,
		status_updates: true,
		usage: undefined
	};
	let defaultFeatureIds = [];

	let actionIds = [];
	let accessControl = {};

	const addUsage = (base_model_id) => {
		const baseModel = $models.find((m) => m.id === base_model_id);

		if (baseModel) {
			if (baseModel.owned_by === 'openai') {
				capabilities.usage = baseModel?.meta?.capabilities?.usage ?? false;
			} else {
				delete capabilities.usage;
			}
			capabilities = capabilities;
		}
	};

	const submitHandler = async () => {
		loading = true;

		info.id = id;
		info.name = name;

		if (id === '') {
			toast.error($i18n.t('Model ID is required.'));
			loading = false;

			return;
		}

		if (name === '') {
			toast.error($i18n.t('Model Name is required.'));
			loading = false;

			return;
		}

		if (knowledge.some((item) => item.status === 'uploading')) {
			toast.error($i18n.t('Please wait until all files are uploaded.'));
			loading = false;

			return;
		}

		info.params = { ...info.params, ...params };

		info.access_control = accessControl;
		info.meta.capabilities = capabilities;

		if (enableDescription) {
			info.meta.description = info.meta.description.trim() === '' ? null : info.meta.description;
		} else {
			info.meta.description = null;
		}

		if (knowledge.length > 0) {
			info.meta.knowledge = knowledge;
		} else {
			if (info.meta.knowledge) {
				delete info.meta.knowledge;
			}
		}

		if (toolIds.length > 0) {
			info.meta.toolIds = toolIds;
		} else {
			if (info.meta.toolIds) {
				delete info.meta.toolIds;
			}
		}

		if (filterIds.length > 0) {
			info.meta.filterIds = filterIds;
		} else {
			if (info.meta.filterIds) {
				delete info.meta.filterIds;
			}
		}

		if (defaultFilterIds.length > 0) {
			info.meta.defaultFilterIds = defaultFilterIds;
		} else {
			if (info.meta.defaultFilterIds) {
				delete info.meta.defaultFilterIds;
			}
		}

		if (actionIds.length > 0) {
			info.meta.actionIds = actionIds;
		} else {
			if (info.meta.actionIds) {
				delete info.meta.actionIds;
			}
		}

		if (defaultFeatureIds.length > 0) {
			info.meta.defaultFeatureIds = defaultFeatureIds;
		} else {
			if (info.meta.defaultFeatureIds) {
				delete info.meta.defaultFeatureIds;
			}
		}

		info.params.system = system.trim() === '' ? null : system;
		info.params.stop = params.stop ? params.stop.split(',').filter((s) => s.trim()) : null;
		Object.keys(info.params).forEach((key) => {
			if (info.params[key] === '' || info.params[key] === null) {
				delete info.params[key];
			}
		});

		await onSubmit(info);

		loading = false;
		success = false;
	};

	onMount(async () => {
		await tools.set(await getTools(localStorage.token));
		await functions.set(await getFunctions(localStorage.token));
		await knowledgeCollections.set([...(await getKnowledgeBases(localStorage.token))]);

		// Scroll to top 'workspace-container' element
		const workspaceContainer = document.getElementById('workspace-container');
		if (workspaceContainer) {
			workspaceContainer.scrollTop = 0;
		}

		if (model) {
			name = model.name;
			await tick();

			id = model.id;

			enableDescription = model?.meta?.description !== null;

			if (model.base_model_id) {
				const base_model = $models
					.filter((m) => !m?.preset && !(m?.arena ?? false))
					.find((m) => [model.base_model_id, `${model.base_model_id}:latest`].includes(m.id));

				console.log('base_model', base_model);

				if (base_model) {
					model.base_model_id = base_model.id;
				} else {
					model.base_model_id = null;
				}
			}

			system = model?.params?.system ?? '';

			params = { ...params, ...model?.params };
			params.stop = params?.stop
				? (typeof params.stop === 'string' ? params.stop.split(',') : (params?.stop ?? [])).join(
						','
					)
				: null;

			knowledge = (model?.meta?.knowledge ?? []).map((item) => {
				if (item?.collection_name && item?.type !== 'file') {
					return {
						id: item.collection_name,
						name: item.name,
						legacy: true
					};
				} else if (item?.collection_names) {
					return {
						name: item.name,
						type: 'collection',
						collection_names: item.collection_names,
						legacy: true
					};
				} else {
					return item;
				}
			});

			toolIds = model?.meta?.toolIds ?? [];
			filterIds = model?.meta?.filterIds ?? [];
			defaultFilterIds = model?.meta?.defaultFilterIds ?? [];
			actionIds = model?.meta?.actionIds ?? [];

			capabilities = { ...capabilities, ...(model?.meta?.capabilities ?? {}) };
			defaultFeatureIds = model?.meta?.defaultFeatureIds ?? [];

			if ('access_control' in model) {
				accessControl = model.access_control;
			} else {
				accessControl = {};
			}

			console.log(model?.access_control);
			console.log(accessControl);

			info = {
				...info,
				...JSON.parse(
					JSON.stringify(
						model
							? model
							: {
									id: model.id,
									name: model.name
								}
					)
				)
			};
			if (!info.price) {
				info.price = {
					prompt_price: 0,
					prompt_cache_price: 0,
					completion_price: 0,
					request_price: 0,
					minimum_credit: 0
				};
			}

			console.log(model);
		}

		loaded = true;
	});
</script>

{#if loaded}
	<div class="w-full max-h-full flex justify-center">
		<input
			bind:this={filesInputElement}
			bind:files={inputFiles}
			type="file"
			hidden
			accept="image/*"
			on:change={() => {
				let reader = new FileReader();
				reader.onload = (event) => {
					let originalImageUrl = `${event.target.result}`;

					const img = new Image();
					img.src = originalImageUrl;

					img.onload = function () {
						const canvas = document.createElement('canvas');
						const ctx = canvas.getContext('2d');

						// Calculate the aspect ratio of the image
						const aspectRatio = img.width / img.height;

						// Calculate the new width and height to fit within 100x100
						let newWidth, newHeight;
						if (aspectRatio > 1) {
							newWidth = 250 * aspectRatio;
							newHeight = 250;
						} else {
							newWidth = 250;
							newHeight = 250 / aspectRatio;
						}

						// Set the canvas size
						canvas.width = 250;
						canvas.height = 250;

						// Calculate the position to center the image
						const offsetX = (250 - newWidth) / 2;
						const offsetY = (250 - newHeight) / 2;

						// Draw the image on the canvas
						ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);

						// Get the base64 representation of the compressed image
						const compressedSrc = canvas.toDataURL();

						// Display the compressed image
						info.meta.profile_image_url = compressedSrc;

						inputFiles = null;
						filesInputElement.value = '';
					};
				};

				if (
					inputFiles &&
					inputFiles.length > 0 &&
					['image/gif', 'image/webp', 'image/jpeg', 'image/png', 'image/svg+xml'].includes(
						inputFiles[0]['type']
					)
				) {
					reader.readAsDataURL(inputFiles[0]);
				} else {
					console.log(`Unsupported File Type '${inputFiles[0]['type']}'.`);
					inputFiles = null;
				}
			}}
		/>

		{#if !edit || (edit && model)}
			<form
				class="flex flex-col w-full"
				on:submit|preventDefault={() => {
					submitHandler();
				}}
			>
				<div class="w-full">
					<!-- 返回按钮 -->
					{#if onBack}
						<button
							class="flex items-center gap-1.5 mb-6 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition"
							type="button"
							on:click={() => {
								onBack();
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
								class="h-4 w-4"
							>
								<path
									fill-rule="evenodd"
									d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
									clip-rule="evenodd"
								/>
							</svg>
							<span class="font-medium">{$i18n.t('Back')}</span>
						</button>
					{/if}

					<!-- 模型图标和基本信息 - OpenAI 风格 -->
					<div class="flex items-start gap-4 mb-6">
						<!-- 图标区域 -->
						<div class="shrink-0">
							<button
								class="rounded-xl flex shrink-0 items-center {info.meta.profile_image_url !==
								`${WEBUI_BASE_URL}/static/favicon.png`
									? 'bg-transparent'
									: 'bg-gray-50 dark:bg-gray-900'} group relative overflow-hidden transition"
								type="button"
								on:click={() => {
									filesInputElement.click();
								}}
							>
								{#if info.meta.profile_image_url}
									<img
										src={info.meta.profile_image_url}
										alt="model profile"
										class="rounded-xl size-20 object-cover shrink-0"
									/>
								{:else}
									<img
										src="{WEBUI_BASE_URL}/static/favicon.png"
										alt="model profile"
										class="rounded-xl size-20 object-cover shrink-0 p-3"
									/>
								{/if}

								<!-- 悬停编辑提示 -->
								<div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-xl">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="size-6 text-white"
									>
										<path
											d="m2.695 14.762-1.262 3.155a.5.5 0 0 0 .65.65l3.155-1.262a4 4 0 0 0 1.343-.886L17.5 5.501a2.121 2.121 0 0 0-3-3L3.58 13.419a4 4 0 0 0-.885 1.343Z"
										/>
									</svg>
								</div>
							</button>
						</div>

						<!-- 标题和基本信息 -->
						<div class="flex-1 min-w-0">
							<div class="space-y-2">
								<input
									class="text-2xl font-semibold w-full bg-transparent outline-none placeholder:text-gray-400"
									placeholder={$i18n.t('Model Name')}
									bind:value={name}
									required
								/>
								<input
									class="text-sm w-full bg-transparent text-gray-500 outline-none placeholder:text-gray-400"
									placeholder={$i18n.t('Model ID')}
									bind:value={id}
									disabled={edit}
									required
								/>
								<div class="flex items-center gap-2">
									<span class="text-xs text-gray-500">{$i18n.t('Model Logo URL')}</span>
									<input
										class="text-xs flex-1 bg-transparent text-gray-500 outline-none placeholder:text-gray-400 border-b border-transparent hover:border-gray-300 dark:hover:border-gray-700 focus:border-gray-400 dark:focus:border-gray-600 transition"
										placeholder="https://..."
										bind:value={info.meta.profile_image_url}
									/>
									<button
										class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
										on:click={() => {
											info.meta.profile_image_url = `${WEBUI_BASE_URL}/static/favicon.png`;
										}}
										type="button"
									>
										{$i18n.t('Reset Image')}
									</button>
								</div>
							</div>
						</div>
					</div>

					{#if preset}
						<div class="mb-6">
							<div class="text-sm font-semibold mb-2">{$i18n.t('Base Model (From)')}</div>
							<div>
								<select
									class="text-sm w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg outline-none hover:border-gray-300 dark:hover:border-gray-700 focus:border-gray-400 dark:focus:border-gray-600 transition"
									placeholder={$i18n.t('Select a base model (e.g. llama3, gpt-4o)')}
									bind:value={info.base_model_id}
									on:change={(e) => {
										addUsage(e.target.value);
									}}
									required
								>
									<option value={null} class="text-gray-900"
										>{$i18n.t('Select a base model')}</option
									>
									{#each $models.filter((m) => (model ? m.id !== model.id : true) && !m?.preset && m?.owned_by !== 'arena' && !(m?.direct ?? false)) as model}
										<option value={model.id} class="text-gray-900">{model.name}</option>
									{/each}
								</select>
							</div>
						</div>
					{/if}

					{#if !preset}
						<div class="mb-6">
							<div class="text-sm font-semibold mb-2">{$i18n.t('Price')}</div>
							<div class="space-y-0.5 mb-2">
								<div class="text-xs text-orange-600">{$i18n.t('Unit: 1M tokens or 1M requests')}</div>
								<div class="text-xs text-gray-500">
									{$i18n.t('Request price has higher priority than token price')}
								</div>
							</div>
							<div class="space-y-2">
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-700 dark:text-gray-300 min-w-[140px]">
										{$i18n.t('Prompt Token Price')}
									</span>
									<input
										class="flex-1 px-2.5 py-1 text-xs bg-gray-50 dark:bg-gray-900 rounded-lg outline-none transition"
										type="number"
										step="0.0001"
										min="0"
										bind:value={info.price.prompt_price}
										autocomplete="off"
										required
									/>
								</div>
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-700 dark:text-gray-300 min-w-[140px]">
										{$i18n.t('Prompt Token Cache Price')}
									</span>
									<input
										class="flex-1 px-2.5 py-1 text-xs bg-gray-50 dark:bg-gray-900 rounded-lg outline-none transition"
										type="number"
										step="0.0001"
										min="0"
										bind:value={info.price.prompt_cache_price}
										autocomplete="off"
										required
									/>
								</div>
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-700 dark:text-gray-300 min-w-[140px]">
										{$i18n.t('Completion Token Price')}
									</span>
									<input
										class="flex-1 px-2.5 py-1 text-xs bg-gray-50 dark:bg-gray-900 rounded-lg outline-none transition"
										type="number"
										step="0.0001"
										min="0"
										bind:value={info.price.completion_price}
										autocomplete="off"
										required
									/>
								</div>
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-700 dark:text-gray-300 min-w-[140px]">
										{$i18n.t('Request Price')}
									</span>
									<input
										class="flex-1 px-2.5 py-1 text-xs bg-gray-50 dark:bg-gray-900 rounded-lg outline-none transition"
										type="number"
										step="0.0001"
										min="0"
										bind:value={info.price.request_price}
										autocomplete="off"
										required
									/>
								</div>
								<div class="flex items-center gap-3">
									<span class="text-xs text-gray-700 dark:text-gray-300 min-w-[140px]">
										{$i18n.t('Minimum Credit Required')}
									</span>
									<input
										class="flex-1 px-2.5 py-1 text-xs bg-gray-50 dark:bg-gray-900 rounded-lg outline-none transition"
										type="number"
										step="0.0001"
										min="0"
										bind:value={info.price.minimum_credit}
										autocomplete="off"
										required
									/>
								</div>
							</div>
						</div>
					{/if}

					<!-- 描述 -->
					<div class="mb-6">
						<div class="mb-2 flex w-full justify-between items-center">
							<div class="text-sm font-semibold">{$i18n.t('Description')}</div>
							<button
								class="px-3 py-1 text-xs flex items-center gap-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
								type="button"
								aria-pressed={enableDescription ? 'true' : 'false'}
								aria-label={enableDescription
									? $i18n.t('Custom description enabled')
									: $i18n.t('Default description enabled')}
								on:click={() => {
									enableDescription = !enableDescription;
								}}
							>
								{#if !enableDescription}
									<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Default')}</span>
								{:else}
									<span class="text-gray-600 dark:text-gray-400">{$i18n.t('Custom')}</span>
								{/if}
							</button>
						</div>

						{#if enableDescription}
							<Textarea
								className="text-sm w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg outline-none focus:border-gray-400 dark:focus:border-gray-600 transition resize-none overflow-y-hidden"
								placeholder={$i18n.t('Add a short description about what this model does')}
								bind:value={info.meta.description}
							/>
						{/if}
					</div>

					<!-- 标签 -->
					<div class="mb-6">
						<Tags
							tags={info?.meta?.tags ?? []}
							on:delete={(e) => {
								const tagName = e.detail;
								info.meta.tags = info.meta.tags.filter((tag) => tag.name !== tagName);
							}}
							on:add={(e) => {
								const tagName = e.detail;
								if (!(info?.meta?.tags ?? null)) {
									info.meta.tags = [{ name: tagName }];
								} else {
									info.meta.tags = [...info.meta.tags, { name: tagName }];
								}
							}}
						/>
					</div>

					<!-- 访问控制 -->
					<div class="mb-6">
						<div class="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-800">
							<AccessControl
								bind:accessControl
								accessRoles={['read', 'write']}
								allowPublic={$user?.permissions?.sharing?.public_models || $user?.role === 'admin'}
							/>
						</div>
					</div>

					<!-- 模型参数 -->
					<div class="mb-6">
						<div class="text-sm font-semibold mb-4">{$i18n.t('Model Params')}</div>

						<div class="space-y-4">
							<div>
								<div class="text-xs font-medium mb-2 text-gray-700 dark:text-gray-300">{$i18n.t('System Prompt')}</div>
								<Textarea
									className="text-sm w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg outline-none focus:border-gray-400 dark:focus:border-gray-600 transition resize-none overflow-y-hidden"
									placeholder={$i18n.t(
										'Write your model system prompt content here\ne.g.) You are Mario from Super Mario Bros, acting as an assistant.'
									)}
									rows={4}
									bind:value={system}
								/>
							</div>

							<div>
								<div class="flex w-full justify-between items-center mb-2">
									<div class="text-xs font-medium text-gray-700 dark:text-gray-300">
										{$i18n.t('Advanced Params')}
									</div>
									<button
										class="px-3 py-1 text-xs flex items-center gap-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
										type="button"
										on:click={() => {
											showAdvanced = !showAdvanced;
										}}
									>
										<span class="text-gray-600 dark:text-gray-400">
											{#if showAdvanced}
												{$i18n.t('Hide')}
											{:else}
												{$i18n.t('Show')}
											{/if}
										</span>
									</button>
								</div>

								{#if showAdvanced}
									<div class="mt-3">
										<AdvancedParams admin={true} custom={true} bind:params />
									</div>
								{/if}
							</div>
						</div>
					</div>

					<!-- 提示词建议 -->
					<div class="mb-6">
						<div class="flex w-full justify-between items-center mb-2">
							<div class="text-sm font-semibold">
								{$i18n.t('Prompt suggestions')}
							</div>

							<div class="flex items-center gap-2">
								<button
									class="px-3 py-1 text-xs flex items-center gap-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
									type="button"
									on:click={() => {
										if ((info?.meta?.suggestion_prompts ?? null) === null) {
											info.meta.suggestion_prompts = [{ content: '' }];
										} else {
											info.meta.suggestion_prompts = null;
										}
									}}
								>
									<span class="text-gray-600 dark:text-gray-400">
										{#if (info?.meta?.suggestion_prompts ?? null) === null}
											{$i18n.t('Default')}
										{:else}
											{$i18n.t('Custom')}
										{/if}
									</span>
								</button>

								{#if (info?.meta?.suggestion_prompts ?? null) !== null}
									<button
										class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
										type="button"
										on:click={() => {
											if (
												info.meta.suggestion_prompts.length === 0 ||
												info.meta.suggestion_prompts.at(-1).content !== ''
											) {
												info.meta.suggestion_prompts = [
													...info.meta.suggestion_prompts,
													{ content: '' }
												];
											}
										}}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 20 20"
											fill="currentColor"
											class="w-4 h-4 text-gray-600 dark:text-gray-400"
										>
											<path
												d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z"
											/>
										</svg>
									</button>
								{/if}
							</div>
						</div>

						{#if info?.meta?.suggestion_prompts}
							<div class="flex flex-col space-y-2 mt-3">
								{#if info.meta.suggestion_prompts.length > 0}
									{#each info.meta.suggestion_prompts as prompt, promptIdx}
										<div class="flex items-center gap-2">
											<input
												class="flex-1 text-sm px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg outline-none focus:border-gray-400 dark:focus:border-gray-600 transition"
												placeholder={$i18n.t('Write a prompt suggestion (e.g. Who are you?)')}
												bind:value={prompt.content}
											/>
											<button
												class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
												type="button"
												on:click={() => {
													info.meta.suggestion_prompts.splice(promptIdx, 1);
													info.meta.suggestion_prompts = info.meta.suggestion_prompts;
												}}
											>
												<XMark className={'size-4 text-gray-500'} />
											</button>
										</div>
									{/each}
								{:else}
									<div class="text-xs text-center text-gray-500 py-4">{$i18n.t('No suggestion prompts')}</div>
								{/if}
							</div>
						{/if}
					</div>

					<!-- 知识库 -->
					<div class="mb-6">
						<Knowledge bind:selectedItems={knowledge} />
					</div>

					<!-- 工具 -->
					<div class="mb-6">
						<ToolsSelector bind:selectedToolIds={toolIds} tools={$tools} />
					</div>

					<!-- 过滤器 -->
					<div class="mb-6">
						<FiltersSelector
							bind:selectedFilterIds={filterIds}
							filters={$functions.filter((func) => func.type === 'filter')}
						/>
					</div>

					{#if filterIds.length > 0}
						{@const toggleableFilters = $functions.filter(
							(func) =>
								func.type === 'filter' &&
								(filterIds.includes(func.id) || func?.is_global) &&
								func?.meta?.toggle
						)}

						{#if toggleableFilters.length > 0}
							<div class="mb-6">
								<DefaultFiltersSelector
									bind:selectedFilterIds={defaultFilterIds}
									filters={toggleableFilters}
								/>
							</div>
						{/if}
					{/if}

					<!-- 动作 -->
					<div class="mb-6">
						<ActionsSelector
							bind:selectedActionIds={actionIds}
							actions={$functions.filter((func) => func.type === 'action')}
						/>
					</div>

					<!-- 功能 -->
					<div class="mb-6">
						<Capabilities bind:capabilities />
					</div>

					{#if Object.keys(capabilities).filter((key) => capabilities[key]).length > 0}
						{@const availableFeatures = Object.entries(capabilities)
							.filter(
								([key, value]) =>
									value && ['web_search', 'code_interpreter', 'image_generation'].includes(key)
							)
							.map(([key, value]) => key)}

						{#if availableFeatures.length > 0}
							<div class="mb-6">
								<DefaultFeatures {availableFeatures} bind:featureIds={defaultFeatureIds} />
							</div>
						{/if}
					{/if}

					<!-- JSON 预览 -->
					<div class="mb-6">
						<div class="flex w-full justify-between items-center mb-2">
							<div class="text-sm font-semibold text-gray-700 dark:text-gray-300">{$i18n.t('JSON Preview')}</div>
							<button
								class="px-3 py-1 text-xs flex items-center gap-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
								type="button"
								on:click={() => {
									showPreview = !showPreview;
								}}
							>
								<span class="text-gray-600 dark:text-gray-400">
									{#if showPreview}
										{$i18n.t('Hide')}
									{:else}
										{$i18n.t('Show')}
									{/if}
								</span>
							</button>
						</div>

						{#if showPreview}
							<div class="mt-3">
								<textarea
									class="text-xs w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg outline-none resize-none font-mono text-gray-600 dark:text-gray-400"
									rows="10"
									value={JSON.stringify(info, null, 2)}
									disabled
									readonly
								/>
							</div>
						{/if}
					</div>

					<!-- 提交按钮 -->
					<div class="flex justify-end sticky bottom-0 py-3 bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800 -mx-4 px-4">
						<button
							class="px-4 py-1.5 text-sm font-medium transition rounded-lg {loading
								? 'cursor-not-allowed bg-gray-400 dark:bg-gray-600'
								: 'bg-black hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100'} text-white dark:text-black flex items-center justify-center gap-2 shadow-sm"
							type="submit"
							disabled={loading}
						>
							<span>
								{#if edit}
									{$i18n.t('Save & Update')}
								{:else}
									{$i18n.t('Save & Create')}
								{/if}
							</span>

							{#if loading}
								<Spinner />
							{/if}
						</button>
					</div>
				</div>
			</form>
		{/if}
	</div>
{/if}
