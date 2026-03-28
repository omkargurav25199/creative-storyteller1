'use client';

import { useState } from 'react';
import PromptForm from '@/components/PromptForm';
import StoryViewer from '@/components/StoryViewer';
import { useStoryStream } from '@/hooks/useStoryStream';

export default function Home() {
  const { title, blocks, status, generate } = useStoryStream();
  const [entered, setEntered] = useState(false);

  return (
    <main className="h-screen w-screen overflow-hidden">

      {/* LANDING SCREEN */}
      {!entered && (
        <div
          className="h-full w-full bg-cover bg-center relative"
          style={{ backgroundImage: "url('/landing.png')" }}
        >
          {/* Glow on table */}
          <div
            onClick={() => setEntered(true)}
            className="absolute bottom-[20%] left-1/2 transform -translate-x-1/2 cursor-pointer"
          >
            <div className="glow-circle" />
          </div>
        </div>
      )}

      {/* MAIN APP */}
      {entered && (
        <div className="h-full flex items-center justify-center transition-all duration-700">

          <div className="app-card">

            <PromptForm onGenerate={generate} />

            <StoryViewer
              title={title}
              blocks={blocks}
              status={status}
            />

          </div>

        </div>
      )}

    </main>
  );
}