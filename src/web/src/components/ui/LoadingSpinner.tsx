'use client';

export default function LoadingSpinner({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-gray-700/50" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-400 animate-spin" />
      </div>
      <p className="text-gray-400 text-sm mt-4">{text}</p>
    </div>
  );
}
