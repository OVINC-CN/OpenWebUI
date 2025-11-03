<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	import { settings } from '$lib/stores';
	import ImagePreview from './ImagePreview.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import { getContext } from 'svelte';

	export let src = '';
	export let alt = '';

	export let className = ` w-full ${($settings?.highContrastMode ?? false) ? '' : 'outline-hidden focus:outline-hidden'}`;

	export let imageClassName = 'rounded-lg max-w-full max-h-96 h-auto object-contain';

	export let dismissible = false;
	export let onDismiss = () => {};

	const i18n = getContext('i18n');

	let _src = '';
	$: _src = src.startsWith('/') ? `${WEBUI_BASE_URL}${src}` : src;

	let showImagePreview = false;
	let imageLoadError = false;
	
	const handleImageError = () => {
		imageLoadError = true;
	};
</script>

<ImagePreview bind:show={showImagePreview} src={_src} {alt} />

{#if imageLoadError}
	<div class="my-2 max-w-md mx-42">
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700 p-8 flex flex-col items-center justify-center min-h-[200px]">
			<div class="text-gray-500 dark:text-gray-400 text-center mb-3">
				{$i18n.t('Failed to load image')}
			</div>
			<a 
				href={_src} 
				target="_blank" 
				rel="noopener noreferrer"
				class="text-blue-600 dark:text-blue-400 hover:underline text-sm"
			>
				{$i18n.t('View link')}
			</a>
		</div>
	</div>
{:else}
	<div class=" relative group w-fit flex items-center">
		<button
			class={className}
			on:click={() => {
				showImagePreview = true;
			}}
			aria-label={$i18n.t('Show image preview')}
			type="button"
		>
			<img 
				src={_src} 
				{alt} 
				class={imageClassName} 
				draggable="false" 
				data-cy="image"
				loading="lazy"
				decoding="async"
				on:error={handleImageError}
			/>
		</button>

		{#if dismissible}
			<div class=" absolute -top-1 -right-1">
				<button
					aria-label={$i18n.t('Remove image')}
					class=" bg-white text-black border border-white rounded-full group-hover:visible invisible transition"
					type="button"
					on:click={() => {
						onDismiss();
					}}
				>
					<XMark className={'size-4'} />
				</button>
			</div>
		{/if}
	</div>
{/if}
