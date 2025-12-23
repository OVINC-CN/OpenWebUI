<script lang="ts">
	import { getContext } from 'svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { marked } from 'marked';

	const i18n = getContext('i18n');

	const featureLabels = {};

	export let availableFeatures = [];
	export let featureIds = [];
</script>

<div>
	<div class="flex w-full justify-between mb-1">
		<div class=" self-center text-xs font-medium text-gray-500">{$i18n.t('Default Features')}</div>
	</div>
	<div class="flex items-center mt-2 flex-wrap">
		{#each availableFeatures as feature}
			<div class=" flex items-center gap-2 mr-3">
				<Checkbox
					state={featureIds.includes(feature) ? 'checked' : 'unchecked'}
					on:change={(e) => {
						if (e.detail === 'checked') {
							featureIds = [...featureIds, feature];
						} else {
							featureIds = featureIds.filter((id) => id !== feature);
						}
					}}
				/>

				<div class=" py-0.5 text-sm capitalize">
					<Tooltip content={marked.parse(featureLabels[feature].description)}>
						{$i18n.t(featureLabels[feature].label)}
					</Tooltip>
				</div>
			</div>
		{/each}
	</div>
</div>
