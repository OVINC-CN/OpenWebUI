<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { getCreditStats } from '$lib/apis/credit';
	import { toast } from 'svelte-sonner';
	import * as echarts from 'echarts';
	import type { EChartsType } from 'echarts';
	import { theme } from '$lib/stores';
	import flatpickr from 'flatpickr';
	import 'flatpickr/dist/flatpickr.css';
	import { Mandarin } from 'flatpickr/dist/l10n/zh.js';

	const maxDimensions = 20;
	const echartsTheme = $theme.includes('dark') ? 'dark' : 'light';

	let userPaymentLine: HTMLDivElement;
	let userPaymentLineOption = {};
	let userPaymentLineChart: EChartsType;

	let modelTokenPie: HTMLDivElement;
	let modelTokenPieOption = {};
	let modelTokenPieChart: EChartsType;

	let modelCostPie: HTMLDivElement;
	let modelCostPieOption = {};
	let modelCostPieChart: EChartsType;

	let userTokenPie: HTMLDivElement;
	let userTokenPieOption = {};
	let userTokenPieChart: EChartsType;

	let userCostPie: HTMLDivElement;
	let userCostPieOption = {};
	let userCostPieChart: EChartsType;

	const i18n = getContext('i18n');

	type ChartItem = {
		name: string;
		value: number;
	};
	type Data = {
		total_tokens: Number;
		total_credit: Number;
		model_cost_pie: Array<ChartItem>;
		model_token_pie: Array<ChartItem>;
		user_cost_pie: Array<ChartItem>;
		user_token_pie: Array<ChartItem>;
		total_payment: Number;
		user_payment_stats_x: Array<String>;
		user_payment_stats_y: Array<Number>;
	};

	let statsData: Data = {};

	let period = 7;

	let endTime = new Date();
	let startTime = new Date();
	startTime.setDate(endTime.getDate() - 7);

	const mergeData = (data: Array<ChartItem>) => {
		let sorted = data.sort((a, b) => b.value - a.value);
		let topItems = sorted.slice(0, maxDimensions);
		let rest = sorted.slice(maxDimensions);
		let restSum = rest.reduce((sum, item) => sum + item.value, 0);
		return [...topItems, ...(restSum > 0 ? [{ name: $i18n.t('Other'), value: restSum }] : [])];
	};

	let dateRangeInput;
	let fp;

	let query = '';
	$: if (query !== undefined) {
		doQuery();
	}

	const doQuery = async () => {
		const data = await getCreditStats(localStorage.token, {
			start_time: Math.round(startTime.getTime() / 1000),
			end_time: Math.round(endTime.getTime() / 1000),
			query: query
		}).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (data) {
			statsData = data;
			drawChart(data);
		}
	};

	const drawChart = (data: Data) => {
		if (!userPaymentLineChart) {
			userPaymentLineChart = echarts.init(userPaymentLine, echartsTheme);
		}
		userPaymentLineOption = {
			title: {
				text: $i18n.t('User Payment Stats'),
				textStyle: {
					fontSize: 14,
					fontWeight: '400'
				}
			},
			legend: {
				type: 'scroll',
				bottom: '10px',
				left: '10px',
				right: '10px'
			},
			tooltip: {
				show: true,
				trigger: 'axis'
			},
			xAxis: {
				type: 'category',
				data: data.user_payment_stats_x
			},
			yAxis: {
				type: 'value'
			},
			series: [
				{
					data: data.user_payment_stats_y,
					type: 'line',
					areaStyle: {}
				}
			]
		};
		userPaymentLineChart.setOption(userPaymentLineOption);

		if (!modelTokenPieChart) {
			modelTokenPieChart = echarts.init(modelTokenPie, echartsTheme);
		}
		modelTokenPieOption = {
			title: {
				text: $i18n.t('Model Tokens Cost'),
				textStyle: {
					fontSize: 14,
					fontWeight: '400'
				}
			},
			legend: {
				type: 'scroll',
				bottom: '10px',
				left: '10px',
				right: '10px'
			},
			tooltip: {
				show: true
			},
			series: [
				{
					type: 'pie',
					data: mergeData(data.model_token_pie),
					radius: ['40%', '60%'],
					label: {
						show: false
					}
				}
			]
		};
		modelTokenPieChart.setOption(modelTokenPieOption);

		if (!modelCostPieChart) {
			modelCostPieChart = echarts.init(modelCostPie, echartsTheme);
		}
		modelCostPieOption = {
			title: {
				text: $i18n.t('Model Credit Cost'),
				textStyle: {
					fontSize: 14,
					fontWeight: '400'
				}
			},
			legend: {
				type: 'scroll',
				bottom: '10px',
				left: '10px',
				right: '10px'
			},
			tooltip: {
				show: true
			},
			series: [
				{
					type: 'pie',
					data: mergeData(data.model_cost_pie),
					radius: ['40%', '60%'],
					label: {
						show: false
					}
				}
			]
		};
		modelCostPieChart.setOption(modelCostPieOption);

		if (!userTokenPieChart) {
			userTokenPieChart = echarts.init(userTokenPie, echartsTheme);
		}
		const _userTokenPieData = mergeData(data.user_token_pie);
		const userTokenX = _userTokenPieData.map((item) => item.name);
		const userTokenY = _userTokenPieData.map((item) => item.value);
		userTokenPieOption = {
			title: {
				text: $i18n.t('User Tokens Cost'),
				textStyle: {
					fontSize: 14,
					fontWeight: '400'
				}
			},
			tooltip: {
				show: true,
				trigger: 'axis'
			},
			xAxis: {
				data: userTokenX,
				type: 'category',
				axisLabel: {
					interval: 0,
					rotate: 45,
					width: 80,
					margin: 24,
					overflow: 'truncate',
					align: 'center',
					verticalAlign: 'middle'
				}
			},
			yAxis: {},
			series: [
				{
					type: 'bar',
					data: userTokenY,
					barMaxWidth: 40,
					showBackground: true,
					backgroundStyle: {
						borderRadius: [5, 5, 0, 0]
					},
					itemStyle: {
						barBorderRadius: [5, 5, 0, 0]
					},
					colorBy: 'data',
					label: {
						show: true,
						position: 'top'
					}
				}
			]
		};
		userTokenPieChart.setOption(userTokenPieOption);

		if (!userCostPieChart) {
			userCostPieChart = echarts.init(userCostPie, echartsTheme);
		}
		const _userCostPieData = mergeData(data.user_cost_pie);
		const userCostX = _userCostPieData.map((item) => item.name);
		const userCostY = _userCostPieData.map((item) => item.value);
		userCostPieOption = {
			title: {
				text: $i18n.t('User Credit Cost'),
				textStyle: {
					fontSize: 14,
					fontWeight: '400'
				}
			},
			tooltip: {
				show: true,
				trigger: 'axis'
			},
			xAxis: {
				data: userCostX,
				type: 'category',
				axisLabel: {
					interval: 0,
					rotate: 45,
					width: 80,
					margin: 24,
					overflow: 'truncate',
					align: 'center',
					verticalAlign: 'middle'
				}
			},
			yAxis: {},
			series: [
				{
					type: 'bar',
					data: userCostY,
					barMaxWidth: 40,
					showBackground: true,
					backgroundStyle: {
						borderRadius: [5, 5, 0, 0]
					},
					itemStyle: {
						barBorderRadius: [5, 5, 0, 0]
					},
					colorBy: 'data',
					label: {
						show: true,
						position: 'top'
					}
				}
			]
		};
		userCostPieChart.setOption(userCostPieOption);
	};

	onMount(async () => {
		if (echartsTheme === 'dark') {
			await import('flatpickr/dist/themes/dark.css');
		}

		let locale = null;
		const lang = document.documentElement.getAttribute('lang');
		if (lang === 'zh-CN') {
			locale = Mandarin;
		}

		const minDays = new Date();
		minDays.setDate(endTime.getDate() - 180);
		const tomorrow = new Date();
		tomorrow.setDate(endTime.getDate() + 1);

		fp = flatpickr(dateRangeInput, {
			locale: locale,
			mode: 'range',
			dateFormat: 'Y-m-d H:i:S',
			enableTime: true,
			animate: true,
			allowInput: true,
			defaultDate: [startTime, endTime],
			defaultHour: 0,
			maxDate: tomorrow,
			minDate: minDays,
			position: 'auto center',
			showMonths: 2,
			time_24hr: true,
			onChange: async (selectedDates, _) => {
				if (selectedDates.length === 2) {
					startTime = selectedDates[0];
					endTime = selectedDates[1];
					await doQuery();
				}
			}
		});

		return () => {
			fp.destroy();
		};
	});
