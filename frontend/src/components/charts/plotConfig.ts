/** Plot config with every option that sends chart data off the page switched off.
 *
 * plotly.js 4 shows a "send to cloud" modebar button by default that uploads the chart data to
 * cloud.plotly.com. Cluster usage must stay on the dashboard, so the button is forced off.
 */
export function withLocalOnlyConfig<T extends object>(config: T | undefined): T & { showSendToCloud: false } {
  return { ...(config ?? ({} as T)), showSendToCloud: false };
}
