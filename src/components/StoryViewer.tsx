'use client';

export default function StoryViewer({ title, blocks, status }: any) {
  return (
    <div className="max-w-2xl mx-auto mt-6 space-y-6">

      {title && (
        <h1 className="text-2xl font-bold text-center">{title}</h1>
      )}

      {blocks.map((block: any, i: number) => (
        <div key={i} className="space-y-3">

          {block.type === 'text' && (
            <p className="text-lg leading-relaxed">{block.content}</p>
          )}

          {block.type === 'image' && (
            <img
              src={block.content}
              alt="scene"
              className="rounded-lg w-full"
            />
          )}

          {block.type === 'audio' && (
            <audio controls src={block.content} />
          )}

        </div>
      ))}

      {status === 'generating' && (
        <p className="text-center text-gray-500">Generating your story...</p>
      )}

      {status === 'complete' && (
        <p className="text-center text-green-600">Story complete ✅</p>
      )}

    </div>
  );
}