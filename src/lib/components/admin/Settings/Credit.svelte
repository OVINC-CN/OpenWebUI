<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { getUsageConfig, setUsageConfig } from '$lib/apis/configs';

	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;

	let config = null;

	const submitHandler = async () => {
		await setUsageConfig(localStorage.token, config);
	};

	onMount(async () => {
		const res = await getUsageConfig(localStorage.token);

		if (res) {
			config = res;
		}
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={async () => {
		await submitHandler();
		saveHandler();
	}}
>
	<div class=" space-y-3 overflow-y-scroll scrollbar-hidden h-full">
		{#if config}
			<div>
				<div class="mb-3">
					<div class=" mb-2.5 text-base font-medium">{$i18n.t('Credit')}</div>
					<hr class=" border-gray-100 dark:border-gray-850 my-2" />
					<div class="flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('No Credit Message')}</div>
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.CREDIT_NO_CREDIT_MSG}
							required
						/>
					</div>
					<div class="flex mt-2 w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Credit Exchange Ratio')}</div>
					</div>
					<div class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t(
							'The exchange ratio of legal currency to credit. If you need a discount, please set it to be greater than 1'
						)}
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.CREDIT_EXCHANGE_RATIO}
							type="number"
							step="0.0001"
							required
						/>
					</div>
					<div class="flex mt-2 w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Default Credit for User')}</div>
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.CREDIT_DEFAULT_CREDIT}
							type="number"
							step="0.0001"
							required
						/>
					</div>
					<div class="flex mt-2 w-full justify-between">
						<div class=" self-center text-xs font-medium">
							{$i18n.t('Minimum Cost Per Request')}
						</div>
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_MINIMUM_COST}
							type="number"
							step="0.0001"
							required
						/>
					</div>
				</div>

				<div class="mb-3">
					<div class=" mb-2.5 text-base font-medium">{$i18n.t('Calculate Token')}</div>
					<hr class=" border-gray-100 dark:border-gray-850 my-2" />
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Model Prefix to Remove')}</div>
					</div>
					<div class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('Remove characters that prefix matched')}
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_MODEL_PREFIX_TO_REMOVE}
						/>
					</div>
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Default Encoding Model')}</div>
					</div>
					<div class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t(
							'If there is no Usage returned, and the model cannot be matched, then use the tiktoken encoder of this model to calculate the Token'
						)}
					</div>
					<div class="flex mt-2 space-x-2">
						<input
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_DEFAULT_ENCODING_MODEL}
							required
						/>
					</div>
				</div>

				<div class="mb-3">
					<div class="text-base font-medium">{$i18n.t('Embedding Price')}</div>
					<hr class="mt-2.5 border-gray-100 dark:border-gray-850 my-2" />
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">
							{$i18n.t('Prompt Price For 1M Tokens')}
						</div>
						<input
							class="rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_DEFAULT_EMBEDDING_PRICE}
							type="number"
							step="0.000001"
						/>
					</div>
				</div>

				<div class="mb-3">
					<div class="text-base font-medium">{$i18n.t('Feature Price')}</div>
					<div class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('For 1M requests')}
					</div>
					<hr class="mt-2.5 border-gray-100 dark:border-gray-850 my-2" />
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Image Generation')}</div>
						<input
							class="rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE}
							type="number"
							step="0.000001"
						/>
					</div>
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Code Execution')}</div>
						<input
							class="rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE}
							type="number"
							step="0.000001"
						/>
					</div>
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Web Search')}</div>
						<input
							class="rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE}
							type="number"
							step="0.000001"
						/>
					</div>
					<div class="mt-2 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Direct Tool Servers')}</div>
						<input
							class="rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							bind:value={config.USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE}
							type="number"
							step="0.000001"
						/>
					</div>

					<div class="mb-3">
						<div class="text-base font-medium">{$i18n.t('Custom Price Configuration')}</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'JSON array configuration for custom function/tool billing patterns of 1M requests, e.g. [{"name": "web search", "path": "$.tools[*].type", "value": "web_search_preview", "exists": false, "cost": 1000000}]'
							)}
						</div>
						<hr class="mt-2.5 border-gray-100 dark:border-gray-850 my-2" />
						<div class="mt-2">
							<textarea
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.USAGE_CUSTOM_PRICE_CONFIG}
								placeholder={$i18n.t('Enter JSON array configuration')}
								rows="4"
							/>
						</div>
					</div>

					<div class="mb-3">
						<div class=" mb-2.5 text-base font-medium">{$i18n.t('Alipay')}</div>
						<hr class=" border-gray-100 dark:border-gray-850 my-2" />
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Alipay Server URL')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_SERVER_URL}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Alipay AppID')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_APP_ID}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">
								{$i18n.t('Alipay App Private Key')}
							</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'Please use a private key in PKCS#1 format. You can convert it using a format-conversion tool.'
							)}
						</div>
						<div class="flex mt-2 space-x-2">
							<SensitiveInput
								outerClassName="w-full flex flex-1 rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_APP_PRIVATE_KEY}
								required={false}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Alipay Public Key')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<SensitiveInput
								outerClassName="w-full flex flex-1 rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_ALIPAY_PUBLIC_KEY}
								required={false}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('OpenWebUI Host')}</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'The address of your service must be accessible by Alipay; do not include any paths, only the HTTP protocol and the domain name'
							)}
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_CALLBACK_HOST}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Alipay Product Code')}</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Trace ticket qrcode pay to input QR_CODE_OFFLINE')}
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_PRODUCT_CODE}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Charge Amount Control')}</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('The allowed range of recharge amounts; if not set, there is no limit')}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'For multiple configurations, use commas (,) to separate them, and use a hyphen (-) for ranges'
							)}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('For example: 10-20,30,40-50')}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'The above values mean that only 10-20 yuan, 30 yuan, and 40-50 yuan can be recharged.'
							)}
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.ALIPAY_AMOUNT_CONTROL}
							/>
						</div>
					</div>

					<div class="mb-3">
						<div class=" mb-2.5 text-base font-medium">{$i18n.t('EZFP Payment')}</div>
						<hr class=" border-gray-100 dark:border-gray-850 my-2" />
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">
								{$i18n.t('EZFP Pay Type Priority')}
							</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<select
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_PAY_PRIORITY}
							>
								<option value="qrcode">{$i18n.t('QRCode')}</option>
								<option value="link">{$i18n.t('Redirect Link')}</option>
							</select>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('EZFP Endpoint')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_ENDPOINT}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('EZFP PID')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_PID}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('EZFP Key')}</div>
						</div>
						<div class="flex mt-2 space-x-2">
							<SensitiveInput
								outerClassName="w-full flex flex-1 rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_KEY}
								required={false}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('OpenWebUI Host')}</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'The address of your service must be accessible by Epay; do not include any paths, only the HTTP protocol and the domain name'
							)}
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_CALLBACK_HOST}
							/>
						</div>
						<div class="mt-2 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Charge Amount Control')}</div>
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('The allowed range of recharge amounts; if not set, there is no limit')}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'For multiple configurations, use commas (,) to separate them, and use a hyphen (-) for ranges'
							)}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('For example: 10-20,30,40-50')}
						</div>
						<div class="text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t(
								'The above values mean that only 10-20 yuan, 30 yuan, and 40-50 yuan can be recharged.'
							)}
						</div>
						<div class="flex mt-2 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								bind:value={config.EZFP_AMOUNT_CONTROL}
							/>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			type="submit"
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>