</script>

<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		<div class="flex-shrink-0">
			{$i18n.t('Credit Statistics')}
		</div>
	</div>

	<div class="flex gap-1">
		<div class=" flex w-full space-x-2">
			<div class="flex flex-1 w-full">
				<div class=" self-center ml-1 mr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<input
					class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={query}
					placeholder={$i18n.t('Fuzzy Search Username')}
				/>
			</div>
		</div>
	</div>
</div>

<div class="mt-2 flex justify-around h-[48px] white">
	<input
		bind:this={dateRangeInput}
		type="text"
		class="w-full rounded-md bg-gray-50 dark:text-gray-300 dark:bg-gray-850 text-center font-medium"
		readonly
	/>
</div>

<div
	class="mt-2 flex justify-between items-center bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
>
	<div class="flex flex-col items-center w-full">
		<span class="text-gray-500 text-xs mb-1">{$i18n.t('Total Payment')}</span>
		<div class="text-blue-600 font-medium">{statsData.total_payment ?? 0}</div>
	</div>
	<div class="flex flex-col items-center border-x border-gray-200 w-full">
		<span class="text-gray-500 text-xs mb-1">{$i18n.t('Total Credit Cost')}</span>
		<div class="text-green-600 font-medium">{statsData.total_credit ?? 0}</div>
	</div>
	<div class="flex flex-col items-center w-full">
		<span class="text-gray-500 text-xs mb-1">{$i18n.t('Total Token Cost')}</span>
		<div class="text-purple-600 font-medium">{statsData.total_tokens ?? 0}</div>
	</div>
</div>

<div
	class="mt-2 bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
	bind:this={userPaymentLine}
	style="width: 100%; height: 300px;"
></div>
<div
	class="mt-2 bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
	bind:this={modelTokenPie}
	style="width: 100%; height: 300px;"
></div>
<div
	class="mt-2 bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
	bind:this={modelCostPie}
	style="width: 100%; height: 300px;"
></div>
<div
	class="mt-2 bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
	bind:this={userTokenPie}
	style="width: 100%; height: 300px;"
></div>
<div
	class="mt-2 bg-gray-50 rounded-md dark:text-gray-300 dark:bg-gray-850"
	bind:this={userCostPie}
	style="width: 100%; height: 300px;"
></div>
