import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function truncateText(text: string | undefined | null, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

export function getCapsuleTypeColor(type: string): string {
  const colors: Record<string, string> = {
    'chat': 'bg-blue-100 text-blue-800',
    'refusal': 'bg-red-100 text-red-800',
    'introspective': 'bg-purple-100 text-purple-800',
    'joint': 'bg-green-100 text-green-800',
    'consent': 'bg-yellow-100 text-yellow-800',
    'perspective': 'bg-indigo-100 text-indigo-800',
    'governance': 'bg-orange-100 text-orange-800',
    'default': 'bg-gray-100 text-gray-800',
  };

  return colors[type] || colors.default;
}

export function debounce<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

export function isValidApiKey(apiKey: string): boolean {
  // Basic validation - adjust based on your API key format
  return apiKey.length >= 32 && /^[a-zA-Z0-9-_]+$/.test(apiKey);
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) +
         Math.random().toString(36).substring(2, 15);
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
