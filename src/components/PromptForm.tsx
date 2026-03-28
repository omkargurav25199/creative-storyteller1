'use client';

import { useState } from 'react';

export default function PromptForm({ onGenerate }: any) {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('storybook');
  const [audience, setAudience] = useState('children');
  const [numScenes, setNumScenes] = useState(3);

  const playSound = () => {
    const audio = new Audio('/bling.mp3');
    audio.play().catch(() => {});
  };

  return (
   <div className="p-6 space-y-4 ">
<textarea
  className="w-full p-4 rounded-md text-lg bg-white/70 backdrop-blur-md outline-none"
  rows={3}
  placeholder="Create a story about..."
  value={prompt}
  onChange={(e) => setPrompt(e.target.value)}
/>
      <p className="text-right italic text-sm text-gray-600">
        🪶 writing...
      </p>

      <button
        onClick={() => onGenerate(prompt, style, audience, numScenes)}
        className="bg-black text-white px-6 py-2 rounded-md mt-4"
      >
        Create Story
      </button>

    </div>
  );
}