export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(num);
};

export const formatDecimal = (num: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatHours = (hours: number): string => {
  if (hours < 1) {
    return `${formatDecimal(hours * 60, 1)} min`;
  } else if (hours < 24) {
    return `${formatDecimal(hours, 1)} hours`;
  } else {
    const days = hours / 24;
    return `${formatDecimal(days, 1)} days`;
  }
};

export const formatCompact = (num: number): string => {
  if (num >= 1000000) {
    return `${formatDecimal(num / 1000000, 1)}M`;
  } else if (num >= 1000) {
    return `${formatDecimal(num / 1000, 1)}K`;
  }
  return formatNumber(num);
};
